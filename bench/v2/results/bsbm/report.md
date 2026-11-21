# BSBM results

Berlin SPARQL Benchmark with the official bsbmtools 0.2 test driver (seed 808080, single client). QMpH = query mixes per hour (higher is better); per-template times are AQET in ms (lower is better), measured at the client. A result-count column that differs between engines marks a template where an engine answers differently.

## bsbm-2785 (2,785 products, 952,930 triples)

50 timed query mixes after 10 warm-up mixes.

| | tripletrail | oxigraph | qlever | jena | graphdb | maplib |
|---|---:|---:|---:|---:|---:|---:|
| load (s) | 1.16 | 4.435 | 2.376 | 5.757 | 12.745 | 2.517 |
| QMpH explore | 70,405 | 34,195 | 4,483 * | 9,273 | 27,001 | 10,622 * |
| QMpH bi | 30,145 | 651 | 11,293 | 3,001 | 4,661 | 16,318 * † |
| QMpH update | 42,228 | 30,660 | n/a | 6,094 | 11,691 | 1,212 * |

\* maplib: BI Q5 skipped: maplib 0.22.0 rejects GROUP BY on a variable its subquery does not bind
\* maplib: explore-and-update: Q9 (DESCRIBE) and Q12 (CONSTRUCT) skipped: the test driver asks for RDF/XML, which the maplib endpoint does not serve
\* maplib: explore: Q9 (DESCRIBE) and Q12 (CONSTRUCT) skipped: the test driver asks for RDF/XML, which the maplib endpoint does not serve
\* qlever: explore: Q9 (DESCRIBE) and Q12 (CONSTRUCT) skipped: the test driver asks for RDF/XML, which QLever does not serve
† maplib: bi result counts differ from the other engines on Q7, Q8, so this QMpH includes wrong answers (maplib 0.20.26 (fixed in 0.22.0) returns one all-unbound row for a GROUP BY over no solutions (SPARQL: no rows), e.g. for a product type without products)

### explore: AQET per template (ms), average result count

| query | tripletrail | oxigraph | qlever | jena | graphdb | maplib | results |
|---|---:|---:|---:|---:|---:|---:|---|
| Q1 | 1.2 | 2.0 | 12.5 | 3.2 | 3.7 | 7.8 | same |
| Q2 | 2.1 | 3.0 | 24.0 | 5.1 | 5.0 | 24.9 | same |
| Q3 | 1.4 | 2.5 | 23.8 | 3.5 | 3.9 | 8.1 | same |
| Q4 | 1.5 | 2.5 | 46.8 | 3.6 | 4.3 | 7.8 | same |
| Q5 | 2.1 | 17.8 | 36.0 | 147 | 9.0 | 15.5 | same |
| Q7 | 1.7 | 3.6 | 59.6 | 4.4 | 5.2 | 14.1 | same |
| Q8 | 2.8 | 2.9 | 39.1 | 4.1 | 4.6 | 16.6 | same |
| Q9 | 0.5 | 1.2 | skipped | 1.3 | 3.4 | skipped | bytes (DESCRIBE/CONSTRUCT), not compared |
| Q10 | 1.5 | 2.5 | 83.8 | 3.4 | 4.6 | 9.7 | same |
| Q11 | 0.9 | 1.5 | 7.6 | 2.8 | 5.6 | 15.4 | same |
| Q12 | 1.0 | 1.5 | skipped | 1.9 | 4.2 | skipped | bytes (DESCRIBE/CONSTRUCT), not compared |

### bi: AQET per template (ms), average result count

| query | tripletrail | oxigraph | qlever | jena | graphdb | maplib | results |
|---|---:|---:|---:|---:|---:|---:|---|
| Q1 | 3.7 | 85.7 | 9.4 | 185 | 25.6 | 19.1 | same |
| Q2 | 2.8 | 2118 | 39.9 | 357 | 256 | 21.7 | same |
| Q3 | 19.5 | 317 | 10.6 | 135 | 33.8 | 19.8 | same |
| Q4 | 21.5 | 68.3 | 45.4 | 63.5 | 75.2 | 21.6 | same |
| Q5 | 3.0 | 6.5 | 12.1 | 6.3 | 5.9 | skipped | same |
| Q6 | 11.2 | 27.7 | 26.1 | 14.2 | 21.5 | 19.6 | same |
| Q7 | 1.5 | 335 | 7.1 | 4.3 | 3.3 | 8.9 | tripletrail=2.26, oxigraph=2.26, qlever=2.26, jena=2.26, graphdb=2.26, maplib=3.04 |
| Q8 | 3.8 | 9.7 | 10.9 | 8.5 | 6.0 | 12.6 | tripletrail=2.6, oxigraph=2.6, qlever=2.6, jena=2.6, graphdb=2.6, maplib=3.34 |

## bsbm-28480 (28,480 products, 9,609,918 triples)

50 timed query mixes after 10 warm-up mixes.

| | tripletrail | oxigraph | qlever | jena | graphdb | maplib |
|---|---:|---:|---:|---:|---:|---:|
| load (s) | 4.866 | 11.591 | 12.315 | 40.618 | 42.178 | 29.124 |
| QMpH explore | 52,765 | 13,492 | 4,400 * | 1,859 | 20,761 | 6,746 * |
| QMpH bi | 14,131 | 53 | 3,461 | 211 | 582 | 5,346 * † |
| QMpH update | 36,273 | 13,496 | n/a | 1,606 | 10,203 | 174 * |

\* maplib: BI Q5 skipped: maplib 0.22.0 rejects GROUP BY on a variable its subquery does not bind
\* maplib: explore-and-update: Q9 (DESCRIBE) and Q12 (CONSTRUCT) skipped: the test driver asks for RDF/XML, which the maplib endpoint does not serve
\* maplib: explore: Q9 (DESCRIBE) and Q12 (CONSTRUCT) skipped: the test driver asks for RDF/XML, which the maplib endpoint does not serve
\* qlever: explore: Q9 (DESCRIBE) and Q12 (CONSTRUCT) skipped: the test driver asks for RDF/XML, which QLever does not serve
† maplib: bi result counts differ from the other engines on Q7, Q8, so this QMpH includes wrong answers (maplib 0.20.26 (fixed in 0.22.0) returns one all-unbound row for a GROUP BY over no solutions (SPARQL: no rows), e.g. for a product type without products)

### explore: AQET per template (ms), average result count

| query | tripletrail | oxigraph | qlever | jena | graphdb | maplib | results |
|---|---:|---:|---:|---:|---:|---:|---|
| Q1 | 1.4 | 5.9 | 12.9 | 2.7 | 3.8 | 21.8 | same |
| Q2 | 2.3 | 3.0 | 23.1 | 4.3 | 4.9 | 26.1 | same |
| Q3 | 1.6 | 8.1 | 24.7 | 2.8 | 4.1 | 20.7 | same |
| Q4 | 1.8 | 7.7 | 54.8 | 3.2 | 4.5 | 23.2 | same |
| Q5 | 6.6 | 91.7 | 20.2 | 927 | 30.7 | 37.7 | same |
| Q7 | 2.6 | 3.5 | 65.0 | 3.7 | 5.0 | 29.1 | same |
| Q8 | 3.1 | 2.6 | 40.5 | 2.9 | 4.4 | 25.3 | same |
| Q9 | 0.6 | 1.2 | skipped | 1.4 | 3.2 | skipped | bytes (DESCRIBE/CONSTRUCT), not compared |
| Q10 | 1.9 | 2.6 | 92.8 | 2.2 | 4.6 | 19.2 | same |
| Q11 | 1.3 | 1.5 | 7.7 | 1.7 | 3.7 | 17.7 | same |
| Q12 | 1.1 | 1.4 | skipped | 2.0 | 3.8 | skipped | bytes (DESCRIBE/CONSTRUCT), not compared |

### bi: AQET per template (ms), average result count

| query | tripletrail | oxigraph | qlever | jena | graphdb | maplib | results |
|---|---:|---:|---:|---:|---:|---:|---|
| Q1 | 29.5 | 992 | 29.1 | 6852 | 135 | 78.4 | same |
| Q2 | 10.9 | 25526 | 323 | 4186 | 2753 | 150 | same |
| Q3 | 93.9 | 4223 | 48.8 | 1573 | 236 | 75.1 | same |
| Q4 | 37.4 | 150 | 86.8 | 158 | 163 | 50.9 | same |
| Q5 | 3.6 | 11.2 | 16.1 | 10.3 | 8.6 | skipped | same |
| Q6 | 11.4 | 31.4 | 30.2 | 15.8 | 22.4 | 25.9 | same |
| Q7 | 1.7 | 5964 | 16.1 | 5.6 | 3.8 | 11.0 | tripletrail=2.76, oxigraph=2.76, qlever=2.76, jena=2.76, graphdb=2.76, maplib=3.54 |
| Q8 | 4.9 | 14.5 | 18.2 | 13.4 | 9.0 | 34.1 | tripletrail=2.6, oxigraph=2.6, qlever=2.6, jena=2.6, graphdb=2.6, maplib=3.34 |
