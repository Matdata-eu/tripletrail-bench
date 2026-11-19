| Engine | Load (s) | Index / start (s) | On disk | RSS after start | Triples |
|---|---|---|---|---|---|
| tripletrail | 1.7 | 0.566 | 697 MiB | 809 MiB (heap 91 MiB) | 1,458,029 |
| PostGIS/pgRouting | 24.1 | - | 824 MiB | 186 MiB (sum over backends, shared buffers counted per process) | 290,336 rows |
| GraphDB | 18.1 | 23.649 | 1.01 GiB | 5.801GiB / 61.31GiB | 1,458,029 |
| Jena GeoSPARQL | 14.2 | 32.781 | 811 MiB | 5626 MiB | 1,458,029 |
| QLever | 7.0 | 0.484 | 190 MiB | 6.219MiB / 61.31GiB | 1,458,029 |


**Family 8 osm** — warm p50 / p95 in ms (cold first run in brackets)

| Query | tripletrail | PostGIS/pgRouting | GraphDB | Jena GeoSPARQL | QLever |
|---|---|---|---|---|---|
| osm_station_admin | 23 / 26 (43) | 157 / 157 (208) | 206 s / 206 s (206 s) | 3.62 s / 3.65 s (6.70 s) | 3.15 s / 3.16 s (3.22 s) |
| osm_track_landuse | 131 / 134 (159) | 701 / 704 (822) | error [1] | error [2] | 2.37 s / 2.41 s (2.37 s) |
| osm_track_track_5m | 86 / 94 (93) | 2.69 s / 2.70 s (2.71 s) | error [3] | 93 s / 95 s (94 s) | 834 / 842 (854) |

Notes:

1. GraphDB osm_track_landuse: HTTP 503: Query interrupted: Query evaluation took too long

2. Jena GeoSPARQL osm_track_landuse: HTTP 503: Query timed out

3. GraphDB osm_track_track_5m: HTTP 503: Query interrupted: Query evaluation took too long

