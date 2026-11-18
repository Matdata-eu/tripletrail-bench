SELECT ST_Area(ST_Union(ST_Buffer(geom::geography, 50)::geometry)::geography)
FROM signal WHERE ST_Within(geom, ST_GeomFromText('{{bbox_wkt}}', 4326))
