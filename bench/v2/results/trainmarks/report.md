# Trainmarks-style results

Synthetic e-commerce data and queries from Trainmarks (seed 42), run over HTTP against each engine's SPARQL endpoint. Load = bulk load of the N-Triples file into the engine's store (s). Query times in ms: median of the warm runs (cold run in brackets); q6 is the DELETE/INSERT update, run once. Row counts that differ between engines are flagged. Geometric mean: of the warm medians of the five read queries q1-q5 (not the update), over the queries the engine answered; fewer than 5 is marked. maplib keeps its data in memory only: its load is reading the file into RAM, behind a small HTTP wrapper (engines/maplib_server.py).

## medium (98,000 triples)

| | tripletrail | oxigraph | qlever | jena | graphdb | maplib | rows |
|---|---:|---:|---:|---:|---:|---:|---|
| load (s) | 0.589 | 0.789 | 0.987 | 1.983 | 6.84 | 0.241 | |
| q1_count | 2.5 (4.5) | 26.0 (63.8) | 9.1 (12.4) | 69.9 (208) | 25.0 (269) | 22.6 (26.2) | 1 |
| q2_customer_orders | 45.1 (47.6) | 83.0 (81.4) | 31.0 (40.8) | 93.7 (494) | 55.6 (243) | 10.6 (12.6) | 20 |
| q3_join_3_entities | 12.0 (13.0) | 18.0 (19.1) | 34.9 (65.0) | 26.2 (34.7) | 16.2 (53.3) | 14.9 (15.5) | 50 |
| q4_optional_aggregation | 39.1 (39.6) | 59.0 (59.4) | 42.7 (43.7) | 81.5 (163) | 65.2 (112) | 10.4 (13.0) | 50 |
| q5_construct | 17.5 (17.9) | 30.8 (35.1) | 60.3 (62.5) | 31.8 (86.7) | 58.2 (110) | 31.7 (35.7) | 3878 |
| q6_delete_insert | 12.3 | 5.3 | 27.5 | 88.0 | 232 | 8.4 |  |
| geometric mean q1-q5 | 15.5 | 37.1 | 30.3 | 53.7 | 38.6 | 16.4 | |

## large (1,001,000 triples)

| | tripletrail | oxigraph | qlever | jena | graphdb | maplib | rows |
|---|---:|---:|---:|---:|---:|---:|---|
| load (s) | 1.149 | 1.41 | 1.848 | 4.452 | 12.434 | 1.37 | |
| q1_count | 2.4 (4.4) | 282 (349) | 11.0 (19.2) | 438 (555) | 213 (437) | 70.6 (124) | 1 |
| q2_customer_orders | 190 (240) | 1,035 (1,038) | 74.5 (103) | 748 (3,201) | 476 (673) | 17.9 (18.9) | 20 |
| q3_join_3_entities | 67.3 (73.8) | 224 (229) | 70.1 (72.7) | 112 (131) | 88.2 (164) | 24.7 (30.8) | 50 |
| q4_optional_aggregation | 187 (193) | 807 (806) | 97.0 (109) | 744 (928) | 690 (673) | 17.3 (18.7) | 50 |
| q5_construct | 112 (111) | 426 (414) | 301 (307) | 150 (311) | 362 (509) | 115 (91.8) | 43091 |
| q6_delete_insert | 63.0 | 59.7 | 23.6 | 187 | 419 | 21.1 |  |
| geometric mean q1-q5 | 57.8 | 468 | 70.0 | 333 | 295 | 36.2 | |

## xlarge (9,995,000 triples)

| | tripletrail | oxigraph | qlever | jena | graphdb | maplib | rows |
|---|---:|---:|---:|---:|---:|---:|---|
| load (s) | 3.84 | 9.264 | 7.554 | 26.916 | 45.017 | 15.749 | |
| q1_count | 2.5 (4.5) | 2,766 (3,280) | 60.0 (74.8) | 1,413 (3,268) | 1,698 (2,372) | 523 (525) | 1 |
| q2_customer_orders | 2,373 (2,360) | 13,564 (13,734) | 412 (440) | 13,030 (24,910) | 4,958 (5,181) | 94.8 (107) | 20 |
| q3_join_3_entities | 499 (501) | 3,209 (3,220) | 271 (274) | 1,262 (1,297) | 906 (929) | 131 (165) | 50 |
| q4_optional_aggregation | 2,101 (2,086) | 11,430 (11,635) | 630 (648) | 14,824 (17,706) | 6,035 (6,129) | 159 (152) | 50 |
| q5_construct | 1,021 (1,029) | 5,395 (5,433) | 1,695 (2,812) | 1,813 (2,878) | 3,911 (4,044) | 711 (805) | 439240 |
| q6_delete_insert | 184 | 349 | 38.1 | 599 | 1,009 | 43.2 |  |
| geometric mean q1-q5 | 365 | 5,945 | 372 | 3,623 | 2,825 | 236 | |
