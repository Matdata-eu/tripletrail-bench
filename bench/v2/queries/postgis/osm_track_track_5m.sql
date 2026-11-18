-- stand-in for the OSM<->RINF 5 m conflation join: ordered pairs of distinct OSM rail ways within 5 m
SELECT count(*) FROM osm_track a JOIN osm_track b ON a.iri <> b.iri AND ST_DWithin(a.geom::geography, b.geom::geography, 5)
