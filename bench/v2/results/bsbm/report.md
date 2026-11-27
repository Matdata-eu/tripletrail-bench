# BSBM results

Berlin SPARQL Benchmark with the official bsbmtools 0.2 test driver (seed 808080, single client). QMpH = query mixes per hour (higher is better); per-template times are AQET in ms (lower is better), measured at the client. A result-count column that differs between engines marks a template where an engine answers differently.

## bsbm-2785 (2,785 products, 952,930 triples)

50 timed query mixes after 10 warm-up mixes.

| | tripletrail | oxigraph | qlever | jena | graphdb | maplib | tripletrail-1t |
|---|---:|---:|---:|---:|---:|---:|---:|
| load (s) | 0.57 | 4.706 | 2.394 | 6.213 | 13.478 | 0.477 | 0.568 |
| QMpH explore | 211,431 | 37,380 | 4,661 * | 9,749 | 22,448 | 4,839 * | 199,693 |
| QMpH bi | 73,342 | 631 | 11,255 | 2,907 | 4,735 | 10,817 * | 71,829 |
| QMpH update | 119,814 | 29,194 | n/a | 5,808 | 12,641 | 2,073 * | 115,947 |

\* maplib: BI Q5 skipped: maplib 0.22.0 rejects GROUP BY on a variable its subquery does not bind
\* maplib: explore-and-update: Q9 (DESCRIBE) and Q12 (CONSTRUCT) skipped: the test driver asks for RDF/XML, which the maplib endpoint does not serve
\* maplib: explore: Q9 (DESCRIBE) and Q12 (CONSTRUCT) skipped: the test driver asks for RDF/XML, which the maplib endpoint does not serve
\* qlever: explore: Q9 (DESCRIBE) and Q12 (CONSTRUCT) skipped: the test driver asks for RDF/XML, which QLever does not serve

### explore: AQET per template (ms), average result count

| query | tripletrail | oxigraph | qlever | jena | graphdb | maplib | tripletrail-1t | results |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| Q1 | 0.4 | 2.0 | 12.0 | 2.7 | 4.5 | 10.7 | 0.4 | same |
| Q2 | 0.6 | 2.8 | 17.9 | 4.6 | 6.0 | 54.8 | 0.6 | same |
| Q3 | 0.5 | 2.2 | 20.1 | 2.9 | 4.8 | 14.2 | 0.4 | same |
| Q4 | 0.5 | 2.3 | 37.7 | 3.1 | 5.4 | 20.0 | 0.5 | same |
| Q5 | 0.7 | 15.4 | 31.8 | 141 | 10.8 | 24.9 | 0.7 | same |
| Q7 | 0.6 | 3.4 | 61.2 | 4.0 | 6.7 | 42.5 | 0.6 | same |
| Q8 | 0.6 | 2.6 | 39.7 | 3.5 | 5.6 | 37.3 | 0.6 | same |
| Q9 | 0.2 | 1.1 | skipped | 1.4 | 4.2 | skipped | 0.2 | bytes (DESCRIBE/CONSTRUCT), not compared |
| Q10 | 0.6 | 2.2 | 94.6 | 2.9 | 5.6 | 18.5 | 0.6 | same |
| Q11 | 0.3 | 1.5 | 6.1 | 2.4 | 4.5 | 25.2 | 0.3 | same |
| Q12 | 0.3 | 1.4 | skipped | 2.0 | 5.1 | skipped | 0.4 | bytes (DESCRIBE/CONSTRUCT), not compared |

### bi: AQET per template (ms), average result count

| query | tripletrail | oxigraph | qlever | jena | graphdb | maplib | tripletrail-1t | results |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| Q1 | 1.2 | 87.9 | 10.8 | 181 | 21.5 | 20.0 | 1.2 | same |
| Q2 | 0.9 | 2187 | 37.5 | 376 | 243 | 15.2 | 0.9 | same |
| Q3 | 8.2 | 319 | 12.2 | 141 | 30.0 | 21.1 | 8.2 | same |
| Q4 | 11.2 | 67.5 | 41.6 | 64.8 | 84.4 | 23.5 | 11.3 | same |
| Q5 | 1.2 | 6.8 | 12.1 | 6.4 | 6.8 | skipped | 1.2 | same |
| Q6 | 4.2 | 27.3 | 27.0 | 13.9 | 23.1 | 45.3 | 4.3 | same |
| Q7 | 0.5 | 355 | 7.3 | 3.6 | 3.7 | 13.8 | 0.5 | same |
| Q8 | 1.5 | 9.4 | 11.8 | 8.2 | 7.8 | 20.4 | 1.5 | same |

## bsbm-28480 (28,480 products, 9,609,918 triples)

50 timed query mixes after 10 warm-up mixes.

| | tripletrail | oxigraph | qlever | jena | graphdb | maplib | tripletrail-1t |
|---|---:|---:|---:|---:|---:|---:|---:|
| load (s) | 5.939 | 13.163 | 13.817 | 41.806 | 49.505 | 4.353 | 5.933 |
| QMpH explore | 156,279 | 13,243 | 4,580 * | 2,003 | 18,231 | 3,342 * | 149,766 |
| QMpH bi | 34,511 | 52 | 3,532 | 211 | 611 | 9,497 * | 24,788 |
| QMpH update | 99,847 | 12,596 | n/a | 1,760 | 9,730 | 715 * | 99,846 |

\* maplib: BI Q5 skipped: maplib 0.22.0 rejects GROUP BY on a variable its subquery does not bind
\* maplib: explore-and-update: Q9 (DESCRIBE) and Q12 (CONSTRUCT) skipped: the test driver asks for RDF/XML, which the maplib endpoint does not serve
\* maplib: explore: Q9 (DESCRIBE) and Q12 (CONSTRUCT) skipped: the test driver asks for RDF/XML, which the maplib endpoint does not serve
\* qlever: explore: Q9 (DESCRIBE) and Q12 (CONSTRUCT) skipped: the test driver asks for RDF/XML, which QLever does not serve

### explore: AQET per template (ms), average result count

| query | tripletrail | oxigraph | qlever | jena | graphdb | maplib | tripletrail-1t | results |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| Q1 | 0.4 | 5.7 | 12.2 | 2.7 | 4.2 | 80.8 | 0.5 | same |
| Q2 | 0.7 | 3.0 | 17.9 | 4.4 | 5.3 | 53.6 | 0.7 | same |
| Q3 | 0.5 | 8.2 | 20.0 | 2.8 | 4.8 | 84.2 | 0.5 | same |
| Q4 | 0.6 | 7.4 | 46.7 | 3.6 | 5.3 | 162 | 0.6 | same |
| Q5 | 2.5 | 94.1 | 18.2 | 856 | 35.0 | 24.2 | 2.7 | same |
| Q7 | 0.7 | 3.6 | 66.1 | 4.0 | 6.1 | 53.1 | 0.8 | same |
| Q8 | 0.6 | 2.8 | 40.4 | 3.0 | 5.1 | 34.8 | 0.6 | same |
| Q9 | 0.2 | 1.2 | skipped | 1.5 | 3.8 | skipped | 0.3 | bytes (DESCRIBE/CONSTRUCT), not compared |
| Q10 | 0.7 | 2.7 | 100 | 2.5 | 5.0 | 26.4 | 0.7 | same |
| Q11 | 0.3 | 1.6 | 6.0 | 2.0 | 4.2 | 31.7 | 0.4 | same |
| Q12 | 0.3 | 1.4 | skipped | 2.2 | 4.9 | skipped | 0.3 | bytes (DESCRIBE/CONSTRUCT), not compared |

### bi: AQET per template (ms), average result count

| query | tripletrail | oxigraph | qlever | jena | graphdb | maplib | tripletrail-1t | results |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| Q1 | 7.5 | 1038 | 28.4 | 6095 | 134 | 30.7 | 11.5 | same |
| Q2 | 1.9 | 25551 | 313 | 4521 | 2603 | 21.1 | 1.9 | same |
| Q3 | 38.5 | 4383 | 47.9 | 1621 | 240 | 34.1 | 73.0 | same |
| Q4 | 23.8 | 149 | 86.6 | 161 | 168 | 26.3 | 24.1 | same |
| Q5 | 1.7 | 12.6 | 16.8 | 10.5 | 8.8 | skipped | 1.7 | same |
| Q6 | 4.7 | 32.2 | 30.2 | 16.1 | 22.2 | 46.5 | 4.9 | same |
| Q7 | 0.6 | 5979 | 16.1 | 5.6 | 3.7 | 14.4 | 0.6 | same |
| Q8 | 2.2 | 13.3 | 17.2 | 13.8 | 10.2 | 21.9 | 2.2 | same |
