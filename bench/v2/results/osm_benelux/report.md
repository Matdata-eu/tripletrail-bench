| Engine | Load (s) | Index / start (s) | On disk | RSS after start | Triples |
|---|---|---|---|---|---|
| GraphDB | 906.6 | 1082.251 | 41.06 GiB | 24.57GiB / 61.31GiB | 201,065,992 |


**Family 8 osm** — warm p50 / p95 in ms (cold first run in brackets)

| Query | GraphDB |
|---|---|
| osm_station_admin | error [1] |
| osm_track_landuse | error [2] |
| osm_track_track_5m | error [3] |

**Family 9 scale** — warm p50 / p95 in ms (cold first run in brackets)

| Query | GraphDB |
|---|---|
| scale_class_counts | 12 s / 12 s (16 s) |
| scale_building_kinds | 4.38 s / 4.41 s (4.72 s) |
| scale_label_lookup | 3.5 / 6.1 (13) |
| scale_named_stations | 19 / 22 (46) |

Notes:

1. GraphDB osm_station_admin: HTTP 503: Query interrupted: Query evaluation took too long

2. GraphDB osm_track_landuse: HTTP 503: Query interrupted: Query evaluation took too long

3. GraphDB osm_track_track_5m: HTTP 503: Query interrupted: Query evaluation took too long

