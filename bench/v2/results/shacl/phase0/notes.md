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
