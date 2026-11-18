SELECT iri FROM signal WHERE ST_Within(geom, ST_GeomFromText('{{bbox_wkt}}', 4326))
