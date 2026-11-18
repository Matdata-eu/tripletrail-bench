SELECT r.iri, count(o.iri) FROM region r JOIN op o ON ST_Within(o.geom, r.geom) GROUP BY r.iri
