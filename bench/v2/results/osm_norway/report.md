| Engine | Load (s) | Index / start (s) | On disk | RSS after start | Triples |
|---|---|---|---|---|---|
| tripletrail | 1.7 | 1.093 | 170 MiB | 245 MiB (heap 51 MiB) | 1,458,029 |
| PostGIS/pgRouting | 24.4 | - | 815 MiB | 186 MiB (sum over backends, shared buffers counted per process) | 290,336 rows |
| GraphDB | 17.6 | 23.597 | 1.01 GiB | 5.901GiB / 61.31GiB | 1,458,029 |
| Jena GeoSPARQL | 14.9 | 33.815 | 811 MiB | 5524 MiB | 1,458,029 |
| QLever | 7.3 | 0.505 | 190 MiB | 6.109MiB / 61.31GiB | 1,458,029 |


**Family 8 osm** — warm p50 / p95 in ms (cold first run in brackets)

| Query | tripletrail | PostGIS/pgRouting | GraphDB | Jena GeoSPARQL | QLever |
|---|---|---|---|---|---|
| osm_station_admin | 41 / 44 (69) | 160 / 162 (213) | 204 s / 204 s (205 s) | 3.95 s / 4.04 s (6.70 s) | 2.77 s / 2.78 s (2.80 s) |
| osm_track_landuse | 162 / 176 (166) | 707 / 718 (833) | error [1] | error [2] | 2.14 s / 2.16 s (2.22 s) |
| osm_track_track_5m | 41 / 45 (81) | 2.74 s / 2.76 s (2.72 s) | error [3] | 98 s / 98 s (100 s) | 451 / 463 (501) |

Notes:

1. GraphDB osm_track_landuse: HTTP 503: Query interrupted: Query evaluation took too long

2. Jena GeoSPARQL osm_track_landuse: HTTP 503: Query timed out

3. GraphDB osm_track_track_5m: HTTP 503: Query interrupted: Query evaluation took too long

