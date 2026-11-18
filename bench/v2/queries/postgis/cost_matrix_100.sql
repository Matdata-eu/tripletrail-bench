SELECT count(*), sum(agg_cost) FROM pgr_dijkstraCostMatrix('SELECT id, source, target, cost, reverse_cost FROM micro_edges',
  ARRAY(SELECT id FROM vertex WHERE iri = ANY({{sql_vids}})), directed => true)
