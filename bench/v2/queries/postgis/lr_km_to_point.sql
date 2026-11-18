-- point at the fraction km / geodesic length of the line (geography form, PostGIS >= 3.4)
SELECT ST_AsText(ST_LineInterpolatePoint(geom::geography,
  least(1.0, {{km}} * 1000 / ST_Length(geom::geography)))::geometry)
FROM line WHERE iri = '{{line}}'
