| Engine | Load (s) | Index / start (s) | On disk | RSS after start | Triples |
|---|---|---|---|---|---|
| tripletrail | 4931.5 | 12.833 | 177.82 GiB | 9788 MiB (heap 41 MiB) | 1,000,042,312 |


**Family 8 osm** — warm p50 / p95 in ms (cold first run in brackets)

| Query | tripletrail |
|---|---|
| osm_station_admin | 3.60 s / 3.60 s (53 s) |
| osm_track_landuse | timeout [1] |
| osm_track_track_5m | 7.80 s / 7.84 s (105 s) |

**Family 9 scale** — warm p50 / p95 in ms (cold first run in brackets)

| Query | tripletrail |
|---|---|
| scale_class_counts | 1.2 / 1.7 (201) |
| scale_building_kinds | 5.3 / 5.3 (10 s) |
| scale_label_lookup | 0.9 / 2.5 (189) |
| scale_named_stations | 30 / 32 (360) |

Notes:

1. tripletrail osm_track_landuse: timeout: HTTP 503: The operation took longer than its timeout
