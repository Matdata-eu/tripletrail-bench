# BSBM results

Berlin SPARQL Benchmark with the official bsbmtools 0.2 test driver (seed 808080, single client). QMpH = query mixes per hour (higher is better); per-template times are AQET in ms (lower is better), measured at the client. A result-count column that differs between engines marks a template where an engine answers differently.

## bsbm-2785 (2,785 products, 952,930 triples)

50 timed query mixes after 10 warm-up mixes.

| | tripletrail | oxigraph | qlever | jena | graphdb | maplib |
|---|---:|---:|---:|---:|---:|---:|
| load (s) | 1.152 | 4.706 | 2.394 | 6.213 | 13.478 | 0.477 |
| QMpH explore | 66,438 | 37,380 | 4,661 * | 9,749 | 22,448 | 4,839 * |
| QMpH bi | 29,920 | 631 | 11,255 | 2,907 | 4,735 | 10,817 * |
| QMpH update | 45,454 | 29,194 | n/a | 5,808 | 12,641 | 2,073 * |

\* maplib: BI Q5 skipped: maplib 0.22.0 rejects GROUP BY on a variable its subquery does not bind
\* maplib: explore-and-update: Q9 (DESCRIBE) and Q12 (CONSTRUCT) skipped: the test driver asks for RDF/XML, which the maplib endpoint does not serve
\* maplib: explore: Q9 (DESCRIBE) and Q12 (CONSTRUCT) skipped: the test driver asks for RDF/XML, which the maplib endpoint does not serve
\* qlever: explore: Q9 (DESCRIBE) and Q12 (CONSTRUCT) skipped: the test driver asks for RDF/XML, which QLever does not serve

### explore: AQET per template (ms), average result count

| query | tripletrail | oxigraph | qlever | jena | graphdb | maplib | results |
|---|---:|---:|---:|---:|---:|---:|---|
| Q1 | 1.3 | 2.0 | 12.0 | 2.7 | 4.5 | 10.7 | same |
| Q2 | 2.3 | 2.8 | 17.9 | 4.6 | 6.0 | 54.8 | same |
| Q3 | 1.5 | 2.2 | 20.1 | 2.9 | 4.8 | 14.2 | same |
| Q4 | 1.6 | 2.3 | 37.7 | 3.1 | 5.4 | 20.0 | same |
| Q5 | 2.1 | 15.4 | 31.8 | 141 | 10.8 | 24.9 | same |
| Q7 | 1.8 | 3.4 | 61.2 | 4.0 | 6.7 | 42.5 | same |
| Q8 | 2.9 | 2.6 | 39.7 | 3.5 | 5.6 | 37.3 | same |
| Q9 | 0.6 | 1.1 | skipped | 1.4 | 4.2 | skipped | bytes (DESCRIBE/CONSTRUCT), not compared |
| Q10 | 1.6 | 2.2 | 94.6 | 2.9 | 5.6 | 18.5 | same |
| Q11 | 0.9 | 1.5 | 6.1 | 2.4 | 4.5 | 25.2 | same |
| Q12 | 1.1 | 1.4 | skipped | 2.0 | 5.1 | skipped | bytes (DESCRIBE/CONSTRUCT), not compared |

### bi: AQET per template (ms), average result count

| query | tripletrail | oxigraph | qlever | jena | graphdb | maplib | results |
|---|---:|---:|---:|---:|---:|---:|---|
| Q1 | 3.6 | 87.9 | 10.8 | 181 | 21.5 | 20.0 | same |
| Q2 | 2.8 | 2187 | 37.5 | 376 | 243 | 15.2 | same |
| Q3 | 20.1 | 319 | 12.2 | 141 | 30.0 | 21.1 | same |
| Q4 | 21.4 | 67.5 | 41.6 | 64.8 | 84.4 | 23.5 | same |
| Q5 | 2.9 | 6.8 | 12.1 | 6.4 | 6.8 | skipped | same |
| Q6 | 11.2 | 27.3 | 27.0 | 13.9 | 23.1 | 45.3 | same |
| Q7 | 1.6 | 355 | 7.3 | 3.6 | 3.7 | 13.8 | same |
| Q8 | 3.9 | 9.4 | 11.8 | 8.2 | 7.8 | 20.4 | same |

## bsbm-28480 (28,480 products, 9,609,918 triples)

50 timed query mixes after 10 warm-up mixes.

| | tripletrail | oxigraph | qlever | jena | graphdb | maplib |
|---|---:|---:|---:|---:|---:|---:|
| load (s) | 4.854 | 13.163 | 13.817 | 41.806 | 49.505 | 4.353 |
| QMpH explore | 46,024 | 13,243 | 4,580 * | 2,003 | 18,231 | 3,342 * |
| QMpH bi | 13,542 | 52 | 3,532 | 211 | 611 | 9,497 * |
| QMpH update | 33,556 | 12,596 | n/a | 1,760 | 9,730 | 715 * |

\* maplib: BI Q5 skipped: maplib 0.22.0 rejects GROUP BY on a variable its subquery does not bind
\* maplib: explore-and-update: Q9 (DESCRIBE) and Q12 (CONSTRUCT) skipped: the test driver asks for RDF/XML, which the maplib endpoint does not serve
\* maplib: explore: Q9 (DESCRIBE) and Q12 (CONSTRUCT) skipped: the test driver asks for RDF/XML, which the maplib endpoint does not serve
\* qlever: explore: Q9 (DESCRIBE) and Q12 (CONSTRUCT) skipped: the test driver asks for RDF/XML, which QLever does not serve

### explore: AQET per template (ms), average result count

| query | tripletrail | oxigraph | qlever | jena | graphdb | maplib | results |
|---|---:|---:|---:|---:|---:|---:|---|
| Q1 | 1.8 | 5.7 | 12.2 | 2.7 | 4.2 | 80.8 | same |
| Q2 | 2.4 | 3.0 | 17.9 | 4.4 | 5.3 | 53.6 | same |
| Q3 | 2.2 | 8.2 | 20.0 | 2.8 | 4.8 | 84.2 | same |
| Q4 | 2.8 | 7.4 | 46.7 | 3.6 | 5.3 | 162 | same |
| Q5 | 8.4 | 94.1 | 18.2 | 856 | 35.0 | 24.2 | same |
| Q7 | 2.9 | 3.6 | 66.1 | 4.0 | 6.1 | 53.1 | same |
| Q8 | 3.5 | 2.8 | 40.4 | 3.0 | 5.1 | 34.8 | same |
| Q9 | 0.7 | 1.2 | skipped | 1.5 | 3.8 | skipped | bytes (DESCRIBE/CONSTRUCT), not compared |
| Q10 | 2.5 | 2.7 | 100 | 2.5 | 5.0 | 26.4 | same |
| Q11 | 1.5 | 1.6 | 6.0 | 2.0 | 4.2 | 31.7 | same |
| Q12 | 1.2 | 1.4 | skipped | 2.2 | 4.9 | skipped | bytes (DESCRIBE/CONSTRUCT), not compared |

### bi: AQET per template (ms), average result count

| query | tripletrail | oxigraph | qlever | jena | graphdb | maplib | results |
|---|---:|---:|---:|---:|---:|---:|---|
| Q1 | 23.4 | 1038 | 28.4 | 6095 | 134 | 30.7 | same |
| Q2 | 17.4 | 25551 | 313 | 4521 | 2603 | 21.1 | same |
| Q3 | 89.7 | 4383 | 47.9 | 1621 | 240 | 34.1 | same |
| Q4 | 35.2 | 149 | 86.6 | 161 | 168 | 26.3 | same |
| Q5 | 4.5 | 12.6 | 16.8 | 10.5 | 8.8 | skipped | same |
| Q6 | 12.6 | 32.2 | 30.2 | 16.1 | 22.2 | 46.5 | same |
| Q7 | 2.1 | 5979 | 16.1 | 5.6 | 3.7 | 14.4 | same |
| Q8 | 5.8 | 13.3 | 17.2 | 13.8 | 10.2 | 21.9 | same |
