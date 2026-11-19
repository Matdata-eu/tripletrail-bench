| Engine | Load (s) | Index / start (s) | On disk | RSS after start | Triples |
|---|---|---|---|---|---|
| tripletrail | 4.4 | 0.55 | 759 MiB | 902 MiB (heap 123 MiB) | 10,539,890 |
| PostGIS/pgRouting | 35.3 | - | 893 MiB | 185 MiB (sum over backends, shared buffers counted per process) | 2,166,762 rows |
| GraphDB | 40.7 | 20.016 | 1.07 GiB | 5.938GiB / 61.31GiB | 10,539,890 |
| Jena GeoSPARQL | 56.9 | 59.212 | 1.94 GiB | 4042 MiB | 10,539,890 |
| QLever | 9.3 | 0.531 | 204 MiB | 6.633MiB / 61.31GiB | 10,539,890 |


**Family 1 selection** — warm p50 / p95 in ms (cold first run in brackets)

| Query | tripletrail | PostGIS/pgRouting | GraphDB | Jena GeoSPARQL | QLever |
|---|---|---|---|---|---|
| sel_bbox | 3.7 / 4.7 (26) | 0.6 / 0.9 (13) | 200 / 351 (629) | 24 / 45 (161) | 610 / 1.10 s (468) |
| sel_polygon | 3.2 / 3.6 (3.9) | 0.5 / 0.8 (0.5) | 168 / 200 (201) | 44 / 61 (108) | 457 / 795 (770) |
| sel_distance | 3.1 / 4.3 (2.7) | 1.6 / 3.7 (24) | 2.05 s / 2.43 s (2.52 s) | 28 / 57 (39) | 134 / 756 (144) |

**Family 2 knn** — warm p50 / p95 in ms (cold first run in brackets)

| Query | tripletrail | PostGIS/pgRouting | GraphDB | Jena GeoSPARQL | QLever |
|---|---|---|---|---|---|
| knn_signals | 6.5 / 9.9 (85) | 0.5 / 0.7 (35) | 3.17 s / 3.76 s (6.15 s) | 2.21 s / 2.60 s (9.22 s) | 144 / 163 (172) |
| knn_ops | 12 / 16 (8.2) | 1.0 / 1.2 (1.4) | 580 / 701 (583) | 424 / 475 (1.58 s) | 63 / 72 (73) |

**Family 3 join** — warm p50 / p95 in ms (cold first run in brackets)

| Query | tripletrail | PostGIS/pgRouting | GraphDB | Jena GeoSPARQL | QLever |
|---|---|---|---|---|---|
| join_signal_ne_20m | 341 / 359 (361) | 842 / 848 (941) | error [1] | error [2] | 2.36 s / 2.40 s (2.49 s) |
| join_op_region | 66 / 73 (57) | 41 / 41 (55) | 17 s / 17 s (17 s) | 7.26 s / 8.22 s (9.52 s) | 458 / 479 (472) |

**Family 4 aggregate** — warm p50 / p95 in ms (cold first run in brackets)

| Query | tripletrail | PostGIS/pgRouting | GraphDB | Jena GeoSPARQL | QLever |
|---|---|---|---|---|---|
| agg_length_region | 906 / 938 (948) | 5.45 s / 5.48 s (5.78 s) | N/A [3] | N/A [4] | N/A [5] |
| agg_total_length | 175 / 198 (150) | 255 / 261 (302) | N/A [3] | N/A [4] | 473 / 491 (503) |
| agg_union_buffers | 10 / 16 (27) | 5.6 / 12 (12) | N/A [3] | N/A [4] | N/A [6] |

**Family 5 linear referencing** — warm p50 / p95 in ms (cold first run in brackets)

| Query | tripletrail | PostGIS/pgRouting | GraphDB | Jena GeoSPARQL | QLever |
|---|---|---|---|---|---|
| lr_km_to_point | 4.6 / 9.8 (4.9) | 9.1 / 12 (45) | N/A [7] | N/A [7] | N/A [7] |
| lr_assets_between_km | 13 / 13 (345) | 0.3 / 0.3 (1.0) | 16 / 23 (320) | 34 / 60 (206) | 21 / 33 (43) |

**Family 6 routing** — warm p50 / p95 in ms (cold first run in brackets)

| Query | tripletrail | PostGIS/pgRouting | GraphDB | Jena GeoSPARQL | QLever |
|---|---|---|---|---|---|
| route_dijkstra | 48 / 77 (3.92 s) | 786 / 869 (1.21 s) | N/A [8] | N/A [8] | N/A [8] |
| route_dijkstra_cost | 45 / 74 (59) | 782 / 860 (852) | N/A [8] | N/A [8] | N/A [8] |
| route_bddijkstra | 41 / 76 (86) | 788 / 874 (850) | N/A [8] | N/A [8] | N/A [8] |
| route_ch | 7.5 / 13 (3.49 s) | N/A [9] | N/A [8] | N/A [8] | N/A [8] |
| route_constrained | 38 / 66 (7.31 s) | 672 / 730 (670) | N/A [8] | N/A [8] | N/A [8] |
| driving_distance_50km | 7.9 / 14 (5.4) | 1.82 s / 2.31 s (1.16 s) | N/A [8] | N/A [8] | N/A [8] |
| ksp5 | 93 / 208 (167) | 12 s / 51 s (49 s) | N/A [8] | N/A [8] | N/A [8] |
| cost_matrix_100 | 462 / 470 (470) | 18 s / 18 s (18 s) | N/A [8] | N/A [8] | N/A [8] |
| components | 296 / 341 (534) | 870 / 873 (893) | N/A [8] | N/A [8] | N/A [8] |

**Family 7 mixed** — warm p50 / p95 in ms (cold first run in brackets)

| Query | tripletrail | PostGIS/pgRouting | GraphDB | Jena GeoSPARQL | QLever |
|---|---|---|---|---|---|
| mixed_route_signals | 574 / 641 (1.01 s) | 775 / 881 (1.28 s) | N/A [8] | N/A [8] | N/A [8] |

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
