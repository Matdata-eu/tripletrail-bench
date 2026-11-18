SELECT r.iri, sum(ST_Length(ST_Intersection(e.geom, r.geom)::geography))
FROM region r JOIN ne e ON ST_Intersects(e.geom, r.geom) GROUP BY r.iri
