| Engine | Load (s) | Index / start (s) | On disk | RSS after start | Triples |
|---|---|---|---|---|---|
| tripletrail | 4931.5 | 12.833 | 177.82 GiB | 9788 MiB (heap 41 MiB) | 1,000,042,312 |
| GraphDB | 4747.3 | 6286.912 | 234.92 GiB | 31.92GiB / 61.31GiB | 1,000,066,611 |


**Family 8 osm** — warm p50 / p95 in ms (cold first run in brackets)

| Query | tripletrail | GraphDB |
|---|---|---|
| osm_station_admin | 3.60 s / 3.60 s (53 s) | error [1] |
| osm_track_landuse | timeout [2] | error [3] |
| osm_track_track_5m | 7.80 s / 7.84 s (105 s) | error [4] |

**Family 9 scale** — warm p50 / p95 in ms (cold first run in brackets)

| Query | tripletrail | GraphDB |
|---|---|---|
| scale_class_counts | 1.2 / 1.7 (201) | 62 s / 63 s (73 s) |
| scale_building_kinds | 5.3 / 5.3 (10 s) | 19 s / 19 s (23 s) |
| scale_label_lookup | 0.9 / 2.5 (189) | 5.2 / 7.7 (33) |
| scale_named_stations | 30 / 32 (360) | 308 / 354 (1.73 s) |

Notes:

1. GraphDB osm_station_admin: HTTP 500: Query evaluation error: org.apache.lucene.store.AlreadyClosedException: Already closed: MMapIndexInput(path="/opt/graphdb/home/data/repositories/bench
2. tripletrail osm_track_landuse: timeout: HTTP 503: The operation took longer than its timeout
3. GraphDB osm_track_landuse: HTTP 503: Query interrupted: Query evaluation took too long

4. GraphDB osm_track_track_5m: HTTP 503: Query interrupted: Query evaluation took too long

