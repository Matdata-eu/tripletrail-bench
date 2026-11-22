| Engine | Load (s) | Index / start (s) | On disk | RSS after start | Triples |
|---|---|---|---|---|---|
| tripletrail | 155.1 | 0.537 | 30.74 GiB | 2223 MiB (heap 31 MiB) | 201,065,992 |
| GraphDB | 772.2 | 1146.741 | 41.06 GiB | 24.65GiB / 61.31GiB | 201,074,632 |
| QLever | 198.3 | 1.28 | 8.28 GiB | 21.64MiB / 61.31GiB | 201,065,992 |


**Family 8 osm** — warm p50 / p95 in ms (cold first run in brackets)

| Query | tripletrail | GraphDB | QLever |
|---|---|---|---|
| osm_station_admin | 76 / 77 (104) | error [1] | 2.42 s / 2.42 s (2.46 s) |
| osm_track_landuse | 1.53 s / 1.56 s (1.60 s) | error [2] | 16 s / 16 s (16 s) |
| osm_track_track_5m | 629 / 633 (616) | error [3] | 2.33 s / 2.34 s (2.31 s) |

**Family 9 scale** — warm p50 / p95 in ms (cold first run in brackets)

| Query | tripletrail | GraphDB | QLever |
|---|---|---|---|
| scale_class_counts | 1.4 / 1.7 (3.8) | 13 s / 13 s (23 s) | 3.7 / 4.8 (7.0) |
| scale_building_kinds | 3.9 / 4.1 (148) | 4.47 s / 4.50 s (4.74 s) | 16 / 16 (17) |
| scale_label_lookup | 0.9 / 1.2 (3.0) | 4.1 / 6.1 (14) | 6.7 / 8.5 (9.7) |
| scale_named_stations | 2.8 / 2.8 (5.2) | 15 / 16 (53) | 87 / 89 (89) |

Notes:

1. GraphDB osm_station_admin: HTTP 500: Query evaluation error: org.apache.lucene.store.AlreadyClosedException: Already closed: MMapIndexInput(path="/opt/graphdb/home/data/repositories/bench
2. GraphDB osm_track_landuse: HTTP 503: Query interrupted: Query evaluation took too long

3. GraphDB osm_track_track_5m: HTTP 503: Query interrupted: Query evaluation took too long

