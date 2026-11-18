SELECT a.iri, count(*) FROM osm_admin a JOIN osm_station s ON ST_Within(s.geom, a.geom) GROUP BY a.iri
