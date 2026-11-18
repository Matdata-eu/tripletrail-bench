WITH route AS (
  SELECT node FROM pgr_dijkstra('SELECT id, source, target, cost, reverse_cost FROM micro_edges',
    (SELECT id FROM vertex WHERE iri = '{{src}}'), (SELECT id FROM vertex WHERE iri = '{{dst}}'), directed => true))
SELECT DISTINCT s.iri FROM route
JOIN vertex v ON v.id = route.node
JOIN ne e ON e.iri = split_part(v.iri, '#', 1)
JOIN signal s ON s.signal_type = 'main'
  AND ST_DWithin(s.geom::geography, e.geom::geography, {{radius_m}})
