//! Compares the tripletrail store with Oxigraph's in-memory store on the generated ERA-shaped
//! network: load time, memory, and SPARQL queries through the same evaluator.
//!
//! Each store runs in its own child process so the memory figures don't mix.
//!
//! Usage: `store [horizontal_lines] [vertical_lines] [elements_between_crossings]`

#[path = "../common.rs"]
#[allow(dead_code)]
mod common;
#[path = "../synthetic.rs"]
mod synthetic;

use common::*;
use std::io::Write;
use std::process::Command;
use std::time::{Duration, Instant};
use synthetic::*;
use tripletrail::oxigraph::io::RdfFormat;
use tripletrail::oxigraph::sparql::{QueryResults, SparqlEvaluator};

const PREFIXES: &str = "PREFIX era: <http://data.europa.eu/949/>
PREFIX geo: <http://www.opengis.net/ont/geosparql#>
PREFIX geof: <http://www.opengis.net/def/function/geosparql/>
";

fn rss_mb() -> f64 {
    let s = std::fs::read_to_string("/proc/self/status").unwrap_or_default();
    s.lines()
        .find(|l| l.starts_with("VmRSS:"))
        .and_then(|l| l.split_whitespace().nth(1)?.parse::<f64>().ok())
        .map_or(0.0, |kb| kb / 1024.0)
}

/// The queries, by name. `{E}` is replaced by a net element IRI.
fn queries() -> Vec<(&'static str, String)> {
    let (_, edges) = split_profile(include_str!("../../../../core/profiles/era-micro.rq"));
    vec![
        (
            "count all triples",
            "SELECT (COUNT(*) AS ?n) WHERE { ?s ?p ?o }".into(),
        ),
        (
            "ERA micro edge query (network build input)",
            format!(
                "PREFIX nav: <http://data.europa.eu/949/concepts/navigabilities/>\n{PREFIXES}{edges}"
            ),
        ),
        (
            "element -> geometry -> WKT join",
            format!(
                "{PREFIXES}SELECT ?e ?w WHERE {{ ?e a era:LinearElement ; geo:hasGeometry ?g . ?g geo:asWKT ?w }}"
            ),
        ),
        (
            "numeric FILTER on lengths",
            format!(
                "{PREFIXES}SELECT ?e WHERE {{ ?e era:lengthOfNetLinearElement ?l FILTER(?l > 505) }}"
            ),
        ),
        (
            "relations of switches (navigability None)",
            format!(
                "{PREFIXES}SELECT ?r ?a WHERE {{ ?r era:navigability <http://data.europa.eu/949/concepts/navigabilities/None> ; era:elementA ?a }}"
            ),
        ),
        (
            "GROUP BY navigability",
            format!(
                "{PREFIXES}SELECT ?n (COUNT(*) AS ?c) WHERE {{ ?r era:navigability ?n }} GROUP BY ?n"
            ),
        ),
        (
            "sfIntersects over every WKT (no index)",
            format!(
                "{PREFIXES}SELECT ?g WHERE {{ ?g geo:asWKT ?w FILTER(geof:sfIntersects(?w, \"POLYGON((5 58, 5.5 58, 5.5 58.5, 5 58.5, 5 58))\"^^geo:wktLiteral)) }}"
            ),
        ),
    ]
}

fn drain(results: QueryResults<'_>) -> usize {
    match results {
        QueryResults::Solutions(s) => s.inspect(|r| assert!(r.is_ok())).count(),
        QueryResults::Boolean(_) => 1,
        QueryResults::Graph(g) => g.inspect(|t| assert!(t.is_ok())).count(),
    }
}

fn evaluator() -> SparqlEvaluator {
    tripletrail::geo::register(SparqlEvaluator::new())
}

/// Best of three runs.
fn best(mut run: impl FnMut() -> usize) -> (usize, Duration) {
    let mut best = Duration::MAX;
    let mut n = 0;
    for _ in 0..3 {
        let t = Instant::now();
        n = run();
        best = best.min(t.elapsed());
    }
    (n, best)
}

fn child(backend: &str, file: &str, elements: usize) {
    let bytes = std::fs::read(file).unwrap();
    let before = rss_mb();
    let t = Instant::now();
    let point_lookups = 2000;
    let mut rng = Rng(0x9E37_79B9_7F4A_7C15);
    let lookups: Vec<String> = (0..point_lookups)
        .map(|_| {
            format!(
                "{PREFIXES}SELECT ?l WHERE {{ <{BASE}ne/{}> era:lengthOfNetLinearElement ?l }}",
                rng.below(elements)
            )
        })
        .collect();
    match backend {
        "oxigraph" => {
            let store = tripletrail::oxigraph::store::Store::new().unwrap();
            let mut loader = store.bulk_loader();
            loader.load_from_slice(RdfFormat::NTriples, &bytes).unwrap();
            loader.commit().unwrap();
            println!("load\t{}", t.elapsed().as_secs_f64());
            println!("memory\t{:.0}", rss_mb() - before);
            for (name, q) in queries() {
                let (n, d) = best(|| {
                    drain(
                        evaluator()
                            .parse_query(&q)
                            .unwrap()
                            .on_store(&store)
                            .execute()
                            .unwrap(),
                    )
                });
                println!("{name}\t{}\t{n}", d.as_secs_f64());
            }
            let t = Instant::now();
            for q in &lookups {
                drain(
                    evaluator()
                        .parse_query(q)
                        .unwrap()
                        .on_store(&store)
                        .execute()
                        .unwrap(),
                );
            }
            println!(
                "{point_lookups} single-element lookups\t{}\t{point_lookups}",
                t.elapsed().as_secs_f64()
            );
        }
        _ => {
            let store = tripletrail_store::Store::new();
            store
                .bulk_load(RdfFormat::NTriples, bytes.as_slice())
                .unwrap();
            println!("load\t{}", t.elapsed().as_secs_f64());
            println!("memory\t{:.0}", rss_mb() - before);
            let m = store.memory_use();
            eprintln!(
                "tripletrail store: {} terms, dictionary {:.0} MB, quad indexes {:.0} MB, {} geometries",
                m.terms,
                m.dictionary as f64 / 1e6,
                m.quads as f64 / 1e6,
                m.geometries
            );
            for (name, q) in queries() {
                let (n, d) = best(|| {
                    drain(
                        evaluator()
                            .parse_query(&q)
                            .unwrap()
                            .on_queryable_dataset(store.snapshot())
                            .execute()
                            .unwrap(),
                    )
                });
                println!("{name}\t{}\t{n}", d.as_secs_f64());
            }
            let t = Instant::now();
            for q in &lookups {
                drain(
                    evaluator()
                        .parse_query(q)
                        .unwrap()
                        .on_queryable_dataset(store.snapshot())
                        .execute()
                        .unwrap(),
                );
            }
            println!(
                "{point_lookups} single-element lookups\t{}\t{point_lookups}",
                t.elapsed().as_secs_f64()
            );
        }
    }
}

fn main() {
    let args: Vec<String> = std::env::args().skip(1).collect();
    if args.first().map(String::as_str) == Some("--child") {
        child(&args[1], &args[2], args[3].parse().unwrap());
        return;
    }
    let n: Vec<usize> = args
        .iter()
        .map(|a| a.parse().expect("numeric arguments"))
        .collect();
    let (h, v, k) = (
        *n.first().unwrap_or(&20),
        *n.get(1).unwrap_or(&20),
        *n.get(2).unwrap_or(&20),
    );
    let g = generate(h, v, k);
    let dir = tripletrail_testdir::tempdir("store-bench");
    let path = dir.join("store.nt");
    {
        let mut out = std::io::BufWriter::new(std::fs::File::create(&path).unwrap());
        for q in &g.quads {
            writeln!(out, "{q} .").unwrap();
        }
    }
    println!("# Store comparison (generated ERA-shaped network)\n");
    println!(
        "grid {h}x{v}, {k} elements between crossings: {} net elements, {} relations, {} triples, {} cores\n",
        g.elements,
        g.relations,
        g.quads.len(),
        std::thread::available_parallelism().map_or(1, |n| n.get())
    );
    let run = |backend: &str| -> Vec<(String, String, String)> {
        let out = Command::new(std::env::current_exe().unwrap())
            .args([
                "--child",
                backend,
                path.to_str().unwrap(),
                &g.elements.to_string(),
            ])
            .output()
            .unwrap();
        eprint!("{}", String::from_utf8_lossy(&out.stderr));
        String::from_utf8(out.stdout)
            .unwrap()
            .lines()
            .map(|l| {
                let mut f = l.split('\t');
                (
                    f.next().unwrap().to_owned(),
                    f.next().unwrap_or("").to_owned(),
                    f.next().unwrap_or("").to_owned(),
                )
            })
            .collect()
    };
    let ox = run("oxigraph");
    let ours = run("tripletrail");
    std::fs::remove_file(&path).ok();
    println!("| | Oxigraph (memory) | tripletrail store | speed-up | rows |");
    println!("|---|---:|---:|---:|---:|");
    for ((name, a, rows), (_, b, rows_b)) in ox.iter().zip(&ours) {
        let (a, b): (f64, f64) = (a.parse().unwrap(), b.parse().unwrap());
        assert_eq!(
            rows, rows_b,
            "{name}: both stores return the same number of rows"
        );
        if name == "memory" {
            println!(
                "| memory after load (RSS) | {a:.0} MB | {b:.0} MB | {:.1}x less | |",
                a / b
            );
        } else {
            println!(
                "| {name} | {} | {} | {:.1}x | {rows} |",
                ms(Duration::from_secs_f64(a)),
                ms(Duration::from_secs_f64(b)),
                a / b
            );
        }
    }
}
