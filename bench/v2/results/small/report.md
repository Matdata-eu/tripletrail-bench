| Engine | Load (s) | Index / start (s) | On disk | RSS after start | Triples |
|---|---|---|---|---|---|
| tripletrail | 0.6 | 0.566 | 57 MiB | 132 MiB (heap 55 MiB) | 805,538 |
| PostGIS/pgRouting | 4.5 | - | 83 MiB | 170 MiB (sum over backends, shared buffers counted per process) | 165,466 rows |
| GraphDB | 12.3 | 2.534 | 143 MiB | 1.966GiB / 61.31GiB | 805,538 |
| Jena GeoSPARQL | 6.0 | 5.271 | 317 MiB | 939 MiB | 805,538 |
| QLever | 2.5 | 0.508 | 16 MiB | 6.012MiB / 61.31GiB | 805,538 |


**Family 1 selection** — warm p50 / p95 in ms (cold first run in brackets)

| Query | tripletrail | PostGIS/pgRouting | GraphDB | Jena GeoSPARQL | QLever |
|---|---|---|---|---|---|
| sel_bbox | 3.2 / 4.0 (4.9) | 0.6 / 0.7 (20) | 56 / 69 (540) | 18 / 30 (126) | 31 / 36 (53) |
| sel_polygon | 2.9 / 3.1 (3.3) | 0.5 / 0.6 (0.6) | 40 / 61 (59) | 22 / 38 (143) | 28 / 31 (29) |
| sel_distance | 2.4 / 2.9 (2.8) | 1.6 / 4.0 (24) | 186 / 309 (396) | 24 / 34 (46) | 27 / 30 (30) |

**Family 2 knn** — warm p50 / p95 in ms (cold first run in brackets)

| Query | tripletrail | PostGIS/pgRouting | GraphDB | Jena GeoSPARQL | QLever |
|---|---|---|---|---|---|
| knn_signals | 4.6 / 6.9 (15) | 0.7 / 0.8 (36) | 302 / 508 (916) | 210 / 317 (1.27 s) | 26 / 33 (50) |
| knn_ops | 7.9 / 11 (9.2) | 0.7 / 0.9 (1.5) | 62 / 132 (75) | 40 / 64 (174) | 18 / 19 (19) |

**Family 3 join** — warm p50 / p95 in ms (cold first run in brackets)

| Query | tripletrail | PostGIS/pgRouting | GraphDB | Jena GeoSPARQL | QLever |
|---|---|---|---|---|---|
| join_signal_ne_20m | 59 / 60 (61) | 152 / 154 (207) | error [1] | 7.75 s / 7.86 s (11 s) | 394 / 402 (419) |
| join_op_region | 12 / 13 (15) | 3.8 / 3.8 (5.8) | 495 / 499 (679) | 245 / 270 (560) | 101 / 110 (105) |

**Family 4 aggregate** — warm p50 / p95 in ms (cold first run in brackets)

| Query | tripletrail | PostGIS/pgRouting | GraphDB | Jena GeoSPARQL | QLever |
|---|---|---|---|---|---|
| agg_length_region | 110 / 127 (132) | 422 / 426 (477) | N/A [2] | N/A [3] | N/A [4] |
| agg_total_length | 30 / 33 (29) | 61 / 62 (60) | N/A [2] | N/A [3] | 67 / 73 (80) |
| agg_union_buffers | 8.7 / 12 (12) | 5.6 / 9.5 (12) | N/A [2] | N/A [3] | N/A [5] |

**Family 5 linear referencing** — warm p50 / p95 in ms (cold first run in brackets)

| Query | tripletrail | PostGIS/pgRouting | GraphDB | Jena GeoSPARQL | QLever |
|---|---|---|---|---|---|
| lr_km_to_point | 4.6 / 6.2 (5.9) | 2.8 / 3.5 (30) | N/A [6] | N/A [6] | N/A [6] |
| lr_assets_between_km | 5.3 / 5.7 (47) | 0.3 / 0.3 (1.3) | 14 / 29 (220) | 23 / 35 (127) | 16 / 19 (31) |

**Family 6 routing** — warm p50 / p95 in ms (cold first run in brackets)

| Query | tripletrail | PostGIS/pgRouting | GraphDB | Jena GeoSPARQL | QLever |
|---|---|---|---|---|---|
| route_dijkstra | 6.6 / 11 (276) | 34 / 37 (74) | N/A [7] | N/A [7] | N/A [7] |
| route_dijkstra_cost | 4.2 / 7.0 (3.4) | 34 / 36 (33) | N/A [7] | N/A [7] | N/A [7] |
| route_bddijkstra | 5.7 / 11 (4.6) | 34 / 38 (34) | N/A [7] | N/A [7] | N/A [7] |
| route_ch | 2.9 / 4.5 (107) | N/A [8] | N/A [7] | N/A [7] | N/A [7] |
| route_constrained | 5.2 / 9.0 (548) | 31 / 33 (31) | N/A [7] | N/A [7] | N/A [7] |
| driving_distance_50km | 6.4 / 8.3 (3.3) | 114 / 157 (34) | N/A [7] | N/A [7] | N/A [7] |
| ksp5 | 14 / 40 (12) | 237 / 633 (135) | N/A [7] | N/A [7] | N/A [7] |
| cost_matrix_100 | 32 / 33 (63) | 486 / 530 (485) | N/A [7] | N/A [7] | N/A [7] |
| components | 18 / 35 (37) | 51 / 51 (52) | N/A [7] | N/A [7] | N/A [7] |

**Family 7 mixed** — warm p50 / p95 in ms (cold first run in brackets)

| Query | tripletrail | PostGIS/pgRouting | GraphDB | Jena GeoSPARQL | QLever |
|---|---|---|---|---|---|
| mixed_route_signals | 77 / 87 (101) | 41 / 50 (92) | N/A [7] | N/A [7] | N/A [7] |

Notes:

1. GraphDB join_signal_ne_20m: HTTP 503: Query interrupted: Query evaluation took too long

2. geof:metricLength / metricArea / aggUnion (GeoSPARQL 1.1) are unknown to GraphDB 10.8 (HTTP 500 'Unknown function')
3. geof:metricLength / metricArea / aggUnion are not implemented by jena-geosparql 6.2 (they return no value; geof:intersection works)
4. geof:intersection is not supported by QLever (HTTP 400 'not supported')
5. geof:buffer and geof:aggUnion are not supported by QLever
6. no linear-referencing functions
7. no routing
8. pgRouting has no contraction-hierarchy query (pgr_contraction only contracts)
