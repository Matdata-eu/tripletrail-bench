//! Times spatial queries with the spatial rewrite's cost model off (fixed rules) and on, on the
//! generated ERA-shaped network with operational points and signals added, and checks both give
//! the same rows. The data is generated: the timings show what each decision is worth, not what
//! real RINF data would give.
//!
//! A second table times joins of two large sides with the index nested loop and with the
//! sweep-line join, both under the cost model.
//!
//! Usage: `cost [horizontal_lines] [vertical_lines] [elements_between_crossings] [runs]`

#[path = "../common.rs"]
#[allow(dead_code)]
mod common;
#[path = "../synthetic.rs"]
mod synthetic;

use common::*;
use std::time::{Duration, Instant};
use synthetic::*;
use tripletrail::Engine;
use tripletrail::oxigraph::model::vocab::{rdf, xsd};
use tripletrail::oxigraph::model::{GraphName, Literal, NamedNode, Quad, Term};

const PREFIXES: &str = "PREFIX era: <http://data.europa.eu/949/>
PREFIX geo: <http://www.opengis.net/ont/geosparql#>
PREFIX geof: <http://www.opengis.net/def/function/geosparql/>
";

/// Operational points (one every `every` net elements, named and typed) and signals (one at the
/// start of every other element), each with a point geometry: what RINF adds to the topology.
fn railway_objects(g: &Gen, every: usize) -> (Vec<Quad>, usize, usize) {
    let mut quads = Vec::new();
    let nn = |s: String| NamedNode::new_unchecked(s);
    let wkt = nn(format!("{GSP}wktLiteral"));
    let mut add = |s: &NamedNode, p: String, o: Term| {
        quads.push(Quad::new(s.clone(), nn(p), o, GraphName::DefaultGraph));
    };
    // Element start points, from their geometry literals.
    let starts: Vec<(f64, f64)> = g
        .quads
        .iter()
        .filter(|q| q.predicate.as_str() == format!("{GSP}asWKT"))
        .filter_map(|q| match &q.object {
            Term::Literal(l) => {
                let inner = l.value().strip_prefix("LINESTRING(")?;
                let mut first = inner.split(',').next()?.split_whitespace();
                Some((first.next()?.parse().ok()?, first.next()?.parse().ok()?))
            }
            _ => None,
        })
        .collect();
    let (mut ops, mut signals) = (0, 0);
    for (i, &(x, y)) in starts.iter().enumerate() {
        if i % every == 0 {
            let op = nn(format!("{BASE}op/{ops}"));
            let geom = nn(format!("{BASE}op/{ops}/geom"));
            add(
                &op,
                rdf::TYPE.as_str().into(),
                nn(format!("{ERA}OperationalPoint")).into(),
            );
            add(
                &op,
                format!("{ERA}opName"),
                Literal::from(format!("OP {ops}")).into(),
            );
            add(&op, format!("{GSP}hasGeometry"), geom.clone().into());
            let point = format!("POINT({:.6} {:.6})", x + 0.0001, y + 0.0001);
            add(
                &geom,
                format!("{GSP}asWKT"),
                Literal::new_typed_literal(point, wkt.clone()).into(),
            );
            ops += 1;
        }
        if i % 2 == 0 {
            let s = nn(format!("{BASE}signal/{signals}"));
            let geom = nn(format!("{BASE}signal/{signals}/geom"));
            add(
                &s,
                rdf::TYPE.as_str().into(),
                nn(format!("{ERA}Signal")).into(),
            );
            add(
                &s,
                format!("{ERA}signalOrientation"),
                Literal::new_typed_literal(format!("{}", signals % 2), xsd::INTEGER).into(),
            );
            add(&s, format!("{GSP}hasGeometry"), geom.clone().into());
            let point = format!("POINT({:.6} {:.6})", x - 0.0001, y - 0.0001);
            add(
                &geom,
                format!("{GSP}asWKT"),
                Literal::new_typed_literal(point, wkt.clone()).into(),
            );
            signals += 1;
        }
    }
    (quads, ops, signals)
}

/// The first run (which builds the index, or gathers statistics), then the median of `runs`.
fn median(e: &Engine, q: &str, runs: usize) -> (usize, Duration, Duration, u64) {
    let (n, first, digest) = count_digest(e, q);
    let mut times: Vec<Duration> = (0..runs)
        .map(|_| {
            let (m, t, d) = count_digest(e, q);
            assert_eq!((m, d), (n, digest));
            t
        })
        .collect();
    (n, first, percentile(&mut times, 0.5), digest)
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
        *args.get(3).unwrap_or(&5),
    );
    let mut g = generate(h, v, k);
    let (objects, ops, signals) = railway_objects(&g, 25);
    g.quads.extend(objects);
    let engine = Engine::new().unwrap();
    let t = Instant::now();
    let triples = g.quads.len();
    engine.load_quads(g.quads).unwrap();
    println!(
        "# Spatial cost model ({} store)\n\n{} net elements, {ops} operational points, {signals} signals, {triples} triples, loaded in {}\n",
        engine.store().kind(),
        g.elements,
        ms(t.elapsed())
    );

    // The network spans about 5..(5 + 0.009 (v + 1) k) east and 58..(58 + 25) north at most.
    let whole = "\"POLYGON((4 57, 60 57, 60 85, 4 85, 4 57))\"^^geo:wktLiteral";
    let window =
        "\"POLYGON((5.66 58.38, 5.74 58.38, 5.74 58.42, 5.66 58.42, 5.66 58.38))\"^^geo:wktLiteral";
    let medium = "\"POLYGON((5.5 58.2, 6.6 58.2, 6.6 58.9, 5.5 58.9, 5.5 58.2))\"^^geo:wktLiteral";
    let queries = [
        (
            "named OP inside a polygon around the whole network",
            format!(
                "SELECT ?op WHERE {{ ?op era:opName \"OP 17\" ; geo:hasGeometry/geo:asWKT ?w FILTER(geof:sfIntersects(?w, {whole})) }}"
            ),
        ),
        (
            "every geometry inside a polygon around the whole network",
            format!("SELECT ?g WHERE {{ ?g geo:asWKT ?w FILTER(geof:sfIntersects(?w, {whole})) }}"),
        ),
        (
            "net elements in a small window",
            format!(
                "SELECT ?ne WHERE {{ ?ne a era:LinearElement ; geo:hasGeometry/geo:asWKT ?w FILTER(geof:sfIntersects(?w, {window})) }}"
            ),
        ),
        (
            "net elements in a larger window",
            format!(
                "SELECT ?ne WHERE {{ ?ne a era:LinearElement ; geo:hasGeometry/geo:asWKT ?w FILTER(geof:sfIntersects(?w, {medium})) }}"
            ),
        ),
        (
            "net elements within 1 km of a named OP (join)",
            "SELECT ?ne WHERE { ?op era:opName \"OP 17\" ; geo:hasGeometry/geo:asWKT ?w1 . \
             ?ne a era:LinearElement ; geo:hasGeometry/geo:asWKT ?w2 FILTER(geof:distance(?w1, ?w2) < 1000) }"
                .to_owned(),
        ),
        (
            "signals within 200 m of OPs in a window (join)",
            format!(
                "SELECT ?op ?s WHERE {{ ?op a era:OperationalPoint ; geo:hasGeometry/geo:asWKT ?w1 . \
                 ?s a era:Signal ; geo:hasGeometry/geo:asWKT ?w2 \
                 FILTER(geof:sfIntersects(?w1, {medium}) && geof:distance(?w1, ?w2) < 200) }}"
            ),
        ),
    ];
    println!(
        "| query | rows | fixed rules | cost model | speed-up | cost model, first run | decisions |\n|---|---:|---:|---:|---:|---:|---|"
    );
    for (name, q) in &queries {
        let q = format!("{PREFIXES}{q}");
        engine.set_cost_model(false);
        let (n_fixed, _, fixed, d_fixed) = median(&engine, &q, runs);
        // With the cost model off no statistics are gathered: the first run below gathers
        // those of this query not cached by an earlier one (and builds the histogram once).
        engine.set_cost_model(true);
        let (n, first, costed, d) = median(&engine, &q, runs);
        assert_eq!(
            (n, d),
            (n_fixed, d_fixed),
            "the cost model changed the result of {name}"
        );
        let decisions: Vec<String> = engine
            .last_spatial_stats()
            .decisions
            .iter()
            .map(ToString::to_string)
            .collect();
        println!(
            "| {name} | {n} | {} | {} | {:.1}x | {} | {} |",
            ms(fixed),
            ms(costed),
            fixed.as_secs_f64() / costed.as_secs_f64(),
            ms(first),
            decisions.join("; ")
        );
    }

    // Joins of two large sides: the index nested loop against the sweep-line join, both with
    // the cost model. With the fixed rules the evaluator would start from the cartesian
    // product of the two sides, which takes minutes.
    let joins = [
        (
            "signals within 50 m of operational points",
            "SELECT ?s ?op WHERE { ?s a era:Signal ; geo:hasGeometry/geo:asWKT ?w1 . \
             ?op a era:OperationalPoint ; geo:hasGeometry/geo:asWKT ?w2 FILTER(geof:distance(?w1, ?w2) < 50) }",
        ),
        (
            "signals within 20 m of net elements",
            "SELECT ?s ?ne WHERE { ?s a era:Signal ; geo:hasGeometry/geo:asWKT ?w1 . \
             ?ne a era:LinearElement ; geo:hasGeometry/geo:asWKT ?w2 FILTER(geof:distance(?w1, ?w2) < 20) }",
        ),
        (
            "net relations whose elements intersect (all geometries x all)",
            "SELECT ?nr WHERE { ?nr era:elementA ?a ; era:elementB ?b . \
             ?a geo:hasGeometry/geo:asWKT ?wa . ?b geo:hasGeometry/geo:asWKT ?wb \
             FILTER(geof:sfIntersects(?wa, ?wb)) }",
        ),
    ];
    println!(
        "\n## Large joins\n\nTimes are medians: the whole query, the spatial rewrite (side evaluation and pairing), and the pairing alone.\n\n| join | rows | pairs | nested loop: query | rewrite | pairing | sweep: query | rewrite | pairing | pairing speed-up | decisions |\n|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|"
    );
    for (name, q) in &joins {
        let q = format!("{PREFIXES}{q}");
        let mut timed = Vec::new();
        for sweep in [false, true] {
            engine.set_sweep_join(sweep);
            let (n, _, total, d) = median(&engine, &q, runs);
            // The rewrite's share, and the pairing's: their medians over as many more runs.
            let (mut rewrite, mut pairing): (Vec<Duration>, Vec<Duration>) = (0..runs)
                .map(|_| {
                    count_digest(&engine, &q);
                    let stats = engine.last_spatial_stats();
                    (stats.lookup, stats.pairing)
                })
                .unzip();
            timed.push((
                (n, d),
                [
                    total,
                    percentile(&mut rewrite, 0.5),
                    percentile(&mut pairing, 0.5),
                ],
                engine.last_spatial_stats(),
            ));
        }
        let (result, nested, _) = &timed[0];
        let (swept_result, swept, stats) = &timed[1];
        assert_eq!(
            result, swept_result,
            "the sweep changed the result of {name}"
        );
        let decisions: Vec<String> = stats.decisions.iter().map(ToString::to_string).collect();
        let times: Vec<String> = nested.iter().chain(swept).map(|t| ms(*t)).collect();
        println!(
            "| {name} | {} | {} | {} | {:.1}x | {} |",
            result.0,
            stats.candidates,
            times.join(" | "),
            nested[2].as_secs_f64() / swept[2].as_secs_f64(),
            decisions.join("; ")
        );
    }
}
