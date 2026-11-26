# SHACL validation suite

The ERA RINF shapes on RINF data, in three profiles (`suites/shacl/run_shacl.py`): `core` is SHACL Core only, `era-local` leaves out the shapes ERA marks as global, `era` is the shapes as published. Time is the whole command (median of 3 runs when under 300 s), validation is the engine's own validation time where it logs one. Same results compares the sorted result keys (focus node, path, constraint component, severity) with TopBraid's and with the majority's; results shows the distinct keys too when an engine gives several results with one key.

## rinf-0076 (1,700,545 triples with the ontology and code lists)

### core

| engine | time (s) | validation (s) | peak memory (MB) | results | violations | warnings | same as TopBraid | same as majority |
|---|---:|---:|---:|---:|---:|---:|---|---|
| tripletrail | 3.6 | 2.3 | 1,088 | 1,701 | 4 | 1,697 | yes | yes |
| jena | 24.2 |  | 5,704 | 1,701 | 4 | 1,697 | yes | yes |
| topbraid | 32.2 |  | 6,486 | 1,701 | 4 | 1,697 | yes | yes |
| graphdb | 70.7 | 24.3 | 32,495 | 1,701 | 4 | 1,697 | yes | yes |
| rdf4j | 3,109.2 | 3,106.8 | 12,690 | 1,019 | 4 | 1,015 | no | no |
| pyshacl | 216.6 |  | 2,301 | 1,701 | 4 | 1,697 | yes | yes |

### era-local

| engine | time (s) | validation (s) | peak memory (MB) | results | violations | warnings | same as TopBraid | same as majority |
|---|---:|---:|---:|---:|---:|---:|---|---|
| tripletrail | 9.2 | 8.0 | 1,841 | 31,783 (31,180 distinct) | 28,884 | 2,899 | yes | yes |
| jena | 47.8 |  | 4,232 | 31,783 (31,180 distinct) | 28,884 | 2,899 | yes | yes |
| topbraid | 55.2 |  | 7,090 | 31,783 (31,180 distinct) | 28,884 | 2,899 | yes | yes |
| graphdb | 222.2 | 182.9 | 44,369 | 31,783 (31,180 distinct) | 28,884 | 2,899 | yes | yes |
| rdf4j | 1.2 (org.eclipse.rdf4j.repository.RepositoryException) | | 251 | | | | | |
| pyshacl | 201.1 (pyparsing.exceptions.ParseException) | | 2,434 | | | | | |

### era

| engine | time (s) | validation (s) | peak memory (MB) | results | violations | warnings | same as TopBraid | same as majority |
|---|---:|---:|---:|---:|---:|---:|---|---|
| tripletrail | 9.4 | 8.1 | 1,856 | 31,783 (31,180 distinct) | 28,884 | 2,899 | yes | yes |
| jena | 48.0 |  | 4,190 | 31,783 (31,180 distinct) | 28,884 | 2,899 | yes | yes |
| topbraid | 55.1 |  | 5,664 | 31,783 (31,180 distinct) | 28,884 | 2,899 | yes | yes |
| graphdb | 225.6 | 184.8 | 44,828 | 31,783 (31,180 distinct) | 28,884 | 2,899 | yes | yes |
| rdf4j | 1.2 (org.eclipse.rdf4j.repository.RepositoryException) | | 286 | | | | | |
| pyshacl | 71.9 (pyparsing.exceptions.ParseException) | | 2,719 | | | | | |

### injected violations

2,606 violations injected (seed 31, 1% of 312,342 focus nodes drawn: datatype 1,093, missing 727, code-list 418, pattern 3, duplicate 365; `suites/shacl/inject.py`), validated with the era-local profile before and after. Recall is the share of injected violations reported; precision the share of new results on one of the 44,925 nodes the mutations touched (the mutated nodes, the objects of removed triples and up to three hops upstream).

| engine | recall | precision | found | new results | missed (by component) |
|---|---:|---:|---:|---:|---|
| tripletrail | 100.0% | 100.0% | 2,606 of 2,606 | 3,309 | none |
| jena | 100.0% | 100.0% | 2,606 of 2,606 | 3,309 | none |
| topbraid | 100.0% | 100.0% | 2,606 of 2,606 | 3,309 | none |
| graphdb | 100.0% | 100.0% | 2,606 of 2,606 | 3,309 | none |
| rdf4j | no era-local result on rinf-0076 | | | | |
| pyshacl | no era-local result on rinf-0076 | | | | |
