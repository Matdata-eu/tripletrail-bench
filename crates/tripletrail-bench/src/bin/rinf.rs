//! Phase-0 benchmark on real RINF data.
//!
//! Loads N-Triples files exported from the ERA knowledge graph (graph.data.era.europa.eu,
//! repository `rinf-plus`, one file per named graph) into the default graph and times:
//! loading, routing on the micro topology (`profiles/era-micro.rq`, only where an infrastructure
//! manager publishes it), routing on the section-of-line network (`profiles/era-sol.rq`,
//! published for every country) and the spatial workloads of the synthetic benchmark on the
//! real geometries.
//!
//! Usage: `rinf [--backend oxigraph|tripletrail] [--store <dir>] [--queries <n>] <file.nt>...`
//!
//! `--backend` picks Oxigraph's store (the default) or the tripletrail store. With `--store` the data
//! goes to an on-disk store (Oxigraph's needs feature `rocksdb`); a store that already holds
//! data is reused without loading. All files are loaded in one bulk load.
//!
//! Every query line ends with a digest of its solutions that does not depend on row order, so
//! two runs on different backends can be compared line by line.

#[path = "../common.rs"]
mod common;

use common::*;
use std::fs::File;
use std::io::{BufReader, Read};
use std::time::{Duration, Instant};
use tripletrail::Engine;
use tripletrail::oxigraph::io::{RdfFormat, RdfParser};
use tripletrail::oxigraph::model::Term;
use tripletrail::oxigraph::sparql::QueryResults;
use tripletrail::oxigraph::store::Store;

const PREFIXES: &str = "PREFIX era: <http://data.europa.eu/949/>
PREFIX geo: <http://www.opengis.net/ont/geosparql#>
PREFIX geof: <http://www.opengis.net/def/function/geosparql/>
PREFIX st: <http://w3id.org/tripletrail/st#>
PREFIX pgr: <http://w3id.org/tripletrail/pgr#>
";

fn open_engine(backend: &str, path: Option<&str>) -> Engine {
    match (backend, path) {
        ("tripletrail", None) => Engine::new_tripletrail(),
        ("tripletrail", Some(p)) => Engine::open_tripletrail(p).unwrap(),
        ("oxigraph", p) => Engine::from_store(open_store(p)),
        (b, _) => panic!("unknown backend {b}, expected oxigraph or tripletrail"),
    }
}

fn open_store(path: Option<&str>) -> Store {
    match path {
        #[cfg(feature = "rocksdb")]
        Some(p) => Store::open(p).unwrap(),
        #[cfg(not(feature = "rocksdb"))]
        Some(_) => panic!("--store needs the rocksdb feature"),
        None => Store::new().unwrap(),
    }
}

/// The IRIs of the first column, sorted so samples do not depend on the store's order.
fn iris(e: &Engine, q: &str) -> Vec<String> {
    let QueryResults::Solutions(s) = e.query(q).unwrap() else {
        panic!()
    };
    let mut v: Vec<_> = s
        .filter_map(|r| match r.unwrap().values()[0].clone() {
            Some(Term::NamedNode(n)) => Some(n.into_string()),
            _ => None,
        })
        .collect();
    v.sort();
    v
}

/// Times one routing function over random pairs of `vertices` on an already cached network.
fn route_pairs(
    e: &Engine,
    head: &str,
    edges: &str,
    vertices: &[(String, String)],
    queries: usize,
    rng: &mut Rng,
) {
    let pairs: Vec<_> = (0..queries)
        .map(|_| {
            (
                &vertices[rng.below(vertices.len())],
                &vertices[rng.below(vertices.len())],
            )
        })
        .collect();
    for func in ["pgr_dijkstra", "pgr_bdDijkstra", "pgr_dijkstraCost"] {
        let out = if func == "pgr_dijkstraCost" {
            "pgr:agg_cost ?agg"
        } else {
            "pgr:node ?node ; pgr:edge ?edge ; pgr:agg_cost ?agg"
        };
        let (mut totals, mut searches, mut found_totals, mut found_searches) =
            (Vec::new(), Vec::new(), Vec::new(), Vec::new());
        let (mut rows, mut digest) = (0, 0u64);
        for (a, b) in &pairs {
            let q = format!(
                "{head}SELECT * WHERE {{ SERVICE <http://w3id.org/tripletrail/pgr> {{
  [] pgr:function pgr:{func} ; pgr:start_vid {} ; pgr:end_vid {} ; {out} .
  {{ {edges} }} }} }}",
                a.0, b.1
            );
            let (n, t, d) = count_digest(e, &q);
            digest = digest.wrapping_add(d);
            let s = e.last_routing_stats();
            assert!(s.cache_hit);
            totals.push(t);
            searches.push(s.search);
            if n > 0 {
                rows += n;
                found_totals.push(t);
                found_searches.push(s.search);
            }
        }
        let found = found_totals.len();
        let p = |v: &mut Vec<Duration>, q| {
            if v.is_empty() {
                "-".into()
            } else {
                ms(percentile(v, q))
            }
        };
        println!(
            "{func}: {queries} random pairs, {found} routable, {:.0} rows/route | all: query p50 {} p95 {}, search p50 {} p95 {} | routable only: query p50 {} p95 {}, search p50 {} p95 {} | digest {digest:016x}",
            rows as f64 / found.max(1) as f64,
            p(&mut totals, 0.5),
            p(&mut totals, 0.95),
            p(&mut searches, 0.5),
            p(&mut searches, 0.95),
            p(&mut found_totals, 0.5),
            p(&mut found_totals, 0.95),
            p(&mut found_searches, 0.5),
            p(&mut found_searches, 0.95),
        );
    }
}

/// Builds the network of `profile` with a first (cache-miss) query, then routes random pairs.
/// `vertices` are (start, end) vertex terms in SPARQL syntax per sampled place.
fn routing(e: &Engine, title: &str, profile: &str, vertices: &[(String, String)], queries: usize) {
    println!("## Routing: {title}\n");
    if vertices.len() < 2 {
        println!("no vertices in the data, skipped\n");
        return;
    }
    // Profile prefixes go after the shared ones so they win where both declare one.
    let (prefixes, edges) = split_profile(profile);
    let head = format!("{PREFIXES}{prefixes}\n");
    let q = format!(
        "{head}SELECT * WHERE {{ SERVICE <http://w3id.org/tripletrail/pgr> {{
  [] pgr:function pgr:pgr_dijkstraCost ; pgr:start_vid {} ; pgr:end_vid {} ; pgr:agg_cost ?agg .
  {{ {edges} }} }} }}",
        vertices[0].0, vertices[1].1
    );
    let (_, first) = count(e, &q);
    let s = e.last_routing_stats();
    println!(
        "sampled places: {}, edge-set rows: {}, graph vertices: {}, arcs: {}",
        vertices.len(),
        s.build.rows,
        s.build.vertices,
        s.build.arcs
    );
    println!("first query (cache miss): {} total", ms(first));
    println!("  edge query evaluation: {}", ms(s.build.edge_query));
    println!("  term interning + CSR build: {}", ms(s.build.build));
    let mut rng = Rng(0x9E37_79B9_7F4A_7C15);
    route_pairs(e, &head, &edges, vertices, queries, &mut rng);
    let start = &vertices[vertices.len() / 2].0;
    for km in [20, 100] {
        let (n, t, d) = count_digest(
            e,
            &format!(
                "{head}SELECT * WHERE {{ SERVICE <http://w3id.org/tripletrail/pgr> {{
  [] pgr:function pgr:pgr_drivingDistance ; pgr:start_vid {start} ; pgr:distance {} ; pgr:node ?n ; pgr:agg_cost ?c .
  {{ {edges} }} }} }}",
                km * 1000
            ),
        );
        println!(
            "pgr_drivingDistance {km} km: {n} vertices reached in {} | digest {d:016x}",
            ms(t)
        );
    }
    println!();
}

fn main() {
    let mut args = std::env::args().skip(1);
    let (mut store_path, mut queries, mut files) = (None, 200, Vec::new());
    let mut backend = "oxigraph".to_string();
    while let Some(a) = args.next() {
        match a.as_str() {
            "--store" => store_path = args.next(),
            "--backend" => backend = args.next().unwrap(),
            "--queries" => queries = args.next().unwrap().parse().unwrap(),
            _ => files.push(a),
        }
    }

    println!("# tripletrail benchmark on real RINF data ({backend} store)\n");
    let engine = open_engine(&backend, store_path.as_deref());
    let store = engine.store();
    if store.is_empty().unwrap() {
        let t = Instant::now();
        let reader = files
            .iter()
            .fold(Box::new(std::io::empty()) as Box<dyn Read>, |r, f| {
                Box::new(r.chain(BufReader::new(File::open(f).unwrap())))
            });
        store
            .load(
                RdfParser::from_format(RdfFormat::NTriples).lenient(),
                reader,
            )
            .unwrap();
        println!("bulk load of {} files: {}", files.len(), ms(t.elapsed()));
    } else {
        println!("reusing loaded store");
    }
    let (triples, t) = first_value(&engine, "SELECT (COUNT(*) AS ?n) WHERE { ?s ?p ?o }");
    println!(
        "triples: {}, counted in {}",
        triples.split('"').nth(1).unwrap_or(&triples),
        ms(t)
    );
    if let Some(mb) = peak_rss_mb() {
        println!("peak RSS after load: {mb:.0} MB");
    }
    // Hand freed load buffers back to the OS, so RSS shows what the store keeps.
    #[cfg(all(target_os = "linux", target_env = "gnu"))]
    {
        unsafe extern "C" {
            fn malloc_trim(pad: usize) -> i32;
        }
        unsafe { malloc_trim(0) };
    }
    if let Some(mb) = rss_mb() {
        println!("RSS after load (freed memory returned): {mb:.0} MB");
    }
    if let tripletrail::store::Dataset::TripleTrail(s) = store {
        let m = s.memory_use();
        println!(
            "tripletrail store: {} terms, dictionary {:.0} MB, quad indexes {:.0} MB, {} geometries",
            m.terms,
            m.dictionary as f64 / 1e6,
            m.quads as f64 / 1e6,
            m.geometries
        );
    }
    println!();

    // Micro topology: route between elements, both travelled forward.
    let elements: Vec<_> = iris(
        &engine,
        &format!("{PREFIXES}SELECT ?e WHERE {{ ?e a era:LinearElement ; era:lengthOfNetLinearElement ?l }}"),
    )
    .into_iter()
    .map(|e| (format!("\"{e}#fwd\""), format!("\"{e}#fwd\"")))
    .collect();
    routing(
        &engine,
        "micro topology (era-micro profile)",
        include_str!("../../../../core/profiles/era-micro.rq"),
        &elements,
        queries,
    );
    routing(
        &engine,
        "micro topology, reversing allowed (era-micro-reversing profile)",
        include_str!("../../../../core/profiles/era-micro-reversing.rq"),
        &elements,
        queries,
    );

    let ops: Vec<_> = iris(
        &engine,
        &format!("{PREFIXES}SELECT DISTINCT ?op WHERE {{ ?sol a era:SectionOfLine ; era:opStart|era:opEnd ?op }}"),
    )
    .into_iter()
    .map(|o| (format!("<{o}>"), format!("<{o}>")))
    .collect();
    routing(
        &engine,
        "sections of line (era-sol profile)",
        include_str!("../../../../core/profiles/era-sol.rq"),
        &ops,
        queries,
    );

    // --- Spatial -----------------------------------------------------------------------
    println!("## Spatial (functions through the evaluator hook, no spatial index yet)\n");
    let (n, t, d) = count_digest(
        &engine,
        &format!("{PREFIXES}SELECT ?w WHERE {{ ?g geo:asWKT ?w }}"),
    );
    println!(
        "geo:asWKT literals: {n}, scanned in {} | digest {d:016x}",
        ms(t)
    );
    let (n, t, d) = count_digest(
        &engine,
        &format!(
            "{PREFIXES}SELECT ?w WHERE {{ ?g geo:asWKT ?w FILTER(geof:isEmpty(?w) = false) }}"
        ),
    );
    println!(
        "parse as WKT (geof:isEmpty bound): {n}, {} | digest {d:016x}",
        ms(t)
    );
    // Boxes around a few RINF cities, ~0.5 x 0.4 degrees.
    for (name, lon, lat) in [
        ("Oslo", 10.75, 59.91),
        ("Brussels", 4.35, 50.85),
        ("Frankfurt", 8.68, 50.11),
        ("Vilnius", 25.28, 54.69),
    ] {
        let area = format!(
            "\"POLYGON(({a} {b}, {c} {b}, {c} {d}, {a} {d}, {a} {b}))\"^^geo:wktLiteral",
            a = lon - 0.25,
            b = lat - 0.2,
            c = lon + 0.25,
            d = lat + 0.2
        );
        let filter = format!(
            "{PREFIXES}SELECT ?g WHERE {{ ?g geo:asWKT ?w FILTER(geof:sfIntersects(?w, {area})) }}"
        );
        for cache in [false, true] {
            tripletrail::geo::set_cache_enabled(cache);
            let (n, t, d) = count_digest(&engine, &filter);
            println!(
                "sfIntersects FILTER, {name} box (parse cache {}): {n} hits, {} | digest {d:016x}",
                if cache { "on" } else { "off" },
                ms(t)
            );
        }
    }
    let (v, t) = first_value(
        &engine,
        &format!(
            "{PREFIXES}SELECT (SUM(geof:metricLength(?w)) AS ?m) WHERE {{ ?g geo:asWKT ?w FILTER(STRSTARTS(STR(?w), \"LINESTRING\")) }}"
        ),
    );
    println!(
        "SUM(geof:metricLength) over all linestrings: {} m, {}",
        v.split('"').nth(1).unwrap_or(&v),
        ms(t)
    );
    let (n, t, d) = count_digest(
        &engine,
        &format!(
            "{PREFIXES}SELECT ?g ?f WHERE {{ ?g geo:asWKT ?w FILTER(STRSTARTS(STR(?w), \"LINESTRING\")) BIND(st:ST_LineLocatePoint(?w, st:ST_Centroid(?w)) AS ?f) }}"
        ),
    );
    println!(
        "ST_LineLocatePoint(?w, ST_Centroid(?w)) for {n} linestrings: {} | digest {d:016x}",
        ms(t)
    );
    let (n, t, d) = count_digest(
        &engine,
        &format!(
            "{PREFIXES}SELECT ?g WHERE {{ ?g geo:asWKT ?w FILTER(geof:distance(?w, \"POINT(10.75 59.91)\"^^geo:wktLiteral) < 2000) }}"
        ),
    );
    println!(
        "geof:distance < 2 km of Oslo S FILTER: {n} hits, {} | digest {d:016x}",
        ms(t)
    );
    if let Some(mb) = peak_rss_mb() {
        println!("\npeak RSS: {mb:.0} MB");
    }
}
