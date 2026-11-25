# BSBM results

Berlin SPARQL Benchmark with the official bsbmtools 0.2 test driver (seed 808080, single client). QMpH = query mixes per hour (higher is better); per-template times are AQET in ms (lower is better), measured at the client. A result-count column that differs between engines marks a template where an engine answers differently.

## bsbm-2785 (2,785 products, 952,930 triples)

50 timed query mixes after 10 warm-up mixes.

| | tripletrail | oxigraph | qlever | jena | graphdb | maplib |
|---|---:|---:|---:|---:|---:|---:|
| load (s) | 0.561 | 4.706 | 1.729 | 6.213 | 13.478 | 0.393 |
| QMpH explore | 163,352 | 37,380 | 6,430 * | 9,749 | 22,448 | 13,362 * |
| QMpH bi | 65,352 | 631 | 20,895 | 2,907 | 4,735 | 27,435 * |
| QMpH update | 94,590 | 29,194 | n/a | 5,808 | 12,641 | 5,478 * |

\* maplib: BI Q5 skipped: maplib 0.22.0 rejects GROUP BY on a variable its subquery does not bind
\* maplib: explore-and-update: Q9 (DESCRIBE) and Q12 (CONSTRUCT) skipped: the test driver asks for RDF/XML, which the maplib endpoint does not serve
\* maplib: explore: Q9 (DESCRIBE) and Q12 (CONSTRUCT) skipped: the test driver asks for RDF/XML, which the maplib endpoint does not serve
\* qlever: explore: Q9 (DESCRIBE) and Q12 (CONSTRUCT) skipped: the test driver asks for RDF/XML, which QLever does not serve

### explore: AQET per template (ms), average result count

| query | tripletrail | oxigraph | qlever | jena | graphdb | maplib | results |
|---|---:|---:|---:|---:|---:|---:|---|
| Q1 | 0.5 | 2.0 | 7.8 | 2.7 | 4.5 | 3.8 | same |
| Q2 | 0.9 | 2.8 | 9.2 | 4.6 | 6.0 | 19.1 | same |
| Q3 | 0.5 | 2.2 | 13.6 | 2.9 | 4.8 | 5.3 | same |
| Q4 | 0.6 | 2.3 | 24.9 | 3.1 | 5.4 | 6.6 | same |
| Q5 | 0.9 | 15.4 | 17.9 | 141 | 10.8 | 9.7 | same |
| Q7 | 0.8 | 3.4 | 48.2 | 4.0 | 6.7 | 15.3 | same |
| Q8 | 0.8 | 2.6 | 22.6 | 3.5 | 5.6 | 13.5 | same |
| Q9 | 0.2 | 1.1 | skipped | 1.4 | 4.2 | skipped | bytes (DESCRIBE/CONSTRUCT), not compared |
| Q10 | 0.6 | 2.2 | 87.3 | 2.9 | 5.6 | 6.4 | same |
| Q11 | 0.4 | 1.5 | 3.0 | 2.4 | 4.5 | 11.4 | same |
| Q12 | 0.5 | 1.4 | skipped | 2.0 | 5.1 | skipped | bytes (DESCRIBE/CONSTRUCT), not compared |

### bi: AQET per template (ms), average result count

| query | tripletrail | oxigraph | qlever | jena | graphdb | maplib | results |
|---|---:|---:|---:|---:|---:|---:|---|
| Q1 | 1.5 | 87.9 | 5.3 | 181 | 21.5 | 7.2 | same |
| Q2 | 1.6 | 2187 | 24.2 | 376 | 243 | 6.2 | same |
| Q3 | 9.0 | 319 | 5.1 | 141 | 30.0 | 8.7 | same |
| Q4 | 11.7 | 67.5 | 30.2 | 64.8 | 84.4 | 9.4 | same |
| Q5 | 1.3 | 6.8 | 5.3 | 6.4 | 6.8 | skipped | same |
| Q6 | 4.7 | 27.3 | 12.7 | 13.9 | 23.1 | 17.5 | same |
| Q7 | 0.7 | 355 | 3.4 | 3.6 | 3.7 | 5.5 | same |
| Q8 | 1.7 | 9.4 | 5.3 | 8.2 | 7.8 | 7.9 | same |

## bsbm-28480 (28,480 products, 9,609,918 triples)

50 timed query mixes after 10 warm-up mixes.

| | tripletrail | oxigraph | qlever | jena | graphdb | maplib |
|---|---:|---:|---:|---:|---:|---:|
| load (s) | 5.849 | 13.163 | 12.431 | 41.806 | 49.505 | 3.853 |
| QMpH explore | 133,124 | 13,243 | 6,756 * | 2,003 | 18,231 | 7,471 * |
| QMpH bi | 28,973 | 52 | 4,791 | 211 | 611 | 23,177 * |
| QMpH update | 79,868 | 12,596 | n/a | 1,760 | 9,730 | 1,168 * |

\* maplib: BI Q5 skipped: maplib 0.22.0 rejects GROUP BY on a variable its subquery does not bind
\* maplib: explore-and-update: Q9 (DESCRIBE) and Q12 (CONSTRUCT) skipped: the test driver asks for RDF/XML, which the maplib endpoint does not serve
\* maplib: explore: Q9 (DESCRIBE) and Q12 (CONSTRUCT) skipped: the test driver asks for RDF/XML, which the maplib endpoint does not serve
\* qlever: explore: Q9 (DESCRIBE) and Q12 (CONSTRUCT) skipped: the test driver asks for RDF/XML, which QLever does not serve

### explore: AQET per template (ms), average result count

| query | tripletrail | oxigraph | qlever | jena | graphdb | maplib | results |
|---|---:|---:|---:|---:|---:|---:|---|
| Q1 | 0.6 | 5.7 | 6.6 | 2.7 | 4.2 | 44.9 | same |
| Q2 | 1.0 | 3.0 | 8.1 | 4.4 | 5.3 | 19.9 | same |
| Q3 | 0.6 | 8.2 | 10.6 | 2.8 | 4.8 | 45.8 | same |
| Q4 | 0.7 | 7.4 | 22.5 | 3.6 | 5.3 | 97.2 | same |
| Q5 | 2.9 | 94.1 | 9.9 | 856 | 35.0 | 10.1 | same |
| Q7 | 0.9 | 3.6 | 48.6 | 4.0 | 6.1 | 20.8 | same |
| Q8 | 0.9 | 2.8 | 20.8 | 3.0 | 5.1 | 13.2 | same |
| Q9 | 0.2 | 1.2 | skipped | 1.5 | 3.8 | skipped | bytes (DESCRIBE/CONSTRUCT), not compared |
| Q10 | 0.8 | 2.7 | 89.1 | 2.5 | 5.0 | 10.5 | same |
| Q11 | 0.4 | 1.6 | 3.1 | 2.0 | 4.2 | 16.2 | same |
| Q12 | 0.5 | 1.4 | skipped | 2.2 | 4.9 | skipped | bytes (DESCRIBE/CONSTRUCT), not compared |

### bi: AQET per template (ms), average result count

| query | tripletrail | oxigraph | qlever | jena | graphdb | maplib | results |
|---|---:|---:|---:|---:|---:|---:|---|
| Q1 | 8.4 | 1038 | 11.5 | 6095 | 134 | 12.2 | same |
| Q2 | 7.5 | 25551 | 279 | 4521 | 2603 | 9.3 | same |
| Q3 | 40.5 | 4383 | 20.3 | 1621 | 240 | 14.2 | same |
| Q4 | 24.9 | 149 | 65.7 | 161 | 168 | 10.8 | same |
| Q5 | 1.9 | 12.6 | 7.0 | 10.5 | 8.8 | skipped | same |
| Q6 | 5.3 | 32.2 | 12.4 | 16.1 | 22.2 | 18.5 | same |
| Q7 | 0.9 | 5979 | 6.1 | 5.6 | 3.7 | 5.8 | same |
| Q8 | 2.5 | 13.3 | 7.1 | 13.8 | 10.2 | 8.7 | same |
