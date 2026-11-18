-- KNN on geography (index-assisted <->), ordered by exact spheroid distance
SELECT iri FROM (
  SELECT iri, geom FROM op
  ORDER BY geom::geography <-> ST_GeogFromText('SRID=4326;{{pt_wkt}}') LIMIT 10
) k ORDER BY ST_Distance(geom::geography, ST_GeogFromText('SRID=4326;{{pt_wkt}}'))
