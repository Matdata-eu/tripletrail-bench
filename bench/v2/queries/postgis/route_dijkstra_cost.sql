-- cost only (no path rows): separates the search from producing ~500 rows per route
SELECT agg_cost FROM pgr_dijkstraCost('SELECT id, source, target, cost, reverse_cost FROM micro_edges',
  (SELECT id FROM vertex WHERE iri = '{{src}}'), (SELECT id FROM vertex WHERE iri = '{{dst}}'), directed => true)
