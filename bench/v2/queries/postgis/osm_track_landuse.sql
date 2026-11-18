SELECT count(*) FROM osm_track t JOIN osm_landuse l ON ST_Intersects(t.geom, l.geom)
