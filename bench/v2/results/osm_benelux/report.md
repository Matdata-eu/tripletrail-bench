| Engine | Load (s) | Index / start (s) | On disk | RSS after start | Triples |
|---|---|---|---|---|---|
| tripletrail | 168.1 | 0.569 | 11.58 GiB | 10098 MiB (heap 2769 MiB) | 201,089,129 |
| GraphDB | 906.6 | 1082.251 | 41.06 GiB | 24.57GiB / 61.31GiB | 201,065,992 |
| QLever | 198.3 | 1.28 | 8.28 GiB | 21.64MiB / 61.31GiB | 201,065,992 |

The engines loaded different extracts (see the Triples column), so their answers are compared across extracts. data-<engine>.json and env-<engine>.json describe an engine that ran on its own.


**Family 8 osm** — warm p50 / p95 in ms (cold first run in brackets)

| Query | tripletrail | GraphDB | QLever |
|---|---|---|---|
| osm_station_admin | 96 / 98 (278) | timeout [1] | 2.42 s / 2.42 s (2.46 s) |
| osm_track_landuse | 1.25 s / 1.26 s (1.76 s) | timeout [2] | 16 s / 16 s (16 s) |
| osm_track_track_5m | 561 / 568 (573) | timeout [3] | 2.33 s / 2.34 s (2.31 s) |

**Family 9 scale** — warm p50 / p95 in ms (cold first run in brackets)

| Query | tripletrail | GraphDB | QLever |
|---|---|---|---|
| scale_class_counts | 2.9 / 3.0 (9.0) | 12 s / 12 s (16 s) | 3.7 / 4.8 (7.0) |
| scale_building_kinds | 7.3 / 7.5 (114) | 4.38 s / 4.41 s (4.72 s) | 16 / 16 (17) |
| scale_label_lookup | 2.3 / 2.8 (10) | 3.5 / 6.1 (13) | 6.7 / 8.5 (9.7) |
| scale_named_stations | 5.2 / 5.3 (137) | 19 / 22 (46) | 87 / 89 (89) |

Notes:

1. GraphDB osm_station_admin: HTTP 503: Query interrupted: Query evaluation took too long

2. GraphDB osm_track_landuse: HTTP 503: Query interrupted: Query evaluation took too long

3. GraphDB osm_track_track_5m: HTTP 503: Query interrupted: Query evaluation took too long

