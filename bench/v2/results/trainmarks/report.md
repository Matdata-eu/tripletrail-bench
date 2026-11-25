# Trainmarks-style results

Synthetic e-commerce data and queries from Trainmarks (seed 42), run over HTTP against each engine's SPARQL endpoint. Load = bulk load of the N-Triples file into the engine's store (s). Query times in ms: median of the warm runs (cold run in brackets); q6 is the DELETE/INSERT update, run once. Row counts that differ between engines are flagged. Geometric mean: of the warm medians of the five read queries q1-q5 (not the update), over the queries the engine answered; fewer than 5 is marked. maplib keeps its data in memory only: its load is reading the file into RAM, behind a small HTTP wrapper (engines/maplib_server.py).

## medium (98,000 triples)

| | tripletrail | oxigraph | qlever | jena | graphdb | maplib | rows |
|---|---:|---:|---:|---:|---:|---:|---|
| load (s) | 0.556 | 0.829 | 0.917 | 2.043 | 7.06 | 0.038 | |
| q1_count | 1.1 (2.6) | 27.1 (64.3) | 2.0 (4.5) | 69.5 (259) | 43.3 (298) | 1.4 (5.9) | 1 |
| q2_customer_orders | 3.3 (4.8) | 83.7 (86.2) | 10.1 (14.4) | 73.1 (516) | 56.8 (239) | 4.3 (7.0) | 20 |
| q3_join_3_entities | 1.7 (2.0) | 19.1 (19.7) | 22.1 (23.7) | 20.2 (26.1) | 22.6 (74.2) | 6.8 (6.9) | 50 |
| q4_optional_aggregation | 3.2 (3.3) | 61.1 (63.2) | 13.9 (15.1) | 78.1 (141) | 83.5 (91.3) | 6.4 (6.4) | 50 |
| q5_construct | 6.5 (7.5) | 31.8 (33.8) | 22.5 (23.0) | 36.5 (91.0) | 61.3 (107) | 23.4 (122) | 3878 |
| q6_delete_insert | 4.6 | 5.5 | 10.7 | 86.8 | 195 | 8.5 |  |
| geometric mean q1-q5 | 2.7 | 38.5 | 10.6 | 49.4 | 49.0 | 5.7 | |

## large (1,001,000 triples)

| | tripletrail | oxigraph | qlever | jena | graphdb | maplib | rows |
|---|---:|---:|---:|---:|---:|---:|---|
| load (s) | 0.563 | 1.664 | 1.257 | 4.887 | 13.21 | 0.273 | |
| q1_count | 1.2 (2.5) | 283 (366) | 2.1 (4.2) | 442 (561) | 235 (439) | 1.5 (5.8) | 1 |
| q2_customer_orders | 12.0 (15.0) | 1,039 (1,032) | 29.1 (38.6) | 774 (3,266) | 697 (650) | 7.6 (10.3) | 20 |
| q3_join_3_entities | 8.5 (8.6) | 222 (226) | 26.9 (29.9) | 115 (151) | 127 (197) | 12.7 (12.7) | 50 |
| q4_optional_aggregation | 13.7 (14.7) | 840 (863) | 38.3 (41.9) | 776 (962) | 713 (795) | 11.3 (11.5) | 50 |
| q5_construct | 76.5 (78.5) | 405 (449) | 118 (136) | 204 (312) | 400 (491) | 44.6 (157) | 43091 |
| q6_delete_insert | 25.7 | 32.6 | 11.7 | 197 | 478 | 11.0 |  |
| geometric mean q1-q5 | 10.6 | 467 | 23.7 | 362 | 359 | 9.4 | |

## xlarge (9,995,000 triples)

| | tripletrail | oxigraph | qlever | jena | graphdb | maplib | rows |
|---|---:|---:|---:|---:|---:|---:|---|
| load (s) | 3.776 | 13.136 | 9.13 | 26.275 | 49.332 | 2.8 | |
| q1_count | 1.0 (2.5) | 2,852 (3,302) | 2.5 (4.4) | 1,445 (3,690) | 1,724 (2,166) | 1.5 (4.7) | 1 |
| q2_customer_orders | 82.9 (91.0) | 13,681 (13,695) | 229 (254) | 13,416 (25,605) | 5,226 (5,504) | 19.3 (24.0) | 20 |
| q3_join_3_entities | 31.7 (30.8) | 3,245 (3,294) | 109 (116) | 1,309 (1,329) | 968 (1,033) | 37.3 (38.9) | 50 |
| q4_optional_aggregation | 112 (117) | 11,571 (11,875) | 393 (407) | 15,618 (18,453) | 6,361 (6,311) | 32.4 (33.7) | 50 |
| q5_construct | 953 (918) | 5,563 (5,554) | 1,500 (2,830) | 1,874 (2,964) | 4,074 (4,205) | 247 (366) | 439240 |
| q6_delete_insert | 107 | 366 | 32.4 | 618 | 1,060 | 16.0 |  |
| geometric mean q1-q5 | 49.3 | 6,057 | 130 | 3,751 | 2,957 | 24.2 | |
