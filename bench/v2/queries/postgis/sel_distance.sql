-- geodesic (spheroid) distance; uses the GiST index on geom::geography
SELECT iri FROM signal
WHERE ST_DWithin(geom::geography, ST_GeogFromText('SRID=4326;{{pt_wkt}}'), {{radius_m}})
