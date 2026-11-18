//! Phase-0 benchmark.
//!
//! Generates a synthetic network shaped like ERA RINF micro topology (net elements with
//! length and WKT geometry, net relations with navigability, switches whose diverging legs
//! are not navigable between each other), loads it into the engine and times:
//! loading, building the routing graph from the ERA profile edge query, routing queries,
//! and a few GeoSPARQL/ST_* workloads. The data is generated: timings are indicative of
//! engine mechanics, not of real RINF content.
//!
//! Usage: `tripletrail-bench [horizontal_lines] [vertical_lines] [elements_between_crossings] [queries]`

use std::time::{Duration, Instant};
use tripletrail::Engine;

mod common;
use common::*;

mod synthetic;
use synthetic::*;

fn main() {
    let args: Vec<usize> = std::env::args()
        .skip(1)
        .map(|a| a.parse().expect("numeric arguments"))
        .collect();
    let (h, v, k, queries) = (
        *args.first().unwrap_or(&20),
        *args.get(1).unwrap_or(&20),
        *args.get(2).unwrap_or(&20),
        *args.get(3).unwrap_or(&200),
    );

    println!("# tripletrail benchmark (synthetic ERA-shaped network)\n");
    let t = Instant::now();
    let g = generate(h, v, k);
    let (elements, relations, triples) = (g.elements, g.relations, g.quads.len());
    println!("grid {h}x{v}, {k} elements between crossings");
    println!("net elements: {elements}, net relations: {relations}, triples: {triples}");
    println!("generate: {}", ms(t.elapsed()));

    let engine = Engine::new().unwrap();
    let t = Instant::now();
    engine.load_quads(g.quads).unwrap();
    let load = t.elapsed();
    println!(
        "bulk load: {} ({:.0} triples/s)\n",
        ms(load),
        triples as f64 / load.as_secs_f64()
    );

    // --- Routing -----------------------------------------------------------------------
    let (profile_prefixes, edges) = split_profile(include_str!("../../../core/profiles/era-micro.rq"));
    let route = |func: &str, from: usize, to: usize, out: &str| {
        format!(
            r#"{profile_prefixes}
PREFIX pgr: <http://w3id.org/tripletrail/pgr#>
SELECT * WHERE {{ SERVICE <http://w3id.org/tripletrail/pgr> {{
  [] pgr:function pgr:{func} ; pgr:start_vid "{BASE}ne/{from}#fwd" ; pgr:end_vid "{BASE}ne/{to}#fwd" ; {out} .
  {{ {edges} }}
}} }}"#
        )
    };
    let (n, first) = count(
        &engine,
        &route("pgr_dijkstraCost", 0, elements - 1, "pgr:agg_cost ?agg"),
    );
    let s = engine.last_routing_stats();
    println!("## Routing (ERA profile, edge-based graph)\n");
    println!(
        "edge-set rows: {}, graph vertices: {}, arcs: {}",
        s.build.rows, s.build.vertices, s.build.arcs
    );
    println!("first query (cache miss): {} total", ms(first));
    println!("  edge query evaluation: {}", ms(s.build.edge_query));
    println!("  term interning + CSR build: {}", ms(s.build.build));
    println!("  search: {}  ({n} result row)", ms(s.search));

    let mut rng = Rng(0x9E37_79B9_7F4A_7C15);
    let pairs: Vec<(usize, usize)> = (0..queries)
        .map(|_| (rng.below(elements), rng.below(elements)))
        .collect();
    for (func, label) in [
        ("pgr_dijkstra", "pgr_dijkstra (full path rows)"),
        ("pgr_bdDijkstra", "pgr_bdDijkstra (full path rows)"),
        ("pgr_dijkstraCost", "pgr_dijkstraCost"),
        ("pgr_trsp", "pgr_trsp (no restrictions)"),
        ("pgr_KSP", "pgr_KSP K=3 (full path rows)"),
    ] {
        let mut totals = Vec::new();
        let mut searches = Vec::new();
        let mut rows = 0;
        let mut found = 0;
        for &(a, b) in &pairs {
            let out = match func {
                "pgr_dijkstraCost" => "pgr:agg_cost ?agg",
                "pgr_KSP" => {
                    "pgr:K 3 ; pgr:path_id ?p ; pgr:node ?node ; pgr:edge ?edge ; pgr:agg_cost ?agg"
                }
                _ => "pgr:node ?node ; pgr:edge ?edge ; pgr:agg_cost ?agg",
            };
            let (n, t) = count(&engine, &route(func, a, b, out));
            let s = engine.last_routing_stats();
            assert!(s.cache_hit);
            totals.push(t);
            searches.push(s.search);
            rows += n;
            found += usize::from(n > 0);
        }
        println!(
            "{label}: {queries} random pairs, {found} routable, {:.0} rows/route | query p50 {} p95 {} | search p50 {} p95 {}",
            rows as f64 / found.max(1) as f64,
            ms(percentile(&mut totals, 0.5)),
            ms(percentile(&mut totals, 0.95)),
            ms(percentile(&mut searches, 0.5)),
            ms(percentile(&mut searches, 0.95)),
        );
    }
    // Contraction hierarchy: built on the first `pgr:engine "ch"` query, then reused.
    let (_, first) = count(
        &engine,
        &route(
            "pgr_dijkstraCost",
            0,
            elements - 1,
            "pgr:agg_cost ?agg ; pgr:engine \"ch\"",
        ),
    );
    let s = engine.last_routing_stats();
    println!(
        "contraction hierarchy: first query {} (contraction {})",
        ms(first),
        ms(s.contraction)
    );
    for (func, out) in [
        ("pgr_dijkstraCost", "pgr:agg_cost ?agg"),
        (
            "pgr_dijkstra",
            "pgr:node ?node ; pgr:edge ?edge ; pgr:agg_cost ?agg",
        ),
    ] {
        let mut totals = Vec::new();
        let mut searches = Vec::new();
        let mut found = 0;
        for &(a, b) in &pairs {
            let plain = count(&engine, &route(func, a, b, out)).0;
            let (n, t) = count(
                &engine,
                &route(func, a, b, &format!("{out} ; pgr:engine \"ch\"")),
            );
            assert_eq!(
                n, plain,
                "same number of rows with and without the hierarchy"
            );
            totals.push(t);
            searches.push(engine.last_routing_stats().search);
            found += usize::from(n > 0);
        }
        println!(
            "{func} with pgr:engine \"ch\": {queries} random pairs, {found} routable | query p50 {} p95 {} | search p50 {} p95 {}",
            ms(percentile(&mut totals, 0.5)),
            ms(percentile(&mut totals, 0.95)),
            ms(percentile(&mut searches, 0.5)),
            ms(percentile(&mut searches, 0.95)),
        );
    }

    // Networks kept on disk: the first engine builds and saves, a restarted one loads.
    let tmp = tripletrail_testdir::tempdir("bench-networks");
    let dir = tmp.join("networks");
    let ch_query = route(
        "pgr_dijkstraCost",
        0,
        elements - 1,
        "pgr:agg_cost ?agg ; pgr:engine \"ch\"",
    );
    {
        let saving = Engine::with_network_dir(engine.store().clone(), &dir).unwrap();
        let (_, t) = count(&saving, &ch_query);
        println!("network directory: build, contract and save {}", ms(t));
    }
    let restarted = Engine::with_network_dir(engine.store().clone(), &dir).unwrap();
    let (_, t) = count(&restarted, &ch_query);
    assert!(restarted.last_routing_stats().cache_hit);
    let size: u64 = std::fs::read_dir(&dir)
        .unwrap()
        .flatten()
        .filter_map(|f| f.metadata().ok())
        .map(|m| m.len())
        .sum();
    println!(
        "network directory: first query after a restart {} ({:.0} MB on disk)",
        ms(t),
        size as f64 / 1e6
    );
    drop(tmp);

    let t = Instant::now();
    let (n, _) = count(
        &engine,
        &format!(
            r#"{profile_prefixes}
PREFIX pgr: <http://w3id.org/tripletrail/pgr#>
SELECT * WHERE {{ SERVICE <http://w3id.org/tripletrail/pgr> {{
  [] pgr:function pgr:pgr_drivingDistance ; pgr:start_vid "{BASE}ne/{}#fwd" ; pgr:distance 20000 ; pgr:node ?n ; pgr:agg_cost ?c .
  {{ {edges} }} }} }}"#,
            elements / 2
        ),
    );
    println!(
        "pgr_drivingDistance 20 km: {n} states reached in {}",
        ms(t.elapsed())
    );

    for (function, out) in [
        ("connectedComponents", "pgr:component ?c ; pgr:node ?n"),
        ("strongComponents", "pgr:component ?c ; pgr:node ?n"),
        ("articulationPoints", "pgr:node ?n"),
        ("bridges", "pgr:edge ?n"),
    ] {
        let (n, t) = count(
            &engine,
            &format!(
                r#"{profile_prefixes}
PREFIX pgr: <http://w3id.org/tripletrail/pgr#>
SELECT ?n WHERE {{ SERVICE <http://w3id.org/tripletrail/pgr> {{
  [] pgr:function pgr:pgr_{function} ; {out} .
  {{ {edges} }} }} }}"#
            ),
        );
        println!("pgr_{function}: {n} rows in {}", ms(t));
    }
    println!();

    // --- Spatial -----------------------------------------------------------------------
    println!("## Spatial\n");
    let geo_prefix = "PREFIX geo: <http://www.opengis.net/ont/geosparql#>\nPREFIX geof: <http://www.opengis.net/def/function/geosparql/>\nPREFIX st: <http://w3id.org/tripletrail/st#>\n";
    let t = Instant::now();
    let index = engine.spatial_index().expect("spatial index");
    println!(
        "R-tree over {} geometries: {} (built lazily on first spatial query after a write)",
        index.stats().geometries,
        ms(t.elapsed())
    );
    let point = "\"POINT(5.7 58.4)\"^^geo:wktLiteral";
    let filters = [
        (
            "sfIntersects, large polygon",
            "geof:sfIntersects(?w, \"POLYGON((5.5 58.2, 6.0 58.2, 6.0 58.6, 5.5 58.6, 5.5 58.2))\"^^geo:wktLiteral)".to_owned(),
        ),
        (
            "sfIntersects, small window",
            "geof:sfIntersects(?w, \"POLYGON((5.66 58.38, 5.74 58.38, 5.74 58.42, 5.66 58.42, 5.66 58.38))\"^^geo:wktLiteral)".to_owned(),
        ),
        ("geof:distance < 2 km", format!("geof:distance(?w, {point}) < 2000")),
        ("ST_DWithinSphere 3 km", format!("st:ST_DWithinSphere(?w, {point}, 3000)")),
    ];
    println!("\n| filter | hits | full scan | indexed |\n|---|---:|---:|---:|");
    for (name, f) in &filters {
        let q = format!("{geo_prefix}SELECT ?g WHERE {{ ?g geo:asWKT ?w FILTER({f}) }}");
        engine.set_spatial_rewrite(false);
        let (n_scan, scan) = count(&engine, &q);
        engine.set_spatial_rewrite(true);
        let mut runs: Vec<Duration> = (0..5).map(|_| count(&engine, &q).1).collect();
        let (n, _) = count(&engine, &q);
        assert_eq!(n, n_scan, "rewrite changed the result of {name}");
        println!(
            "| {name} | {n} | {} | {} |",
            ms(scan),
            ms(percentile(&mut runs, 0.5))
        );
    }
    println!();
    // Nearest neighbours: ORDER BY distance LIMIT k, the PostGIS `<->` query.
    println!("| nearest | rows | full sort | indexed |\n|---|---:|---:|---:|");
    for k in [1, 10, 100] {
        let q = format!(
            "{geo_prefix}SELECT ?g WHERE {{ ?g geo:asWKT ?w }} ORDER BY (geof:distance(?w, {point})) LIMIT {k}"
        );
        engine.set_spatial_rewrite(false);
        let (n_scan, scan) = count(&engine, &q);
        engine.set_spatial_rewrite(true);
        let mut runs: Vec<Duration> = (0..5).map(|_| count(&engine, &q).1).collect();
        let (n, _) = count(&engine, &q);
        assert_eq!(n, n_scan);
        assert!(
            engine.last_spatial_stats().filters > 0,
            "k = {k} was not indexed"
        );
        println!(
            "| {k} nearest geometries | {n} | {} | {} |",
            ms(scan),
            ms(percentile(&mut runs, 0.5))
        );
    }
    println!();
    // Joins between two variables: without the index these are nested loops over all pairs
    // (tens of billions of function calls here), so only the indexed time is measured.
    let window =
        "\"POLYGON((5.66 58.38, 5.74 58.38, 5.74 58.42, 5.66 58.42, 5.66 58.38))\"^^geo:wktLiteral";
    let joins = [
        (
            "elements in a window x elements they intersect (FILTER)",
            format!(
                "{geo_prefix}SELECT ?a ?b WHERE {{ ?a geo:hasGeometry/geo:asWKT ?w1 . ?b geo:hasGeometry/geo:asWKT ?w2 FILTER(?a != ?b && geof:sfIntersects(?w1, {window}) && geof:sfIntersects(?w1, ?w2)) }}"
            ),
        ),
        (
            "all pairs of intersecting elements (?a geo:sfIntersects ?b)",
            format!("{geo_prefix}SELECT ?a ?b WHERE {{ ?a geo:sfIntersects ?b FILTER(?a != ?b) }}"),
        ),
    ];
    println!("| join | rows | indexed | of which index lookups |\n|---|---:|---:|---:|");
    for (name, q) in &joins {
        let (n, t) = count(&engine, q);
        let s = engine.last_spatial_stats();
        assert!(s.joins == 1, "{name} was not answered through the index");
        println!("| {name} | {n} | {} | {} |", ms(t), ms(s.lookup));
    }
    println!();
    let (v, t) = first_value(
        &engine,
        &format!(
            "{geo_prefix}SELECT (SUM(geof:metricLength(?w)) AS ?m) WHERE {{ ?g geo:asWKT ?w }}"
        ),
    );
    println!(
        "SUM(geof:metricLength) over all geometries: {} m, {}",
        v.split('"').nth(1).unwrap_or(&v),
        ms(t)
    );
    let (n, t) = count(
        &engine,
        &format!(
            "{geo_prefix}SELECT ?g ?f WHERE {{ ?g geo:asWKT ?w BIND(st:ST_LineLocatePoint(?w, st:ST_Centroid(?w)) AS ?f) }}"
        ),
    );
    println!(
        "ST_LineLocatePoint(?w, ST_Centroid(?w)) for {n} lines: {}",
        ms(t)
    );
    println!();

    // --- Writes ------------------------------------------------------------------------
    // What the next routing and spatial queries cost after small updates. On the tripletrail
    // store, an update keeps the networks whose edge query reads none of the changed
    // predicates and patches the spatial index; on Oxigraph's store both are rebuilt.
    println!(
        "## After a small update ({} store)\n",
        engine.store().kind()
    );
    let probe_route = route("pgr_dijkstraCost", 0, elements - 1, "pgr:agg_cost ?agg");
    let probe_spatial = format!(
        "{geo_prefix}SELECT ?g WHERE {{ ?g geo:asWKT ?w FILTER(geof:sfIntersects(?w, \"POLYGON((5.66 58.38, 5.74 58.38, 5.74 58.42, 5.66 58.42, 5.66 58.38))\"^^geo:wktLiteral)) }}"
    );
    count(&engine, &probe_route);
    count(&engine, &probe_spatial);
    println!("| update | next route query | next spatial query |\n|---|---:|---:|");
    for (name, update) in [
        (
            "add a label to an element",
            format!("INSERT DATA {{ <{BASE}ne/0> <http://www.w3.org/2000/01/rdf-schema#label> \"first\" }}"),
        ),
        (
            "add a geometry",
            "INSERT DATA { <http://example.com/new> <http://www.opengis.net/ont/geosparql#asWKT> \"POINT(5.7 58.4)\"^^<http://www.opengis.net/ont/geosparql#wktLiteral> }".to_owned(),
        ),
        (
            "change an element's length",
            format!("DELETE {{ <{BASE}ne/1> <{ERA}lengthOfNetLinearElement> ?l }} INSERT {{ <{BASE}ne/1> <{ERA}lengthOfNetLinearElement> 501 }} WHERE {{ <{BASE}ne/1> <{ERA}lengthOfNetLinearElement> ?l }}"),
        ),
    ] {
        engine.update(&update).unwrap();
        let (_, r) = count(&engine, &probe_route);
        let hit = engine.last_routing_stats().cache_hit;
        let (_, sp) = count(&engine, &probe_spatial);
        println!(
            "| {name} | {}{} | {} |",
            ms(r),
            if hit { "" } else { " (network rebuilt)" },
            ms(sp)
        );
    }
    if let Some(mb) = peak_rss_mb() {
        println!("\npeak RSS: {mb:.0} MB");
    }
}
