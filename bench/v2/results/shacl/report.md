# SHACL validation suite

The ERA RINF shapes on RINF data, in three profiles (`suites/shacl/run_shacl.py`): `core` is SHACL Core only, `era-local` leaves out the shapes ERA marks as global, `era` is the shapes as published. Time is the whole command (median of 3 runs when under 300 s), validation is the engine's own validation time where it logs one. Same results compares the sorted result keys (focus node, path, constraint component, severity) with TopBraid's and with the majority's.

## rinf-0076 (1,700,545 triples with the ontology and code lists)

### core

| engine | time (s) | validation (s) | peak memory (MB) | results | violations | warnings | same as TopBraid | same as majority |
|---|---:|---:|---:|---:|---:|---:|---|---|
| tripletrail | 3.6 | 2.4 | 1,082 | 1,701 | 4 | 1,697 | yes | yes |
| jena | 24.2 |  | 5,537 | 1,701 | 4 | 1,697 | yes | yes |
| topbraid | 32.6 |  | 7,080 | 1,701 | 4 | 1,697 | yes | yes |
| graphdb | 75.5 | 37.6 | 32,560 | 1,701 | 4 | 1,697 | yes | yes |
| rdf4j | 3,368.4 | 3,366.2 | 10,800 | 1,019 | 4 | 1,015 | no | no |
| pyshacl | 220.4 |  | 2,301 | 1,701 | 4 | 1,697 | yes | yes |

### era-local

| engine | time (s) | validation (s) | peak memory (MB) | results | violations | warnings | same as TopBraid | same as majority |
|---|---:|---:|---:|---:|---:|---:|---|---|
| tripletrail | 9.4 | 8.2 | 1,839 | 31,783 | 28,884 | 2,899 | yes | yes |
| jena | 49.0 |  | 4,186 | 31,783 | 28,884 | 2,899 | yes | yes |
| topbraid | 55.5 |  | 6,561 | 31,783 | 28,884 | 2,899 | yes | yes |
| graphdb | 231.2 | 190.6 | 44,452 | 31,783 | 28,884 | 2,899 | yes | yes |
| rdf4j | 1.2 (	... 16 more) | | 245 | | | | | |
| pyshacl | 57.7 (pyparsing.exceptions.ParseException: Expected SelectQuery, found 'era'  (at char 627), (line:16, col:18)) | | 2,531 | | | | | |

### era

| engine | time (s) | validation (s) | peak memory (MB) | results | violations | warnings | same as TopBraid | same as majority |
|---|---:|---:|---:|---:|---:|---:|---|---|
| tripletrail | 9.6 | 8.3 | 1,828 | 31,783 | 28,884 | 2,899 | yes | yes |
| jena | 49.1 |  | 5,095 | 31,783 | 28,884 | 2,899 | yes | yes |
| topbraid | 57.0 |  | 6,397 | 31,783 | 28,884 | 2,899 | yes | yes |
| graphdb | 231.8 | 191.4 | 44,469 | 31,783 | 28,884 | 2,899 | yes | yes |
| rdf4j | 1.2 (	... 16 more) | | 301 | | | | | |
| pyshacl | 1,059.1 (Exception: Unknown namespace prefix : geo) | | 2,854 | | | | | |

## rinf-0080 (11,830,200 triples with the ontology and code lists)

### core

| engine | time (s) | validation (s) | peak memory (MB) | results | violations | warnings | same as TopBraid | same as majority |
|---|---:|---:|---:|---:|---:|---:|---|---|
| tripletrail | 35.8 | 30.3 | 1,626 | 281,387 | 96 | 281,291 | yes | yes |
| jena | 75.1 |  | 14,293 | 281,387 | 96 | 281,291 | yes | yes |
| topbraid | 243.0 |  | 15,733 | 281,387 | 96 | 281,291 | yes | yes |
| graphdb | 13.8 (graphdb: loading the data failed) | | 1,034 | | | | | |
| rdf4j | 469.5 | 466.6 | 22,493 | 2,100 | 96 | 2,004 | no | no |
| pyshacl | 2,994.1 |  | 15,219 | 281,387 | 96 | 281,291 | yes | yes |

### era-local

| engine | time (s) | validation (s) | peak memory (MB) | results | violations | warnings | same as TopBraid | same as majority |
|---|---:|---:|---:|---:|---:|---:|---|---|
| tripletrail | 185.8 | 180.3 | 11,957 | 894,300 | 297,578 | 596,722 | yes | yes |
| jena | 885.9 |  | 13,500 | 947,629 | 297,578 | 650,051 | yes | yes |
| topbraid | 1,176.1 |  | 13,434 | 947,629 | 297,578 | 650,051 | yes | yes |
| graphdb | 13.8 (graphdb: loading the data failed) | | 1,034 | | | | | |
| rdf4j | skipped: failed on rinf-0076 | | | | | | | |
| pyshacl | skipped: failed on rinf-0076 | | | | | | | |

### era

| engine | time (s) | validation (s) | peak memory (MB) | results | violations | warnings | same as TopBraid | same as majority |
|---|---:|---:|---:|---:|---:|---:|---|---|
| tripletrail | 218.2 | 212.7 | 12,616 | 894,300 | 297,578 | 596,722 | yes | yes |
| jena | 922.0 |  | 13,531 | 947,629 | 297,578 | 650,051 | yes | yes |
| topbraid | 1,322.7 |  | 15,278 | 947,629 | 297,578 | 650,051 | yes | yes |
| graphdb | 14.0 (graphdb: loading the data failed) | | 1,034 | | | | | |
| rdf4j | skipped: failed on rinf-0076 | | | | | | | |
| pyshacl | skipped: failed on rinf-0076 | | | | | | | |

## rinf-all (42,712,515 triples with the ontology and code lists)

### core

| engine | time (s) | validation (s) | peak memory (MB) | results | violations | warnings | same as TopBraid | same as majority |
|---|---:|---:|---:|---:|---:|---:|---|---|
| tripletrail | 122.2 | 100.4 | 4,749 | 850,873 | 58,344 | 792,529 |  |  |
| jena | 266.9 (	at java.base/java.util.regex.Pattern$Branch.match(Pattern.java:4914)) | | 22,266 | | | | | |
| topbraid | 601.4 (	at java.base/java.util.regex.Pattern$GroupTail.match(Pattern.java:5000)) | | 24,156 | | | | | |
| graphdb | skipped: failed on rinf-0080 | | | | | | | |
| rdf4j | 2,313.1 (	at java.base/java.util.regex.Pattern$BmpCharProperty.match(Pattern.java:4134)) | | 50,106 | | | | | |
| pyshacl | 3,602.8 (timed out) | | 41,382 | | | | | |

### era-local

| engine | time (s) | validation (s) | peak memory (MB) | results | violations | warnings | same as TopBraid | same as majority |
|---|---:|---:|---:|---:|---:|---:|---|---|
| tripletrail | 585.0 | 563.3 | 35,949 | 3,552,367 | 193,111 | 3,359,256 |  |  |
| jena | 1,474.1 (	at java.base/java.util.regex.Pattern$Curly.match0(Pattern.java:4582)) | | 23,746 | | | | | |
| topbraid | 2,477.0 (	at java.base/java.util.regex.Pattern$Curly.match(Pattern.java:4544)) | | 34,784 | | | | | |
| graphdb | skipped: failed on rinf-0080 | | | | | | | |
| rdf4j | skipped: failed on rinf-0076 | | | | | | | |
| pyshacl | skipped: timed out on an earlier profile of this dataset | | | | | | | |

### era

| engine | time (s) | validation (s) | peak memory (MB) | results | violations | warnings | same as TopBraid | same as majority |
|---|---:|---:|---:|---:|---:|---:|---|---|
| tripletrail | 645.3 | 623.6 | 35,953 | 3,552,713 | 193,457 | 3,359,256 |  |  |
| jena | 1,657.4 (	at java.base/java.util.regex.Pattern$BmpCharProperty.match(Pattern.java:4134)) | | 27,627 | | | | | |
| topbraid | 2,756.6 (	at java.base/java.util.regex.Pattern$GroupHead.match(Pattern.java:4969)) | | 26,052 | | | | | |
| graphdb | skipped: failed on rinf-0080 | | | | | | | |
| rdf4j | skipped: failed on rinf-0076 | | | | | | | |
| pyshacl | skipped: timed out on an earlier profile of this dataset | | | | | | | |
