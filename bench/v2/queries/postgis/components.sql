SELECT count(*), max(n) FROM (
  SELECT component, count(*) AS n FROM pgr_connectedComponents('SELECT id, source, target, cost, reverse_cost FROM micro_edges') GROUP BY component) c
