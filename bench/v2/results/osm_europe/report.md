| Engine | Load (s) | Index / start (s) | On disk | RSS after start | Triples |
|---|---|---|---|---|---|
| tripletrail | 4374.4 | 0.563 | 61.02 GiB | 51667 MiB (heap 14921 MiB); 7145 MiB (heap 31 MiB) when it first answered | 1,000,055,618 |
| GraphDB | 4747.3 | 6286.912 | 234.92 GiB | 31.92GiB / 61.31GiB | 1,000,066,611 |
| QLever | 1623.0 | 1.298 | 48.54 GiB | 94.23MiB / 61.31GiB | 1,000,066,611 |

The engines loaded different extracts (see the Triples column), so their answers are compared across extracts. data-<engine>.json and env-<engine>.json describe an engine that ran on its own.


**Family 8 osm** — warm p50 / p95 in ms (cold first run in brackets)

| Query | tripletrail | GraphDB | QLever |
|---|---|---|---|
| osm_station_admin | 3.99 s / 3.99 s (14 s) unchecked [1] | not run | 55 s / 55 s (85 s) unchecked [2] |
| osm_track_landuse | timeout [3] | not run | timeout [4] |
| osm_track_track_5m | 164 s / 164 s (280 s) unchecked [5] | timeout [6] | 23 s / 23 s (23 s) unchecked [7] |

**Family 9 scale** — warm p50 / p95 in ms (cold first run in brackets)

| Query | tripletrail | GraphDB | QLever |
|---|---|---|---|
| scale_class_counts | 2.7 / 7.8 (155) unchecked [8] | 62 s / 63 s (73 s) | 4.3 / 4.3 (7.8) |
| scale_building_kinds | 12 / 12 (1.32 s) unchecked [9] | 19 s / 19 s (23 s) | 33 / 34 (1.23 s) |
| scale_label_lookup | 2.4 / 2.8 (492) | 5.2 / 7.7 (33) | 8.2 / 9.1 (14) |
| scale_named_stations | 29 / 29 (4.00 s) unchecked [10] | 308 / 354 (1.73 s) | 851 / 860 (779) |

Notes:

1. tripletrail osm_station_admin: not checked (correctness.csv): other extract (1,000,055,618 triples against 1,000,066,611): 0 agree, 6 differ
2. QLever osm_station_admin: not checked (correctness.csv): 6 runs without a majority answer
3. tripletrail osm_track_landuse: client timeout
4. QLever osm_track_landuse: HTTP 429: {
    "exception": "Operation timed out. Last operation: Spatial Join of ?w1 and ?w2 using intersects",
    "query": "PREFIX era: <http://data.europa.
5. tripletrail osm_track_track_5m: not checked (correctness.csv): other extract (1,000,055,618 triples against 1,000,066,611): 0 agree, 5 differ
6. GraphDB osm_track_track_5m: HTTP 503: Query interrupted: Query evaluation took too long

7. QLever osm_track_track_5m: not checked (correctness.csv): 6 runs without a majority answer
8. tripletrail scale_class_counts: not checked (correctness.csv): other extract (1,000,055,618 triples against 1,000,066,611): 0 agree, 6 differ
9. tripletrail scale_building_kinds: not checked (correctness.csv): other extract (1,000,055,618 triples against 1,000,066,611): 0 agree, 6 differ
10. tripletrail scale_named_stations: not checked (correctness.csv): other extract (1,000,055,618 triples against 1,000,066,611): 0 agree, 6 differ

GraphDB's `osm_station_admin` and `osm_track_landuse` are not run here. In run 45004762850 they ran only in the
triple form of bench commit 2b9eb00, which is not the query in main. The form in main already hit the 600 s limit
at 201M triples (osm_benelux, run 44958878631).
