| Engine | Load (s) | Index / start (s) | On disk | RSS after start | Triples |
|---|---|---|---|---|---|
| tripletrail | 191.7 | 0.57 | 11.58 GiB | 13128 MiB (heap 3559 MiB); 1754 MiB (heap 31 MiB) when it first answered | 201,152,412 |
| GraphDB | 906.6 | 1082.251 | 41.06 GiB | 24.57GiB / 61.31GiB | 201,065,992 |
| QLever | 198.3 | 1.28 | 8.28 GiB | 21.64MiB / 61.31GiB | 201,065,992 |

The engines loaded different extracts (see the Triples column), so their answers are compared across extracts. data-<engine>.json and env-<engine>.json describe an engine that ran on its own.


**Family 8 osm** — warm p50 / p95 in ms (cold first run in brackets)

| Query | tripletrail | GraphDB | QLever |
|---|---|---|---|
| osm_station_admin | 105 / 119 (174) unchecked [1] | timeout [2] | 2.42 s / 2.42 s (2.46 s) unchecked [3] |
| osm_track_landuse | 1.37 s / 1.40 s (1.42 s) unchecked [4] | timeout [5] | 16 s / 16 s (16 s) unchecked [6] |
| osm_track_track_5m | 1.20 s / 1.22 s (1.24 s) unchecked [7] | timeout [8] | 2.33 s / 2.34 s (2.31 s) unchecked [9] |

**Family 9 scale** — warm p50 / p95 in ms (cold first run in brackets)

| Query | tripletrail | GraphDB | QLever |
|---|---|---|---|
| scale_class_counts | 4.1 / 5.6 (3.1) unchecked [10] | 12 s / 12 s (16 s) | 3.7 / 4.8 (7.0) |
| scale_building_kinds | 8.1 / 8.2 (75) unchecked [11] | 4.38 s / 4.41 s (4.72 s) | 16 / 16 (17) |
| scale_label_lookup | 2.6 / 4.8 (34) | 3.5 / 6.1 (13) | 6.7 / 8.5 (9.7) |
| scale_named_stations | 7.2 / 9.2 (6.2) unchecked [12] | 19 / 22 (46) | 87 / 89 (89) |

Notes:

1. tripletrail osm_station_admin: not checked (correctness.csv): other extract (201,152,412 triples against 201,065,992): 0 agree, 6 differ
2. GraphDB osm_station_admin: HTTP 503: Query interrupted: Query evaluation took too long

3. QLever osm_station_admin: not checked (correctness.csv): 6 runs without a majority answer
4. tripletrail osm_track_landuse: not checked (correctness.csv): other extract (201,152,412 triples against 201,065,992): 0 agree, 6 differ
5. GraphDB osm_track_landuse: HTTP 503: Query interrupted: Query evaluation took too long

6. QLever osm_track_landuse: not checked (correctness.csv): 6 runs without a majority answer
7. tripletrail osm_track_track_5m: not checked (correctness.csv): other extract (201,152,412 triples against 201,065,992): 0 agree, 6 differ
8. GraphDB osm_track_track_5m: HTTP 503: Query interrupted: Query evaluation took too long

9. QLever osm_track_track_5m: not checked (correctness.csv): 6 runs without a majority answer
10. tripletrail scale_class_counts: not checked (correctness.csv): other extract (201,152,412 triples against 201,065,992): 0 agree, 6 differ
11. tripletrail scale_building_kinds: not checked (correctness.csv): other extract (201,152,412 triples against 201,065,992): 0 agree, 6 differ
12. tripletrail scale_named_stations: not checked (correctness.csv): other extract (201,152,412 triples against 201,065,992): 0 agree, 6 differ
