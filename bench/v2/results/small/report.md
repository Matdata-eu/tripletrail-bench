| Engine | Load (s) | Index / start (s) | On disk | RSS after start | Triples |
|---|---|---|---|---|---|
| tripletrail | 1.2 | 0.565 | 48 MiB | 157 MiB (heap 85 MiB) | 805,538 |
| PostGIS/pgRouting | 4.5 | - | 83 MiB | 170 MiB (sum over backends, shared buffers counted per process) | 165,466 rows |
| GraphDB | 12.8 | 2.531 | 143 MiB | 2.012GiB / 61.31GiB | 805,538 |
| Jena GeoSPARQL | 6.2 | 5.298 | 317 MiB | 939 MiB | 805,538 |
| QLever | 2.5 | 0.527 | 16 MiB | 5.895MiB / 61.31GiB | 805,538 |


**Family 1 selection** — warm p50 / p95 in ms (cold first run in brackets)

| Query | tripletrail | PostGIS/pgRouting | GraphDB | Jena GeoSPARQL | QLever |
|---|---|---|---|---|---|
| sel_bbox | 3.9 / 4.4 (9.6) | 0.7 / 0.8 (21) | 40 / 64 (483) | 21 / 35 (133) | 27 / 31 (40) |
| sel_polygon | 3.2 / 3.6 (3.6) | 0.6 / 0.7 (0.6) | 29 / 54 (63) | 25 / 36 (118) | 25 / 27 (25) |
| sel_distance | 3.4 / 4.2 (3.9) | 1.7 / 4.6 (24) | 172 / 285 (410) | 24 / 35 (50) | 23 / 26 (16) |

**Family 2 knn** — warm p50 / p95 in ms (cold first run in brackets)

| Query | tripletrail | PostGIS/pgRouting | GraphDB | Jena GeoSPARQL | QLever |
|---|---|---|---|---|---|
| knn_signals | 6.2 / 10 (18) | 0.9 / 0.9 (37) | 311 / 657 (924) | 200 / 319 (1.33 s) | 18 / 34 (45) |
| knn_ops | 12 / 16 (13) | 0.8 / 0.9 (1.5) | 79 / 93 (79) | 36 / 82 (147) | 17 / 19 (19) |

**Family 3 join** — warm p50 / p95 in ms (cold first run in brackets)

| Query | tripletrail | PostGIS/pgRouting | GraphDB | Jena GeoSPARQL | QLever |
|---|---|---|---|---|---|
| join_signal_ne_20m | 67 / 73 (65) | 162 / 177 (216) | error [1] | 7.74 s / 7.94 s (11 s) | 326 / 330 (304) |
| join_op_region | 17 / 17 (17) | 3.8 / 3.9 (5.9) | 466 / 499 (664) | 227 / 248 (603) | 77 / 93 (106) |

**Family 4 aggregate** — warm p50 / p95 in ms (cold first run in brackets)

| Query | tripletrail | PostGIS/pgRouting | GraphDB | Jena GeoSPARQL | QLever |
|---|---|---|---|---|---|
| agg_length_region | 182 / 190 (175) | 425 / 426 (480) | N/A [2] | N/A [3] | N/A [4] |
| agg_total_length | 37 / 41 (51) | 49 / 63 (66) | N/A [2] | N/A [3] | 59 / 68 (76) |
| agg_union_buffers | 9.3 / 12 (14) | 5.7 / 9.7 (12) | N/A [2] | N/A [3] | N/A [5] |

**Family 5 linear referencing** — warm p50 / p95 in ms (cold first run in brackets)

| Query | tripletrail | PostGIS/pgRouting | GraphDB | Jena GeoSPARQL | QLever |
|---|---|---|---|---|---|
| lr_km_to_point | 5.5 / 6.5 (6.2) | 2.8 / 3.5 (40) | N/A [6] | N/A [6] | N/A [6] |
| lr_assets_between_km | 3.6 / 3.9 (45) | 0.4 / 0.5 (1.0) | 11 / 22 (226) | 19 / 31 (176) | 16 / 18 (27) |

**Family 6 routing** — warm p50 / p95 in ms (cold first run in brackets)

| Query | tripletrail | PostGIS/pgRouting | GraphDB | Jena GeoSPARQL | QLever |
|---|---|---|---|---|---|
| route_dijkstra | 7.5 / 12 (279) | 36 / 41 (85) | N/A [7] | N/A [7] | N/A [7] |
| route_dijkstra_cost | 5.4 / 8.6 (4.8) | 35 / 41 (33) | N/A [7] | N/A [7] | N/A [7] |
| route_bddijkstra | 6.5 / 12 (5.0) | 36 / 42 (37) | N/A [7] | N/A [7] | N/A [7] |
| route_ch | 3.2 / 5.3 (110) | N/A [8] | N/A [7] | N/A [7] | N/A [7] |
| route_constrained | 7.1 / 10 (558) | 31 / 34 (31) | N/A [7] | N/A [7] | N/A [7] |
| driving_distance_50km | 6.7 / 9.0 (3.6) | 113 / 164 (32) | N/A [7] | N/A [7] | N/A [7] |
| ksp5 | 18 / 44 (13) | 244 / 842 (137) | N/A [7] | N/A [7] | N/A [7] |
| cost_matrix_100 | 32 / 34 (63) | 507 / 565 (491) | N/A [7] | N/A [7] | N/A [7] |
| components | 20 / 41 (38) | 52 / 53 (53) | N/A [7] | N/A [7] | N/A [7] |

**Family 7 mixed** — warm p50 / p95 in ms (cold first run in brackets)

| Query | tripletrail | PostGIS/pgRouting | GraphDB | Jena GeoSPARQL | QLever |
|---|---|---|---|---|---|
| mixed_route_signals | 80 / 90 (106) | 43 / 51 (98) | N/A [7] | N/A [7] | N/A [7] |

Notes:

1. GraphDB join_signal_ne_20m: HTTP 503: Query interrupted: Query evaluation took too long

2. geof:metricLength / metricArea / aggUnion (GeoSPARQL 1.1) are unknown to GraphDB 10.8 (HTTP 500 'Unknown function')
3. geof:metricLength / metricArea / aggUnion are not implemented by jena-geosparql 6.2 (they return no value; geof:intersection works)
4. geof:intersection is not supported by QLever (HTTP 400 'not supported')
5. geof:buffer and geof:aggUnion are not supported by QLever
6. no linear-referencing functions
7. no routing
8. pgRouting has no contraction-hierarchy query (pgr_contraction only contracts)
