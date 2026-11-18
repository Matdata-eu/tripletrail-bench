//! The cost of named graph grants (#204) on the query path: the same queries on the generated
//! ERA-shaped network, its subjects spread over eight named graphs, read
//!
//! - without access control (the default graph is the union of the graphs),
//! - by a caller who may read every graph (`QueryOptions::readable` naming all eight), and
//! - by a caller who may read half of them, compared with a store holding only those graphs,
//! - and under row rules (#202): an `sg:visibleIf` shape hiding about 10% of the net elements,
//!   then with `sg:hideProperties` on `era:navigability` too, compared with a store holding only the
//!   rows those rules show.
//!
//! Each pair must give the same rows; the table shows what the narrowing costs. The data
//! is generated, so the numbers show the overhead, not what real data would give.
//!
//! Usage: `access [horizontal_lines] [vertical_lines] [elements_between_crossings] [runs]`

#[path = "../common.rs"]
#[allow(dead_code)]
mod common;
#[path = "../synthetic.rs"]
mod synthetic;

use common::*;
use std::collections::hash_map::DefaultHasher;
use std::hash::{Hash, Hasher};
use std::sync::Arc;
use std::time::{Duration, Instant};
use synthetic::*;
use tripletrail::oxigraph::io::{RdfFormat, RdfParser};
use tripletrail::oxigraph::model::{Graph, NamedNodeRef, Triple};
use tripletrail::oxigraph::model::{GraphName, NamedNode, Quad};
use tripletrail::oxigraph::sparql::QueryResults;
use tripletrail::{Engine, QueryOptions, ReadableGraphs, RowRule, RowRules, RowShapes};

const GRAPHS: usize = 8;

const PREFIXES: &str = "PREFIX era: <http://data.europa.eu/949/>
PREFIX geo: <http://www.opengis.net/ont/geosparql#>
PREFIX geof: <http://www.opengis.net/def/function/geosparql/>
";

fn graph(i: usize) -> NamedNode {
    NamedNode::new_unchecked(format!("urn:graph:{i}"))
}

/// Rows, the median time of `runs` and an order-independent digest of the rows.
fn median(
    e: &Engine,
    q: &str,
    readable: Option<&ReadableGraphs>,
    runs: usize,
) -> (usize, Duration, u64) {
    median_with(e, q, readable, None, runs)
}

fn median_with(
    e: &Engine,
    q: &str,
    readable: Option<&ReadableGraphs>,
    rows: Option<&RowRules>,
    runs: usize,
) -> (usize, Duration, u64) {
    let mut times = Vec::with_capacity(runs);
    let mut out = (0, 0);
    for _ in 0..runs.max(1) {
        let options = QueryOptions {
            readable: readable.cloned(),
            row_rules: rows.cloned(),
            ..QueryOptions::default()
        };
        let t = Instant::now();
        let QueryResults::Solutions(s) = e.query_with_options(q, options).unwrap() else {
            panic!("{q} is no SELECT")
        };
        let rows: Vec<_> = s.map(|r| r.unwrap()).collect();
        times.push(t.elapsed());
        let digest = rows.iter().fold(0u64, |acc, r| {
            let mut h = DefaultHasher::new();
            for (v, t) in r.iter() {
                v.as_str().hash(&mut h);
                t.to_string().hash(&mut h);
            }
            acc.wrapping_add(h.finish())
        });
        out = (rows.len(), digest);
    }
    (out.0, percentile(&mut times, 0.5), out.1)
}

fn main() {
    let args: Vec<usize> = std::env::args()
        .skip(1)
        .map(|a| a.parse().expect("numeric arguments"))
        .collect();
    let (h, v, k, runs) = (
        *args.first().unwrap_or(&20),
        *args.get(1).unwrap_or(&20),
        *args.get(2).unwrap_or(&20),
        *args.get(3).unwrap_or(&7),
    );
    let g = generate(h, v, k);
    // Each subject's triples go to one graph, chosen by its IRI.
    let quads: Vec<Quad> = g
        .quads
        .into_iter()
        .map(|q| {
            let mut hasher = DefaultHasher::new();
            q.subject.to_string().hash(&mut hasher);
            let i = (hasher.finish() % GRAPHS as u64) as usize;
            Quad::new(
                q.subject,
                q.predicate,
                q.object,
                GraphName::NamedNode(graph(i)),
            )
        })
        .collect();
    let triples = quads.len();
    // The half grant is compared with a store that holds only those graphs.
    let halved: Vec<Quad> = quads
        .iter()
        .filter(|q| (0..GRAPHS / 2).any(|i| q.graph_name == GraphName::NamedNode(graph(i))))
        .cloned()
        .collect();
    let engine = Engine::new().unwrap();
    engine.load_quads(quads).unwrap();
    engine.set_union_default_graph(true);
    let only_half = Engine::new().unwrap();
    only_half.load_quads(halved).unwrap();
    only_half.set_union_default_graph(true);
    println!(
        "# Named graph grants ({} store)\n\n{} net elements, {triples} triples in {GRAPHS} graphs, median of {runs} runs\n",
        engine.store().kind(),
        g.elements,
    );
    let all = ReadableGraphs {
        default_graph: false,
        named: (0..GRAPHS).map(graph).collect(),
    };
    let half = ReadableGraphs {
        default_graph: false,
        named: (0..GRAPHS / 2).map(graph).collect(),
    };
    let window = "\"POLYGON((5.5 58.2, 6.6 58.2, 6.6 58.9, 5.5 58.9, 5.5 58.2))\"^^geo:wktLiteral";
    let queries = [
        ("count every triple", "SELECT (COUNT(*) AS ?n) { ?s ?p ?o }".to_owned()),
        (
            "net elements and their lengths",
            "SELECT ?ne ?l { ?ne a era:LinearElement ; era:lengthOfNetLinearElement ?l }".to_owned(),
        ),
        (
            "net elements per navigability",
            "SELECT ?nav (COUNT(*) AS ?n) { ?r a era:NetRelation ; era:navigability ?nav } GROUP BY ?nav".to_owned(),
        ),
        (
            "relations from element to element (join)",
            "SELECT ?a ?b { ?r era:elementA ?a ; era:elementB ?b . ?a a era:LinearElement . ?b a era:LinearElement }".to_owned(),
        ),
        (
            "two hops along relations (path)",
            "SELECT (COUNT(*) AS ?n) { ?a ^era:elementA/era:elementB/^era:elementA/era:elementB ?b }".to_owned(),
        ),
        (
            "net elements in a window (spatial)",
            format!("SELECT ?ne {{ ?ne a era:LinearElement ; geo:hasGeometry/geo:asWKT ?w FILTER(geof:sfIntersects(?w, {window})) }}"),
        ),
    ];
    println!(
        "| query | rows | no access control | all graphs granted | ratio | rows | store of half the graphs | half granted | ratio |\n|---|---:|---:|---:|---:|---:|---:|---:|---:|"
    );
    for (name, q) in &queries {
        let q = format!("{PREFIXES}{q}");
        // Warm the caches and the spatial views once for each mode.
        for r in [None, Some(&all), Some(&half)] {
            median(&engine, &q, r, 1);
        }
        median(&only_half, &q, None, 1);
        let (n, plain, d) = median(&engine, &q, None, runs);
        let (n_all, granted, d_all) = median(&engine, &q, Some(&all), runs);
        assert_eq!(
            (n, d),
            (n_all, d_all),
            "granting every graph changed the rows of {name}"
        );
        let (n_half, halved, d_half) = median(&engine, &q, Some(&half), runs);
        let (n_own, own, d_own) = median(&only_half, &q, None, runs);
        assert_eq!(
            (n_half, d_half),
            (n_own, d_own),
            "the half grant and the store of those graphs differ on {name}"
        );
        let ratio = |t: Duration, base: Duration| t.as_secs_f64() / base.as_secs_f64().max(1e-9);
        println!(
            "| {name} | {n} | {} | {} | {:.2} | {n_half} | {} | {} | {:.2} |",
            ms(plain),
            ms(granted),
            ratio(granted, plain),
            ms(own),
            ms(halved),
            ratio(halved, own),
        );
    }
    row_rules(&engine, &queries, runs);
}

/// The row rules' table: each rule set against a store holding only what it shows.
fn row_rules(engine: &Engine, queries: &[(&str, String)], runs: usize) {
    // Row-level policies are an enterprise feature (#818).
    #[cfg(feature = "enterprise")]
    tripletrail_enterprise::rows::install();
    if !tripletrail::row_policies_available() {
        println!("\nRow rules: skipped (build with --features enterprise)");
        return;
    }
    // The length under which a net element is hidden: about the shortest 10%.
    let QueryResults::Solutions(s) = engine
        .query(&format!(
            "{PREFIXES}SELECT ?l {{ ?ne era:lengthOfNetLinearElement ?l }} ORDER BY ?l"
        ))
        .unwrap()
    else {
        unreachable!()
    };
    let lengths: Vec<String> = s
        .map(|r| match r.unwrap().get("l") {
            Some(tripletrail::oxigraph::model::Term::Literal(l)) => l.value().to_owned(),
            _ => unreachable!(),
        })
        .collect();
    let cut = &lengths[lengths.len() / 10];
    let shapes = |hide: bool| -> Graph {
        let ttl = format!(
            "@prefix sh: <http://www.w3.org/ns/shacl#> . @prefix era: <http://data.europa.eu/949/> .
             @prefix ex: <urn:shapes:> . @prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
             ex:Long a sh:NodeShape ; sh:targetClass era:LinearElement ;
               sh:property [ sh:path era:lengthOfNetLinearElement ;
                             sh:minInclusive \"{cut}\"^^xsd:double ] .
             {}",
            if hide {
                "ex:NoNavigability a sh:NodeShape ; sh:property [ sh:path era:navigability ] ."
            } else {
                ""
            }
        );
        RdfParser::from_format(RdfFormat::Turtle)
            .for_slice(ttl.as_bytes())
            .map(|q| Triple::from(q.unwrap()))
            .collect()
    };
    let shape = |local: &str| -> tripletrail::oxigraph::model::Term {
        NamedNodeRef::new_unchecked(&format!("urn:shapes:{local}"))
            .into_owned()
            .into()
    };
    let sets = [
        (
            "visibleIf, ~10% of the net elements hidden",
            RowRules {
                shapes: Arc::new(RowShapes::new(shapes(false))),
                rules: vec![RowRule::VisibleIf {
                    shape: shape("Long"),
                    references: true,
                }],
                agent: None,
                graphs: None,
            },
        ),
        (
            "visibleIf and hideProperties (navigability)",
            RowRules {
                shapes: Arc::new(RowShapes::new(shapes(true))),
                rules: vec![
                    RowRule::VisibleIf {
                        shape: shape("Long"),
                        references: true,
                    },
                    RowRule::HideProperties {
                        shape: shape("NoNavigability"),
                    },
                ],
                agent: None,
                graphs: None,
            },
        ),
    ];
    for (title, rules) in &sets {
        // The store of the visible rows, read through the rules themselves, in the same
        // graphs and with the same union default graph as the store under the rules.
        let QueryResults::Solutions(visible) = engine
            .query_with_options(
                "SELECT ?s ?p ?o ?g WHERE { GRAPH ?g { ?s ?p ?o } }",
                QueryOptions {
                    row_rules: Some(rules.clone()),
                    ..QueryOptions::default()
                },
            )
            .unwrap()
        else {
            unreachable!()
        };
        use tripletrail::oxigraph::model::{NamedOrBlankNode, Term};
        let quads: Vec<Quad> = visible
            .map(|r| {
                let r = r.unwrap();
                let subject = match r.get("s").unwrap().clone() {
                    Term::NamedNode(n) => NamedOrBlankNode::NamedNode(n),
                    Term::BlankNode(b) => NamedOrBlankNode::BlankNode(b),
                    _ => unreachable!(),
                };
                let Some(Term::NamedNode(p)) = r.get("p").cloned() else {
                    unreachable!()
                };
                let Some(Term::NamedNode(g)) = r.get("g").cloned() else {
                    unreachable!()
                };
                Quad::new(
                    subject,
                    p,
                    r.get("o").unwrap().clone(),
                    GraphName::NamedNode(g),
                )
            })
            .collect();
        let shown = quads.len();
        let only = Engine::new().unwrap();
        only.load_quads(quads).unwrap();
        only.set_union_default_graph(true);
        println!(
            "\n## Row rules: {title}\n\n{shown} triples shown\n\n| query | rows | store of the shown rows | row rules | ratio |\n|---|---:|---:|---:|---:|"
        );
        for (name, q) in queries {
            let q = format!("{PREFIXES}{q}");
            median_with(engine, &q, None, Some(rules), 1);
            median(&only, &q, None, 1);
            let (n_own, own, d_own) = median(&only, &q, None, runs);
            let (n, ruled, d) = median_with(engine, &q, None, Some(rules), runs);
            assert_eq!(
                (n, d),
                (n_own, d_own),
                "the row rules and the store of the shown rows differ on {name}"
            );
            println!(
                "| {name} | {n} | {} | {} | {:.2} |",
                ms(own),
                ms(ruled),
                ruled.as_secs_f64() / own.as_secs_f64().max(1e-9),
            );
        }
    }
}
