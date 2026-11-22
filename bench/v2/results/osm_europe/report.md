| Engine | Load (s) | Index / start (s) | On disk | RSS after start | Triples |
|---|---|---|---|---|---|
| tripletrail | 4931.5 | 12.833 | 177.82 GiB | 9788 MiB (heap 41 MiB) | 1,000,042,312 |
| GraphDB | 4747.3 | 6286.912 | 234.92 GiB | 31.92GiB / 61.31GiB | 1,000,066,611 |

The engines loaded different extracts (see the Triples column), so their answers are compared across extracts. data-<engine>.json and env-<engine>.json describe an engine that ran on its own.


**Family 8 osm** — warm p50 / p95 in ms (cold first run in brackets)

| Query | tripletrail | GraphDB |
|---|---|---|
| osm_station_admin | 3.60 s / 3.60 s (53 s) | not run |
| osm_track_landuse | timeout [1] | not run |
| osm_track_track_5m | 7.80 s / 7.84 s (105 s) | error [2] |

**Family 9 scale** — warm p50 / p95 in ms (cold first run in brackets)

| Query | tripletrail | GraphDB |
|---|---|---|
| scale_class_counts | 1.2 / 1.7 (201) | 62 s / 63 s (73 s) |
| scale_building_kinds | 5.3 / 5.3 (10 s) | 19 s / 19 s (23 s) |
| scale_label_lookup | 0.9 / 2.5 (189) | 5.2 / 7.7 (33) |
| scale_named_stations | 30 / 32 (360) | 308 / 354 (1.73 s) |

Notes:

1. tripletrail osm_track_landuse: timeout: HTTP 503: The operation took longer than its timeout
2. GraphDB osm_track_track_5m: HTTP 503: Query interrupted: Query evaluation took too long


GraphDB's `osm_station_admin` and `osm_track_landuse` are not run here. In run 45004762850 they ran only in the
triple form of bench commit 2b9eb00, which is not the query in main. The form in main already hit the 600 s limit
at 201M triples (osm_benelux, run 44958878631).
