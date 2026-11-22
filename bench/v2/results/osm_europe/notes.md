GraphDB's `osm_station_admin` and `osm_track_landuse` are not run here. In run 45004762850 they ran only in the
triple form of bench commit 2b9eb00, which is not the query in main. The form in main already hit the 600 s limit
at 201M triples (osm_benelux, run 44958878631).
