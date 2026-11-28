| Engine | Load (s) | Index / start (s) | On disk | RSS after start | Triples |
|---|---|---|---|---|---|
| tripletrail | 4.9 | 0.56 | 637 MiB | 712 MiB (heap 51 MiB) | 10,539,890 |
| PostGIS/pgRouting | 35.3 | - | 893 MiB | 185 MiB (sum over backends, shared buffers counted per process) | 2,166,762 rows |
| GraphDB | 50.1 | 19.767 | 1.07 GiB | 5.964GiB / 61.31GiB | 10,539,890 |
| Jena GeoSPARQL | 58.1 | 60.274 | 1.94 GiB | 3864 MiB | 10,539,890 |
| QLever | 10.5 | 0.534 | 204 MiB | 6.562MiB / 61.31GiB | 10,539,890 |


**Family 1 selection** — warm p50 / p95 in ms (cold first run in brackets)

| Query | tripletrail | PostGIS/pgRouting | GraphDB | Jena GeoSPARQL | QLever |
|---|---|---|---|---|---|
| sel_bbox | 4.3 / 5.5 (230) | 0.7 / 0.8 (17) | 196 / 346 (640) | 31 / 47 (163) | 584 / 1.07 s (437) |
| sel_polygon | 3.5 / 4.2 (3.5) | 0.7 / 0.8 (0.8) | 168 / 202 (198) | 37 / 53 (130) | 421 / 749 (756) |
| sel_distance | 4.5 / 5.9 (4.0) | 1.6 / 3.8 (24) | 2.08 s / 2.30 s (2.73 s) | ~~33 / 55 (37)~~ wrong [1] | ~~144 / 725 (155)~~ wrong [2] |

**Family 2 knn** — warm p50 / p95 in ms (cold first run in brackets)

| Query | tripletrail | PostGIS/pgRouting | GraphDB | Jena GeoSPARQL | QLever |
|---|---|---|---|---|---|
| knn_signals | 13 / 20 (282) | 0.7 / 0.8 (38) | 3.16 s / 3.75 s (4.95 s) | 2.37 s / 2.66 s (10 s) | 125 / 152 (193) |
| knn_ops | 25 / 31 (16) | 1.0 / 1.2 (1.7) | 589 / 691 (595) | 412 / 471 (1.71 s) | 41 / 56 (77) |

**Family 3 join** — warm p50 / p95 in ms (cold first run in brackets)

| Query | tripletrail | PostGIS/pgRouting | GraphDB | Jena GeoSPARQL | QLever |
|---|---|---|---|---|---|
| join_signal_ne_20m | 275 / 309 (321) | 867 / 878 (964) | timeout [3] | timeout [4] | ~~2.92 s / 3.10 s (2.80 s)~~ wrong [5] |
| join_op_region | 76 / 111 (47) | 41 / 41 (56) | 17 s / 17 s (17 s) | 7.64 s / 8.02 s (9.37 s) | ~~392 / 413 (389)~~ wrong [6] |

**Family 4 aggregate** — warm p50 / p95 in ms (cold first run in brackets)

| Query | tripletrail | PostGIS/pgRouting | GraphDB | Jena GeoSPARQL | QLever |
|---|---|---|---|---|---|
| agg_length_region | 1.59 s / 1.62 s (1.69 s) | 5.46 s / 5.48 s (5.83 s) | N/A [7] | N/A [8] | N/A [9] |
| agg_total_length | 116 / 126 (101) | 256 / 262 (298) | N/A [7] | N/A [8] | ~~448 / 488 (503)~~ wrong [10] |
| agg_union_buffers | 9.9 / 17 (50) | 5.6 / 13 (12) | N/A [7] | N/A [8] | N/A [11] |

**Family 5 linear referencing** — warm p50 / p95 in ms (cold first run in brackets)

| Query | tripletrail | PostGIS/pgRouting | GraphDB | Jena GeoSPARQL | QLever |
|---|---|---|---|---|---|
| lr_km_to_point | 11 / 13 (13) | 9.2 / 12 (41) | N/A [12] | N/A [12] | N/A [12] |
| lr_assets_between_km | 5.2 / 5.6 (387) | 0.3 / 0.4 (1.1) | 13 / 20 (232) | 37 / 58 (208) | 23 / 32 (39) |

**Family 6 routing** — warm p50 / p95 in ms (cold first run in brackets)

| Query | tripletrail | PostGIS/pgRouting | GraphDB | Jena GeoSPARQL | QLever |
|---|---|---|---|---|---|
| route_dijkstra | 51 / 80 (3.94 s) | 837 / 927 (1.28 s) | N/A [13] | N/A [13] | N/A [13] |
| route_dijkstra_cost | 46 / 76 (79) | 830 / 914 (911) | N/A [13] | N/A [13] | N/A [13] |
| route_bddijkstra | ~~43 / 80 (67)~~ wrong [14] | 834 / 927 (901) | N/A [13] | N/A [13] | N/A [13] |
| route_ch | 9.1 / 15 (3.33 s) unchecked [15] | N/A [16] | N/A [13] | N/A [13] | N/A [13] |
| route_constrained | 42 / 69 (7.37 s) | 713 / 777 (703) | N/A [13] | N/A [13] | N/A [13] |
| driving_distance_50km | 8.6 / 13 (9.4) | 1.84 s / 2.53 s (1.29 s) | N/A [13] | N/A [13] | N/A [13] |
| ksp5 | 94 / 218 (174) | 12 s / 53 s (52 s) | N/A [13] | N/A [13] | N/A [13] |
| cost_matrix_100 | 462 / 479 (499) | 20 s / 20 s (20 s) | N/A [13] | N/A [13] | N/A [13] |
| components | 298 / 301 (568) | 895 / 941 (904) | N/A [13] | N/A [13] | N/A [13] |

**Family 7 mixed** — warm p50 / p95 in ms (cold first run in brackets)

| Query | tripletrail | PostGIS/pgRouting | GraphDB | Jena GeoSPARQL | QLever |
|---|---|---|---|---|---|
| mixed_route_signals | 592 / 663 (1.32 s) | 817 / 947 (1.35 s) | N/A [13] | N/A [13] | N/A [13] |

Notes:

1. Jena GeoSPARQL sel_distance: answer differs from the reference (correctness.csv): ref 6 got 7: 0 missing, 1 extra
2. QLever sel_distance: answer differs from the reference (correctness.csv): ref 6 got 7: 0 missing, 1 extra
3. GraphDB join_signal_ne_20m: HTTP 503: Query interrupted: Query evaluation took too long

4. Jena GeoSPARQL join_signal_ne_20m: HTTP 503: Query timed out

5. QLever join_signal_ne_20m: answer differs from the reference (correctness.csv): [315812.0] vs [315829.0] (x8)
6. QLever join_op_region: answer differs from the reference (correctness.csv): 4 groups differ, e.g. 0_3: 2588.0 vs 2589.0 (x8)
7. geof:metricLength / metricArea / aggUnion (GeoSPARQL 1.1) are unknown to GraphDB 10.8 (HTTP 500 'Unknown function')
8. geof:metricLength / metricArea / aggUnion are not implemented by jena-geosparql 6.2 (they return no value; geof:intersection works)
9. geof:intersection is not supported by QLever (HTTP 400 'not supported')
10. QLever agg_total_length: answer differs from the reference (correctness.csv): [166293719.21746182] vs [165988198.3654]; [166293719.21746174] vs [165988198.3654]; [166293719.2174618] vs [165988198.3654]
11. geof:buffer and geof:aggUnion are not supported by QLever
12. no linear-referencing functions
13. no routing
14. tripletrail route_bddijkstra: answer differs from the reference (correctness.csv): cost 116812.4 vs 116700.80000000003 (232 vs 232 edges); match: no path (x23); cost 180525.2000000001 vs 180465.59999999986 (354 vs 356 edges)
15. tripletrail route_ch: not checked (correctness.csv): 1003 runs without a majority answer
16. pgRouting has no contraction-hierarchy query (pgr_contraction only contracts)
