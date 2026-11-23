# Trainmarks-style results

Synthetic e-commerce data and queries from Trainmarks (seed 42), run over HTTP against each engine's SPARQL endpoint. Load = bulk load of the N-Triples file into the engine's store (s). Query times in ms: median of the warm runs (cold run in brackets); q6 is the DELETE/INSERT update, run once. Row counts that differ between engines are flagged. Geometric mean: of the warm medians of the five read queries q1-q5 (not the update), over the queries the engine answered; fewer than 5 is marked. maplib keeps its data in memory only: its load is reading the file into RAM, behind a small HTTP wrapper (engines/maplib_server.py).

## medium (98,000 triples)

| | tripletrail | oxigraph | qlever | jena | graphdb | maplib | rows |
|---|---:|---:|---:|---:|---:|---:|---|
| load (s) | 0.613 | 0.829 | 1.027 | 2.043 | 7.06 | 0.109 | |
| q1_count | 2.5 (4.8) | 27.1 (64.3) | 5.6 (10.0) | 69.5 (259) | 43.3 (298) | 3.7 (9.2) | 1 |
| q2_customer_orders | 9.5 (12.3) | 83.7 (86.2) | 27.0 (40.8) | 73.1 (516) | 56.8 (239) | 12.8 (18.7) | 20 |
| q3_join_3_entities | 5.2 (5.7) | 19.1 (19.7) | 30.3 (39.8) | 20.2 (26.1) | 22.6 (74.2) | 19.9 (19.7) | 50 |
| q4_optional_aggregation | 7.8 (9.0) | 61.1 (63.2) | 20.0 (21.5) | 78.1 (141) | 83.5 (91.3) | 17.7 (17.6) | 50 |
| q5_construct | 17.2 (8.4) | 31.8 (33.8) | 31.9 (33.6) | 36.5 (91.0) | 61.3 (107) | 73.9 (187) | 3878 |
| q6_delete_insert | 12.4 | 5.5 | 28.8 | 86.8 | 195 | 22.4 |  |
| geometric mean q1-q5 | 7.0 | 38.5 | 19.6 | 49.4 | 49.0 | 16.5 | |

## large (1,001,000 triples)

| | tripletrail | oxigraph | qlever | jena | graphdb | maplib | rows |
|---|---:|---:|---:|---:|---:|---:|---|
| load (s) | 1.144 | 1.664 | 1.942 | 4.887 | 13.21 | 0.353 | |
| q1_count | 2.8 (4.9) | 283 (366) | 5.4 (10.0) | 442 (561) | 235 (439) | 3.8 (8.1) | 1 |
| q2_customer_orders | 33.8 (36.3) | 1,039 (1,032) | 74.6 (97.6) | 774 (3,266) | 697 (650) | 18.6 (23.8) | 20 |
| q3_join_3_entities | 23.8 (25.3) | 222 (226) | 75.1 (79.3) | 115 (151) | 127 (197) | 33.2 (33.6) | 50 |
| q4_optional_aggregation | 44.4 (41.9) | 840 (863) | 70.4 (82.7) | 776 (962) | 713 (795) | 27.7 (27.6) | 50 |
| q5_construct | 113 (113) | 405 (449) | 154 (272) | 204 (312) | 400 (491) | 104 (254) | 43091 |
| q6_delete_insert | 47.8 | 32.6 | 26.0 | 197 | 478 | 19.1 |  |
| geometric mean q1-q5 | 25.8 | 467 | 50.4 | 362 | 359 | 23.2 | |

## xlarge (9,995,000 triples)

| | tripletrail | oxigraph | qlever | jena | graphdb | maplib | rows |
|---|---:|---:|---:|---:|---:|---:|---|
| load (s) | 3.765 | 13.136 | 10.233 | 26.275 | 49.332 | 3.098 | |
| q1_count | 2.6 (5.0) | 2,852 (3,302) | 6.8 (10.1) | 1,445 (3,690) | 1,724 (2,166) | 3.4 (8.4) | 1 |
| q2_customer_orders | 120 (153) | 13,681 (13,695) | 408 (442) | 13,416 (25,605) | 5,226 (5,504) | 37.7 (58.2) | 20 |
| q3_join_3_entities | 87.3 (63.0) | 3,245 (3,294) | 259 (273) | 1,309 (1,329) | 968 (1,033) | 48.0 (65.1) | 50 |
| q4_optional_aggregation | 175 (173) | 11,571 (11,875) | 566 (619) | 15,618 (18,453) | 6,361 (6,311) | 36.7 (37.9) | 50 |
| q5_construct | 1,067 (1,038) | 5,563 (5,554) | 1,731 (2,901) | 1,874 (2,964) | 4,074 (4,205) | 441 (500) | 439240 |
| q6_delete_insert | 176 | 366 | 62.4 | 618 | 1,060 | 37.4 |  |
| geometric mean q1-q5 | 87.6 | 6,057 | 234 | 3,751 | 2,957 | 39.7 | |
