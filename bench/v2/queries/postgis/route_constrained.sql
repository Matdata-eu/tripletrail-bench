SELECT d.seq, e.iri AS edge, d.agg_cost
FROM pgr_dijkstra('SELECT id, source, target, cost, reverse_cost FROM micro_edges WHERE gauge = 1435 AND electrified',
  (SELECT id FROM vertex WHERE iri = '{{src}}'), (SELECT id FROM vertex WHERE iri = '{{dst}}'), directed => true) d
LEFT JOIN micro_edges e ON e.id = d.edge ORDER BY d.seq
