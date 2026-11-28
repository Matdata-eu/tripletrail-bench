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

## rinf-0080 (11,830,200 triples with the ontology and code lists)

### core

| engine | time (s) | validation (s) | peak memory (MB) | results | violations | warnings | same as TopBraid | same as majority |
|---|---:|---:|---:|---:|---:|---:|---|---|
| tripletrail | 32.4 | 27.3 | 1,745 | 281,387 | 96 | 281,291 | yes | yes |
| jena | 73.2 |  | 12,843 | 281,387 | 96 | 281,291 | yes | yes |
| topbraid | 255.8 |  | 14,181 | 281,387 | 96 | 281,291 | yes | yes |
| graphdb | 374.5 | 246.2 | 52,694 | 281,387 | 96 | 281,291 | yes | yes |
| rdf4j | 556.9 | 553.5 | 20,978 | 2,100 | 96 | 2,004 | no | no |
| pyshacl | 2,668.2 |  | 15,230 | 281,387 | 96 | 281,291 | yes | yes |

### era-local

| engine | time (s) | validation (s) | peak memory (MB) | results | violations | warnings | same as TopBraid | same as majority |
|---|---:|---:|---:|---:|---:|---:|---|---|
| tripletrail | 179.5 | 174.0 | 11,966 | 894,300 | 297,578 | 596,722 | yes | yes |
| jena | 778.8 |  | 12,415 | 947,629 (894,300 distinct) | 297,578 | 650,051 | yes | yes |
| topbraid | 1,253.0 |  | 11,961 | 947,629 (894,300 distinct) | 297,578 | 650,051 | yes | yes |
| graphdb | 3,199.0 (graphdb: container peak memory 53157052416 bytes) | | 50,695 | | | | | |
| rdf4j | skipped: failed on rinf-0076 | | | | | | | |
| pyshacl | skipped: failed on rinf-0076 | | | | | | | |

### era

| engine | time (s) | validation (s) | peak memory (MB) | results | violations | warnings | same as TopBraid | same as majority |
|---|---:|---:|---:|---:|---:|---:|---|---|
| tripletrail | 203.8 | 198.4 | 12,625 | 894,300 | 297,578 | 596,722 | yes | yes |
| jena | 800.9 |  | 12,355 | 947,629 (894,300 distinct) | 297,578 | 650,051 | yes | yes |
| topbraid | 1,343.7 |  | 11,913 | 947,629 (894,300 distinct) | 297,578 | 650,051 | yes | yes |
| graphdb | 3,136.0 (graphdb: container peak memory 54429499392 bytes) | | 51,908 | | | | | |
| rdf4j | skipped: failed on rinf-0076 | | | | | | | |
| pyshacl | skipped: failed on rinf-0076 | | | | | | | |

## rinf-all (43,003,520 triples with the ontology and code lists)

### core

| engine | time (s) | validation (s) | peak memory (MB) | results | violations | warnings | same as TopBraid | same as majority |
|---|---:|---:|---:|---:|---:|---:|---|---|
| tripletrail | 125.0 | 102.9 | 4,786 | 923,615 (919,987 distinct) | 131,086 | 792,529 |  | yes |
| jena | 357.4 |  | 24,662 | 923,615 (919,987 distinct) | 131,086 | 792,529 |  | yes |
| topbraid | 977.5 (exit 1) | | 28,745 | | | | | |
| graphdb | skipped: left out of this dataset by the benchmark profile (bench/v2/profiles/shacl.txt) | | | | | | | |
| rdf4j | 2,459.8 | 2,454.3 | 50,310 | 15,058 (14,655 distinct) | 11,179 | 3,879 |  | no |
| pyshacl | 3,603.8 (timed out) | | 41,767 | | | | | |

### era-local

| engine | time (s) | validation (s) | peak memory (MB) | results | violations | warnings | same as TopBraid | same as majority |
|---|---:|---:|---:|---:|---:|---:|---|---|
| tripletrail | 601.4 | 578.6 | 36,112 | 3,626,416 (3,579,628 distinct) | 265,853 | 3,360,563 |  |  |
| jena | 2,661.2 |  | 32,444 | 3,804,723 (3,579,560 distinct) | 266,245 | 3,538,478 |  |  |
| topbraid | 3,600.2 (timed out) | | 101 | | | | | |
| graphdb | skipped: left out of this dataset by the benchmark profile (bench/v2/profiles/shacl.txt) | | | | | | | |
| rdf4j | skipped: failed on rinf-0076 | | | | | | | |
| pyshacl | skipped: timed out on an earlier profile of this dataset | | | | | | | |

- tripletrail against jena: 68 keys only in tripletrail, 0 only in jena. SPARQLConstraintComponent on http://www.opengis.net/ont/geosparql#asWKT (Violation): 59 only here, 0 only in jena; SPARQLConstraintComponent on http://www.w3.org/2000/01/rdf-schema#label (Violation): 8 only here, 0 only in jena; SPARQLConstraintComponent on http://data.europa.eu/949/typeOfTraffic (Violation): 1 only here, 0 only in jena.

### era

| engine | time (s) | validation (s) | peak memory (MB) | results | violations | warnings | same as TopBraid | same as majority |
|---|---:|---:|---:|---:|---:|---:|---|---|
| tripletrail | 662.0 | 639.4 | 36,122 | 3,626,762 (3,579,669 distinct) | 266,199 | 3,360,563 |  |  |
| jena | 2,777.6 |  | 35,978 | 3,805,069 (3,579,601 distinct) | 266,591 | 3,538,478 |  |  |
| topbraid | skipped: timed out on an earlier profile of this dataset | | | | | | | |
| graphdb | skipped: left out of this dataset by the benchmark profile (bench/v2/profiles/shacl.txt) | | | | | | | |
| rdf4j | skipped: failed on rinf-0076 | | | | | | | |
| pyshacl | skipped: timed out on an earlier profile of this dataset | | | | | | | |

- tripletrail against jena: 68 keys only in tripletrail, 0 only in jena. SPARQLConstraintComponent on http://www.opengis.net/ont/geosparql#asWKT (Violation): 59 only here, 0 only in jena; SPARQLConstraintComponent on http://www.w3.org/2000/01/rdf-schema#label (Violation): 8 only here, 0 only in jena; SPARQLConstraintComponent on http://data.europa.eu/949/typeOfTraffic (Violation): 1 only here, 0 only in jena.
