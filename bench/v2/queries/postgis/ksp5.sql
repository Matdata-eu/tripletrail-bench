SELECT path_id, max(agg_cost) FROM pgr_KSP('SELECT id, source, target, cost, reverse_cost FROM micro_edges',
  (SELECT id FROM vertex WHERE iri = '{{src}}'), (SELECT id FROM vertex WHERE iri = '{{dst}}'), 5, directed => true) GROUP BY path_id
