| Engine | Load (s) | Index / start (s) | On disk | RSS after start | Triples |
|---|---|---|---|---|---|
| tripletrail | 4235.0 | 0.534 | 61.02 GiB | 53319 MiB (heap 13744 MiB); 4933 MiB (heap 31 MiB) when it first answered | 1,000,017,822 |
| GraphDB | 4747.3 | 6286.912 | 234.92 GiB | 31.92GiB / 61.31GiB | 1,000,066,611 |
| QLever | 1623.0 | 1.298 | 48.54 GiB | 94.23MiB / 61.31GiB | 1,000,066,611 |

The engines loaded different extracts (see the Triples column), so their answers are compared across extracts. data-<engine>.json and env-<engine>.json describe an engine that ran on its own.


**Family 8 osm** — warm p50 / p95 in ms (cold first run in brackets)

| Query | tripletrail | GraphDB | QLever |
|---|---|---|---|
| osm_station_admin | 3.91 s / 3.94 s (10 s) | not run | 55 s / 55 s (85 s) |
| osm_track_landuse | timeout [1] | not run | timeout [2] |
| osm_track_track_5m | 7.05 s / 7.05 s (29 s) | timeout [3] | 23 s / 23 s (23 s) |

**Family 9 scale** — warm p50 / p95 in ms (cold first run in brackets)

| Query | tripletrail | GraphDB | QLever |
|---|---|---|---|
| scale_class_counts | 1.1 / 1.2 (45) | 62 s / 63 s (73 s) | 4.3 / 4.3 (7.8) |
| scale_building_kinds | 4.7 / 5.1 (700) | 19 s / 19 s (23 s) | 33 / 34 (1.23 s) |
| scale_label_lookup | 0.9 / 1.9 (283) | 5.2 / 7.7 (33) | 8.2 / 9.1 (14) |
| scale_named_stations | 15 / 15 (2.53 s) | 308 / 354 (1.73 s) | 851 / 860 (779) |

Notes:

1. tripletrail osm_track_landuse: client timeout
2. QLever osm_track_landuse: HTTP 429: {
    "exception": "Operation timed out. Last operation: Spatial Join of ?w1 and ?w2 using intersects",
    "query": "PREFIX era: <http://data.europa.
3. GraphDB osm_track_track_5m: HTTP 503: Query interrupted: Query evaluation took too long


GraphDB's `osm_station_admin` and `osm_track_landuse` are not run here. In run 45004762850 they ran only in the
triple form of bench commit 2b9eb00, which is not the query in main. The form in main already hit the 600 s limit
at 201M triples (osm_benelux, run 44958878631).
