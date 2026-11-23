# SHACL suite, phase 0

Data: RINF graph 0076 (Norway) from ERA's rinf-plus endpoint, 1,594,395 triples, plus the ERA ontology and 425 SKOS code lists (106,150 triples): 1,700,545 triples in one N-Triples file. Shapes: ERA-RINF-shapes.ttl at era-ontology commit 8177357 (SHA-256 e0038a08…), 7,640 triples: 76 node shapes, 393 property shapes, 211 SPARQL constraints used 336 times, 7 SPARQL targets, no rules. Machine: cloud session container, 4 cores, 15 GB memory; engines run one at a time.

## Feature support

Each cell is a probe in `bench/v2/suites/shacl/features/` on `data.ttl`: yes when the engine gives the expected number of results (or inferred triples), no otherwise. AF rules run with the engine's own inference command; n/a means it has none.

| engine | version | Core | SPARQL constraints | SPARQL targets | SPARQL functions | SPARQL components | AF rules |
|---|---|---|---|---|---|---|---|
| tripletrail | tripletrail 0.1.0 | yes | yes | yes | yes | yes | yes |
| jena | apache-jena-6.2.0 | yes | yes | yes | no (wrong count) | yes | n/a |
| topbraid | shacl-1.5.0 | yes | yes | yes | yes | yes | yes |
| pyshacl | pyshacl 0.30.1 | yes | yes | yes | yes | yes | yes |
| rdf4j | rdf4j 5.3.2 | yes | yes | no (error) | no (wrong count) | no (wrong count) | n/a |
| graphdb | graphdb:10.8.0 | yes | yes | no (error) | no (error) | no (wrong count) | n/a |

## ERA RINF shapes on the data

Same results: the engine's sorted result keys (focus node, path, constraint component, severity) hash to the same SHA-256 as Jena's.

| engine | ran | time (s) | peak memory (MB) | results | violations | warnings | same results as Jena |
|---|---|---:|---:|---:|---:|---:|---|
| tripletrail | yes | 12.4 | 1,650 | 31,783 | 28,884 | 2,899 | yes |
| jena | yes | 66.7 | 1,518 | 31,783 | 28,884 | 2,899 | yes |
| topbraid | yes | 75.9 | 1,682 | 31,783 | 28,884 | 2,899 | yes |
| pyshacl | no (exit 1) | 3393.2 | 2,863 |  |  |  |  |
| rdf4j | no (exit 2) | 1.2 | 180 |  |  |  |  |
| graphdb | yes | 269.5 | 10,681 | 31,783 | 28,884 | 2,899 | yes |

## Notes

- **One machine, one run each.** The timings come from a 4-core cloud container, so they show how
  the engines compare, not what a server would do. The full suite (#30) runs on a ccx43.
- **TripleTrail, Jena, TopBraid and GraphDB give the same 31,783 results** (28,884 violations,
  2,899 warnings, from 9 shapes): their result keys hash the same.
- **GraphDB** validates when the shapes are added to a repository that already holds the data. Its
  time includes loading the data over HTTP (31 s); validation itself took 221 s. Its memory is
  the container's peak (cgroup v1 `max_usage_in_bytes`, page cache included), with an 8 GB heap.
- **RDF4J 5.3.2** refuses the shapes: `$PATH` in a SPARQL constraint of a property shape is not
  allowed there (`LangStringEnRequired`), so nothing is validated. GraphDB 10.8, which also builds
  on RDF4J's ShaclSail, accepts them.
- **pySHACL 0.30.1** stopped after 3,393 s with a SPARQL parse error in one of the constraints
  (`Expected SelectQuery, found 'rdfs'`), so it gave no report.
- **maplib**'s open build (0.24.0) has no SHACL: `Model.validate` stops with "not implemented:
  Contact Data Treehouse to try". It is not in the tables.
- **Feature probes**: Jena gives no result for a `sh:SPARQLFunction` called in a constraint;
  RDF4J and GraphDB refuse SPARQL targets and do not run SPARQL-based constraint components.
  RDF4J gives no result for the SPARQL function, and GraphDB refuses it. Jena's, RDF4J's and
  GraphDB's command-line paths have no SHACL-AF rules.
