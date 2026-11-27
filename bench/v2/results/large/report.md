| Engine | Load (s) | Index / start (s) | On disk | RSS after start | Triples |
|---|---|---|---|---|---|
| tripletrail | 5.4 | 0.538 | 385 MiB | 1052 MiB (heap 641 MiB); 484 MiB (heap 77 MiB) when it first answered | 10,539,890 |
| tripletrail, 1 thread per query | 5.4 | 0.537 | 385 MiB | 781 MiB (heap 370 MiB); 488 MiB (heap 81 MiB) when it first answered | 10,539,890 |
| PostGIS/pgRouting | 35.3 | - | 893 MiB | 185 MiB (sum over backends, shared buffers counted per process) | 2,166,762 rows |
| GraphDB | 50.1 | 19.767 | 1.07 GiB | 5.964GiB / 61.31GiB | 10,539,890 |
| Jena GeoSPARQL | 58.1 | 60.274 | 1.94 GiB | 3864 MiB | 10,539,890 |
| QLever | 10.5 | 0.534 | 204 MiB | 6.562MiB / 61.31GiB | 10,539,890 |


**Family 1 selection** — warm p50 / p95 in ms (cold first run in brackets)

| Query | tripletrail | tripletrail, 1 thread per query | PostGIS/pgRouting | GraphDB | Jena GeoSPARQL | QLever |
|---|---|---|---|---|---|---|
| sel_bbox | 1.5 / 1.8 (21) | 1.7 / 2.6 (29) | 0.7 / 0.8 (17) | 196 / 346 (640) | 31 / 47 (163) | 584 / 1.07 s (437) |
| sel_polygon | 1.1 / 1.4 (1.4) | 1.2 / 1.4 (1.5) | 0.7 / 0.8 (0.8) | 168 / 202 (198) | 37 / 53 (130) | 421 / 749 (756) |
| sel_distance | 1.6 / 2.6 (1.0) | 1.7 / 2.6 (1.0) | 1.6 / 3.8 (24) | 2.08 s / 2.30 s (2.73 s) | 33 / 55 (37) | 144 / 725 (155) |

**Family 2 knn** — warm p50 / p95 in ms (cold first run in brackets)

| Query | tripletrail | tripletrail, 1 thread per query | PostGIS/pgRouting | GraphDB | Jena GeoSPARQL | QLever |
|---|---|---|---|---|---|---|
| knn_signals | 4.9 / 7.7 (50) | 4.9 / 7.6 (50) | 0.7 / 0.8 (38) | 3.16 s / 3.75 s (4.95 s) | 2.37 s / 2.66 s (10 s) | 125 / 152 (193) |
| knn_ops | 8.4 / 11 (5.7) | 8.7 / 11 (5.6) | 1.0 / 1.2 (1.7) | 589 / 691 (595) | 412 / 471 (1.71 s) | 41 / 56 (77) |

**Family 3 join** — warm p50 / p95 in ms (cold first run in brackets)

| Query | tripletrail | tripletrail, 1 thread per query | PostGIS/pgRouting | GraphDB | Jena GeoSPARQL | QLever |
|---|---|---|---|---|---|---|
| join_signal_ne_20m | 158 / 177 (211) | 243 / 257 (301) | 867 / 878 (964) | timeout [1] | timeout [2] | 2.92 s / 3.10 s (2.80 s) |
| join_op_region | 29 / 30 (29) | 31 / 41 (29) | 41 / 41 (56) | 17 s / 17 s (17 s) | 7.64 s / 8.02 s (9.37 s) | 392 / 413 (389) |

**Family 4 aggregate** — warm p50 / p95 in ms (cold first run in brackets)

| Query | tripletrail | tripletrail, 1 thread per query | PostGIS/pgRouting | GraphDB | Jena GeoSPARQL | QLever |
|---|---|---|---|---|---|---|
| agg_length_region | 490 / 536 (551) | 576 / 609 (644) | 5.46 s / 5.48 s (5.83 s) | N/A [3] | N/A [4] | N/A [5] |
| agg_total_length | 72 / 93 (81) | 116 / 124 (113) | 256 / 262 (298) | N/A [3] | N/A [4] | 448 / 488 (503) |
| agg_union_buffers | 3.4 / 5.3 (22) | 3.3 / 5.2 (21) | 5.6 / 13 (12) | N/A [3] | N/A [4] | N/A [6] |

**Family 5 linear referencing** — warm p50 / p95 in ms (cold first run in brackets)

| Query | tripletrail | tripletrail, 1 thread per query | PostGIS/pgRouting | GraphDB | Jena GeoSPARQL | QLever |
|---|---|---|---|---|---|---|
| lr_km_to_point | 4.5 / 5.3 (5.4) | 4.6 / 5.3 (5.0) | 9.2 / 12 (41) | N/A [7] | N/A [7] | N/A [7] |
| lr_assets_between_km | 1.7 / 3.7 (321) | 1.6 / 1.8 (325) | 0.3 / 0.4 (1.1) | 13 / 20 (232) | 37 / 58 (208) | 23 / 32 (39) |

**Family 6 routing** — warm p50 / p95 in ms (cold first run in brackets)

| Query | tripletrail | tripletrail, 1 thread per query | PostGIS/pgRouting | GraphDB | Jena GeoSPARQL | QLever |
|---|---|---|---|---|---|---|
| route_dijkstra | 26 / 50 (3.08 s) | 26 / 50 (3.07 s) | 837 / 927 (1.28 s) | N/A [8] | N/A [8] | N/A [8] |
| route_dijkstra_cost | 23 / 45 (51) | 23 / 45 (49) | 830 / 914 (911) | N/A [8] | N/A [8] | N/A [8] |
| route_bddijkstra | 20 / 48 (58) | 20 / 49 (58) | 834 / 927 (901) | N/A [8] | N/A [8] | N/A [8] |
| route_ch | 3.9 / 6.3 (2.93 s) | 3.9 / 6.2 (2.96 s) | N/A [9] | N/A [8] | N/A [8] | N/A [8] |
| route_constrained | 21 / 39 (6.32 s) | 21 / 40 (6.29 s) | 713 / 777 (703) | N/A [8] | N/A [8] | N/A [8] |
| driving_distance_50km | 3.7 / 6.1 (4.6) | 3.6 / 5.7 (4.1) | 1.84 s / 2.53 s (1.29 s) | N/A [8] | N/A [8] | N/A [8] |
| ksp5 | 61 / 149 (124) | 63 / 147 (122) | 12 s / 53 s (52 s) | N/A [8] | N/A [8] | N/A [8] |
| cost_matrix_100 | 448 / 458 (453) | 441 / 460 (445) | 20 s / 20 s (20 s) | N/A [8] | N/A [8] | N/A [8] |
| components | 224 / 239 (501) | 223 / 248 (463) | 895 / 941 (904) | N/A [8] | N/A [8] | N/A [8] |

**Family 7 mixed** — warm p50 / p95 in ms (cold first run in brackets)

| Query | tripletrail | tripletrail, 1 thread per query | PostGIS/pgRouting | GraphDB | Jena GeoSPARQL | QLever |
|---|---|---|---|---|---|---|
| mixed_route_signals | 436 / 495 (918) | 468 / 535 (948) | 817 / 947 (1.35 s) | N/A [8] | N/A [8] | N/A [8] |

Notes:

1. GraphDB join_signal_ne_20m: HTTP 503: Query interrupted: Query evaluation took too long

2. Jena GeoSPARQL join_signal_ne_20m: HTTP 503: Query timed out

3. geof:metricLength / metricArea / aggUnion (GeoSPARQL 1.1) are unknown to GraphDB 10.8 (HTTP 500 'Unknown function')
4. geof:metricLength / metricArea / aggUnion are not implemented by jena-geosparql 6.2 (they return no value; geof:intersection works)
5. geof:intersection is not supported by QLever (HTTP 400 'not supported')
6. geof:buffer and geof:aggUnion are not supported by QLever
7. no linear-referencing functions
8. no routing
9. pgRouting has no contraction-hierarchy query (pgr_contraction only contracts)
