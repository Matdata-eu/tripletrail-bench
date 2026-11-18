SELECT iri FROM signal WHERE ST_Within(geom, ST_GeomFromText('{{poly_wkt}}', 4326))
