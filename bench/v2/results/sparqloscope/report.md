# Sparqloscope results

One cold run per query after an engine restart (QLever's cache cleared before each query), at the client, HTTP included. Failed and timed-out queries count as 2 x the timeout in the geometric means, as on the QLever evaluation site. Engines whose result sizes differ from the majority are listed per query in the last section.

## bsbm-2785 (102 queries)

| | tripletrail | oxigraph | qlever | jena | graphdb | maplib |
|---|---:|---:|---:|---:|---:|---:|
| load (s) | 1.147 | 1.709 | 2.392 | 5.956 | 12.942 | 2.512 |
| answered | 102 | 101 | 102 | 102 | 102 | 102 |
| failed | 0 | 0 | 0 | 0 | 0 | 0 |
| timed out | 0 | 1 | 0 | 0 | 0 | 0 |
| **geometric mean** | **4.9 ms** | **74.3 ms** | **14.2 ms** | **108.9 ms** | **81.1 ms** | **11.9 ms** |
| join | 5.0 ms | 60.6 ms | 20.4 ms | 73.7 ms | 49.6 ms | 11.5 ms |
| optional | 5.1 ms | 173.9 ms | 21.7 ms | 386.0 ms | 100.3 ms | 14.2 ms |
| minus | 4.6 ms | 86.6 ms | 16.1 ms | 122.4 ms | 52.5 ms | 8.6 ms |
| exists | 3.4 ms | 382.3 ms | 17.9 ms | 126.7 ms | 218.4 ms | 16.7 ms |
| union | 3.0 ms | 277.0 ms | 16.5 ms | 147.4 ms | 190.1 ms | 11.8 ms |
| group by / distinct | 6.9 ms | 40.9 ms | 9.7 ms | 99.8 ms | 76.9 ms | 8.4 ms |
| property path | 4.0 ms | 35.6 ms | 7.3 ms | 65.3 ms | 13.1 ms | 30.1 ms |
| regex / string | 3.9 ms | 12.5 ms | 17.7 ms | 30.8 ms | 41.9 ms | 6.7 ms |
| result size | 16.0 ms | 65.4 ms | 122.2 ms | 164.2 ms | 160.5 ms | 58.9 ms |
| numeric | 6.5 ms | 19.3 ms | 6.2 ms | 57.0 ms | 70.1 ms | 4.3 ms |
| filter / language | 1.7 ms | 169.6 ms | 6.8 ms | 62.6 ms | 56.1 ms | 4.5 ms |
| date | 13.4 ms | 32.9 ms | 7.7 ms | 85.7 ms | 113.5 ms | 11.0 ms |
| count | 2.4 ms | 520.0 ms | 4.1 ms | 575.6 ms | 265.3 ms | 51.2 ms |

<details><summary>Per query</summary>

| query | tripletrail | oxigraph | qlever | jena | graphdb | maplib |
|---|---:|---:|---:|---:|---:|---:|
| join-2-small-large | 5.0 ms | 18.9 ms | 26.3 ms | 135.6 ms | 213.2 ms | 13.0 ms |
| join-2-large-small | 3.3 ms | 7.6 ms | 17.1 ms | 17.6 ms | 25.5 ms | 7.9 ms |
| join-2-large-large | 12.0 ms | 472.7 ms | 22.3 ms | 525.7 ms | 157.2 ms | 14.0 ms |
| join-2-largest-result | 7.7 ms | 192.1 ms | 12.2 ms | 160.8 ms | 54.9 ms | 14.1 ms |
| join-2-large-large-with-large-result | 7.6 ms | 186.9 ms | 11.7 ms | 144.8 ms | 66.7 ms | 13.8 ms |
| join-2-large-large-with-small-result | 4.8 ms | 115.8 ms | 24.5 ms | 70.1 ms | 61.7 ms | 7.5 ms |
| join-3-star-largest-sum-of-join-sizes | 9.2 ms | 544.1 ms | 21.7 ms | 286.5 ms | 108.2 ms | 21.9 ms |
| join-3-chain-largest-sum-of-join-sizes | 6.4 ms | 352.1 ms | 19.0 ms | 193.6 ms | 62.9 ms | 13.9 ms |
| join-xlarge-star-on-small-predicates | 2.5 ms | 5.9 ms | 30.4 ms | 24.6 ms | 10.1 ms | 13.0 ms |
| join-xlarge-chain-on-small-predicates | 2.6 ms | 3.8 ms | 28.9 ms | 12.9 ms | 15.1 ms | 6.7 ms |
| optional-join-small-large | 3.1 ms | 4.2 ms | 21.0 ms | 71.2 ms | 13.2 ms | 9.6 ms |
| optional-join-large-small | 2.9 ms | 330.1 ms | 19.2 ms | 1.58 s | 221.5 ms | 13.3 ms |
| optional-join-large-large | 10.6 ms | 406.4 ms | 22.2 ms | 567.8 ms | 141.9 ms | 14.4 ms |
| optional-join-2-large-large-with-large-result | 4.4 ms | 200.4 ms | 14.6 ms | 308.1 ms | 178.5 ms | 13.3 ms |
| optional-join-2-large-large-with-small-join-result-1 | 4.7 ms | 89.5 ms | 26.4 ms | 150.4 ms | 39.1 ms | 9.5 ms |
| optional-join-2-large-large-with-small-join-result-2 | 3.4 ms | 85.2 ms | 27.5 ms | 126.0 ms | 55.5 ms | 9.5 ms |
| optional-join-3-star-1 | 13.0 ms | 690.2 ms | 28.4 ms | 830.0 ms | 205.7 ms | 37.9 ms |
| optional-join-3-star-2 | 10.6 ms | 325.2 ms | 19.5 ms | 870.4 ms | 192.2 ms | 22.2 ms |
| optional-join-3-chain-1 | 5.9 ms | 367.5 ms | 21.4 ms | 475.6 ms | 124.8 ms | 13.4 ms |
| optional-join-3-chain-2 | 2.3 ms | 352.3 ms | 20.2 ms | 571.5 ms | 129.4 ms | 13.6 ms |
| minus-join-small-large | 2.3 ms | 56.8 ms | 11.9 ms | 105.5 ms | 71.8 ms | 7.1 ms |
| minus-join-large-small | 1.7 ms | 26.4 ms | 15.3 ms | 82.3 ms | 42.5 ms | 10.0 ms |
| minus-join-large-large | 8.9 ms | 89.8 ms | 16.7 ms | 151.5 ms | 36.6 ms | 6.1 ms |
| minus-join-2-large-large-with-large-result | 2.6 ms | 66.2 ms | 10.0 ms | 91.1 ms | 54.3 ms | 6.6 ms |
| minus-join-2-large-large-with-small-join-result-1 | 4.0 ms | 18.0 ms | 14.7 ms | 42.6 ms | 13.7 ms | 6.2 ms |
| minus-join-2-large-large-with-small-join-result-2 | 3.7 ms | 16.3 ms | 15.4 ms | 41.0 ms | 27.7 ms | 7.4 ms |
| minus-join-3-star-1 | 16.1 ms | 448.3 ms | 24.2 ms | 429.7 ms | 99.9 ms | 13.6 ms |
| minus-join-3-star-2 | 10.9 ms | 265.9 ms | 24.5 ms | 317.5 ms | 79.4 ms | 14.1 ms |
| minus-join-3-chain-1 | 4.8 ms | 261.3 ms | 18.8 ms | 141.7 ms | 95.5 ms | 9.5 ms |
| minus-join-3-chain-2 | 4.0 ms | 292.8 ms | 14.9 ms | 186.7 ms | 90.7 ms | 9.5 ms |
| exists-join-small-large | 1.5 ms | 4.7 ms | 9.4 ms | 27.0 ms | 40.3 ms | 12.8 ms |
| exists-join-large-small | 1.6 ms | 333.0 ms | 16.3 ms | 182.2 ms | 335.8 ms | 8.3 ms |
| exists-join-large-large | 8.4 ms | 407.1 ms | 22.4 ms | 211.9 ms | 513.6 ms | 22.8 ms |
| exists-join-2-large-large-with-large-result | 2.2 ms | 176.8 ms | 11.9 ms | 143.1 ms | 274.4 ms | 22.2 ms |
| exists-join-2-large-large-with-small-join-result-1 | 1.6 ms | 117.5 ms | 16.5 ms | 47.6 ms | 63.5 ms | 13.9 ms |
| exists-join-2-large-large-with-small-join-result-2 | 3.4 ms | 99.7 ms | 15.5 ms | 46.5 ms | 89.8 ms | 9.8 ms |
| exists-join-3-star-1 | 15.3 ms | 652.5 ms | 25.3 ms | 297.1 ms | 280.8 ms | 18.6 ms |
| exists-join-3-star-2 | 8.2 ms | 647.2 ms | 25.4 ms | 293.3 ms | 353.2 ms | 22.0 ms |
| exists-join-3-chain-1 | 2.6 ms | 330.2 ms | 22.2 ms | 195.0 ms | 459.6 ms | 24.8 ms |
| exists-join-3-chain-2 | 2.5 ms | timeout | 22.2 ms | 189.7 ms | 496.6 ms | 22.0 ms |
| union-no-constraint | 1.1 ms | 83.7 ms | 7.4 ms | 88.3 ms | 124.4 ms | 13.4 ms |
| union-constraint-from-star | 4.7 ms | 383.9 ms | 15.9 ms | 307.8 ms | 329.1 ms | 13.3 ms |
| union-constraint-small-join | 4.0 ms | 207.2 ms | 43.3 ms | 103.0 ms | 131.6 ms | 9.7 ms |
| union-constraint-large-join | 10.2 ms | 370.3 ms | 16.6 ms | 313.3 ms | 307.8 ms | 22.1 ms |
| union-constraint-filter-restrictive | 1.1 ms | 661.6 ms | 14.4 ms | 79.2 ms | 149.6 ms | 6.0 ms |
| multicolumn-join-small | 1.1 ms | 8.0 ms | 16.0 ms | 10.3 ms | 9.5 ms | 7.1 ms |
| multicolumn-join-large | 9.8 ms | 249.1 ms | 25.1 ms | 70.0 ms | 117.2 ms | 13.1 ms |
| group-by-count-object-high-multiplicity | 1.5 ms | 19.5 ms | 8.2 ms | 147.5 ms | 72.4 ms | 8.0 ms |
| group-by-count-object-low-multiplicity | 7.6 ms | 52.8 ms | 9.2 ms | 845.7 ms | 178.1 ms | 14.9 ms |
| group-by-count-object-wrong-sort-order | 9.9 ms | 249.9 ms | 19.4 ms | 194.0 ms | 88.5 ms | 9.8 ms |
| group-by-complex-aggregate | 58.7 ms | 423.5 ms | 22.7 ms | 212.1 ms | 326.2 ms | 14.7 ms |
| group-by-implicit-numeric-baseline | 2.4 ms | 17.0 ms | 6.4 ms | 53.6 ms | 30.0 ms | 6.8 ms |
| group-by-implicit-numeric-sum | 6.0 ms | 17.2 ms | 7.3 ms | 57.7 ms | 126.8 ms | 5.2 ms |
| group-by-implicit-numeric-min | 5.5 ms | 16.6 ms | 6.8 ms | 47.9 ms | 46.2 ms | 6.7 ms |
| group-by-implicit-numeric-max | 4.9 ms | 16.5 ms | 6.7 ms | 39.8 ms | 34.1 ms | 5.5 ms |
| group-by-implicit-numeric-avg | 18.6 ms | 17.3 ms | 7.2 ms | 48.9 ms | 60.0 ms | 5.8 ms |
| group-by-implicit-string-baseline | 2.0 ms | 10.2 ms | 5.1 ms | 356.3 ms | 16.7 ms | 4.9 ms |
| group-by-implicit-string-min | 3.7 ms | 53.6 ms | 5.8 ms | 68.1 ms | 121.1 ms | 4.7 ms |
| group-by-implicit-string-max | 4.1 ms | 51.3 ms | 5.8 ms | 41.8 ms | 132.2 ms | 4.5 ms |
| group-by-string-groupconcat | 51.4 ms | 157.8 ms | 116.5 ms | 137.5 ms | 273.1 ms | 39.7 ms |
| distinct-count-object-high-multiplicity | 5.1 ms | 16.9 ms | 5.9 ms | 55.1 ms | 38.7 ms | 9.3 ms |
| distinct-count-object-low-multiplicity | 5.1 ms | 20.9 ms | 8.4 ms | 61.8 ms | 39.7 ms | 9.1 ms |
| distinct-count-object-wrong-sort-order | 15.5 ms | 254.9 ms | 12.0 ms | 139.0 ms | 99.3 ms | 13.5 ms |
| transitive-path-plus | 2.4 ms | 6.5 ms | 6.7 ms | 36.7 ms | 13.0 ms | 11.4 ms |
| transitive-path-plus-fixed-subject | 2.3 ms | 2.7 ms | 6.1 ms | 8.0 ms | 7.4 ms | 11.6 ms |
| transitive-path-large-join-and-plus | 7.4 ms | 302.8 ms | 8.2 ms | 279.0 ms | 17.4 ms | 80.4 ms |
| transitive-path-small-join-and-plus | 6.0 ms | 299.3 ms | 8.4 ms | 221.6 ms | 17.8 ms | 78.1 ms |
| regex-3-contains | 4.9 ms | 15.2 ms | 23.8 ms | 132.2 ms | 64.6 ms | 6.6 ms |
| regex-3-fixed | 5.0 ms | 14.7 ms | 24.3 ms | 27.9 ms | 54.4 ms | 7.5 ms |
| regex-3 | 5.0 ms | 12.2 ms | 24.0 ms | 20.8 ms | 33.0 ms | 9.4 ms |
| regex-prefix-1 | 2.9 ms | 11.7 ms | 5.5 ms | 22.9 ms | 53.5 ms | 7.1 ms |
| regex-prefix-2 | 2.8 ms | 11.7 ms | 5.4 ms | 19.4 ms | 29.3 ms | 7.1 ms |
| regex-prefix-3 | 4.0 ms | 11.8 ms | 5.2 ms | 20.3 ms | 28.6 ms | 5.3 ms |
| strlen | 3.5 ms | 11.7 ms | 23.0 ms | 21.7 ms | 28.8 ms | 6.7 ms |
| strbefore | 4.0 ms | 12.5 ms | 24.6 ms | 34.8 ms | 47.4 ms | 6.8 ms |
| strafter | 4.2 ms | 12.4 ms | 51.4 ms | 35.9 ms | 43.6 ms | 6.9 ms |
| strstarts | 3.7 ms | 11.9 ms | 38.3 ms | 38.7 ms | 41.9 ms | 5.5 ms |
| strends | 3.5 ms | 12.0 ms | 22.8 ms | 32.7 ms | 54.5 ms | 5.7 ms |
| result-size-tiny | 1.1 ms | 2.3 ms | 4.4 ms | 13.0 ms | 9.7 ms | 4.4 ms |
| result-size-small | 1.6 ms | 6.9 ms | 13.6 ms | 36.8 ms | 35.1 ms | 11.1 ms |
| result-size-medium | 65.2 ms | 418.1 ms | 735.7 ms | 648.6 ms | 756.6 ms | 275.9 ms |
| result-size-large | 93.7 ms | 447.6 ms | 765.6 ms | 659.7 ms | 649.2 ms | 241.2 ms |
| result-size-xlarge | 94.8 ms | 403.5 ms | 812.3 ms | 585.4 ms | 639.3 ms | 216.6 ms |
| numeric-baseline | 5.9 ms | 18.1 ms | 4.9 ms | 56.1 ms | 72.7 ms | 4.7 ms |
| numeric-abs | 3.7 ms | 31.7 ms | 6.6 ms | 64.1 ms | 80.6 ms | 4.9 ms |
| numeric-ceil | 5.5 ms | 17.1 ms | 5.7 ms | 55.8 ms | 59.3 ms | 3.3 ms |
| numeric-floor | 5.2 ms | 17.2 ms | 6.5 ms | 48.8 ms | 59.3 ms | 4.0 ms |
| numeric-round | 5.3 ms | 17.6 ms | 6.7 ms | 49.6 ms | 87.1 ms | 4.7 ms |
| numeric-add | 7.2 ms | 19.1 ms | 6.2 ms | 58.9 ms | 94.0 ms | 4.0 ms |
| numeric-greater | 19.7 ms | 17.5 ms | 7.3 ms | 68.1 ms | 49.6 ms | 4.5 ms |
| filter-few-results | 1.3 ms | 277.4 ms | 7.7 ms | 27.0 ms | 75.5 ms | 3.2 ms |
| filter-many-results | 1.1 ms | 316.2 ms | 9.6 ms | 140.4 ms | 64.3 ms | 7.9 ms |
| filter-language-en | 3.1 ms | 55.6 ms | 4.3 ms | 64.9 ms | 36.4 ms | 3.5 ms |
| date-year | 12.5 ms | 34.5 ms | 8.0 ms | 99.9 ms | 149.2 ms | 11.5 ms |
| date-month | 13.8 ms | 32.0 ms | 7.4 ms | 94.6 ms | 127.9 ms | 10.7 ms |
| date-day | 13.8 ms | 32.3 ms | 7.6 ms | 66.6 ms | 76.7 ms | 10.7 ms |
| number-of-triples | 2.4 ms | 269.9 ms | 2.7 ms | 371.5 ms | 258.1 ms | 36.8 ms |
| number-of-subjects | 3.3 ms | 325.5 ms | 2.4 ms | 430.1 ms | 302.3 ms | 73.6 ms |
| number-of-predicates | 2.1 ms | 325.4 ms | 2.4 ms | 367.2 ms | 277.4 ms | 75.6 ms |
| number-of-objects | 2.1 ms | 341.8 ms | 2.4 ms | 2.40 s | 293.5 ms | 273.8 ms |
| number-of-literals | 2.3 ms | 1.32 s | 30.5 ms | 698.0 ms | 304.5 ms | 41.3 ms |
| number-of-blank-nodes | 2.2 ms | 1.53 s | 4.2 ms | 370.7 ms | 180.4 ms | 7.8 ms |

</details>

Queries where engines disagree (row count, or the value of a one-row answer):

- union-constraint-filter-restrictive: graphdb differ (graphdb: ['181781']; majority: ['89'])
- group-by-string-groupconcat: maplib differ (maplib: ['134440']; majority: ['2487830'])
- regex-prefix-1: qlever differ (qlever: ['669']; majority: ['0'])
- regex-prefix-2: qlever differ (qlever: ['259']; majority: ['0'])
- regex-prefix-3: qlever differ (qlever: ['54']; majority: ['0'])
- strbefore: maplib differ (maplib: ['62304']; majority: ['34911'])
- strafter: maplib differ (maplib: ['99476']; majority: ['72083'])
- numeric-greater: qlever, maplib differ (qlever: ['53840'], maplib: ['53840']; majority: ['None'])

## rinf-0076 (102 queries)

| | tripletrail | oxigraph | qlever | jena | graphdb | maplib |
|---|---:|---:|---:|---:|---:|---:|
| load (s) | 1.14 | 2.797 | 3.338 | 10.509 | 16.443 | 5.158 |
| answered | 102 | 101 | 102 | 102 | 102 | 102 |
| failed | 0 | 0 | 0 | 0 | 0 | 0 |
| timed out | 0 | 1 | 0 | 0 | 0 | 0 |
| **geometric mean** | **6.9 ms** | **107.8 ms** | **24.1 ms** | **118.4 ms** | **92.5 ms** | **16.2 ms** |
| join | 6.9 ms | 88.6 ms | 42.1 ms | 76.8 ms | 58.0 ms | 17.1 ms |
| optional | 10.8 ms | 454.7 ms | 33.3 ms | 537.0 ms | 191.8 ms | 24.8 ms |
| minus | 10.6 ms | 232.5 ms | 31.2 ms | 193.0 ms | 79.6 ms | 13.9 ms |
| exists | 10.5 ms | 824.3 ms | 25.3 ms | 258.1 ms | 347.7 ms | 22.9 ms |
| union | 7.2 ms | 609.4 ms | 23.7 ms | 255.9 ms | 156.0 ms | 20.9 ms |
| group by / distinct | 7.8 ms | 23.4 ms | 11.5 ms | 62.3 ms | 43.7 ms | 7.5 ms |
| property path | 9.7 ms | 59.0 ms | 47.9 ms | 86.5 ms | 56.2 ms | 82.0 ms |
| regex / string | 9.9 ms | 71.7 ms | 64.6 ms | 77.9 ms | 171.2 ms | 14.7 ms |
| result size | 42.8 ms | 136.8 ms | 275.1 ms | 277.9 ms | 224.2 ms | 130.6 ms |
| numeric | 1.7 ms | 3.1 ms | 6.2 ms | 7.3 ms | 9.8 ms | 2.3 ms |
| filter / language | 2.4 ms | 558.1 ms | 14.7 ms | 181.0 ms | 110.0 ms | 10.1 ms |
| date | 1.2 ms | 2.4 ms | 3.8 ms | 6.7 ms | 9.2 ms | 2.3 ms |
| count | 1.2 ms | 924.1 ms | 4.5 ms | 913.0 ms | 403.3 ms | 79.8 ms |

<details><summary>Per query</summary>

| query | tripletrail | oxigraph | qlever | jena | graphdb | maplib |
|---|---:|---:|---:|---:|---:|---:|
| join-2-small-large | 5.3 ms | 33.9 ms | 42.2 ms | 143.2 ms | 215.6 ms | 10.9 ms |
| join-2-large-small | 3.3 ms | 14.0 ms | 26.6 ms | 42.5 ms | 24.8 ms | 7.1 ms |
| join-2-large-large | 21.0 ms | 458.2 ms | 28.6 ms | 469.1 ms | 140.9 ms | 21.8 ms |
| join-2-largest-result | 13.9 ms | 450.6 ms | 23.5 ms | 216.7 ms | 92.1 ms | 37.7 ms |
| join-2-large-large-with-large-result | 13.9 ms | 459.7 ms | 22.1 ms | 167.9 ms | 80.5 ms | 37.6 ms |
| join-2-large-large-with-small-result | 6.1 ms | 127.7 ms | 20.2 ms | 71.1 ms | 36.8 ms | 9.8 ms |
| join-3-star-largest-sum-of-join-sizes | 16.5 ms | 661.8 ms | 30.6 ms | 268.6 ms | 155.7 ms | 38.9 ms |
| join-3-chain-largest-sum-of-join-sizes | 18.2 ms | 598.1 ms | 44.6 ms | 290.8 ms | 152.3 ms | 22.3 ms |
| join-xlarge-star-on-small-predicates | 2.9 ms | 29.4 ms | 247.6 ms | 27.7 ms | 42.3 ms | 28.1 ms |
| join-xlarge-chain-on-small-predicates | 2.7 ms | 8.1 ms | 1.47 s | 13.4 ms | 28.1 ms | 23.8 ms |
| optional-join-small-large | 3.5 ms | 14.5 ms | 23.8 ms | 95.4 ms | 26.6 ms | 25.4 ms |
| optional-join-large-small | 3.1 ms | 2.14 s | 45.7 ms | 6.13 s | 853.2 ms | 38.2 ms |
| optional-join-large-large | 21.8 ms | 2.21 s | 47.4 ms | 1.88 s | 717.7 ms | 37.6 ms |
| optional-join-2-large-large-with-large-result | 14.6 ms | 433.4 ms | 23.0 ms | 252.4 ms | 162.1 ms | 38.5 ms |
| optional-join-2-large-large-with-small-join-result-1 | 8.0 ms | 130.8 ms | 21.0 ms | 113.7 ms | 61.2 ms | 9.6 ms |
| optional-join-2-large-large-with-small-join-result-2 | 6.6 ms | 389.2 ms | 23.2 ms | 301.4 ms | 86.6 ms | 9.4 ms |
| optional-join-3-star-1 | 23.2 ms | 1.28 s | 44.2 ms | 1.60 s | 376.1 ms | 37.6 ms |
| optional-join-3-star-2 | 15.9 ms | 502.8 ms | 33.3 ms | 828.9 ms | 311.1 ms | 21.7 ms |
| optional-join-3-chain-1 | 17.2 ms | 619.0 ms | 38.9 ms | 324.3 ms | 201.2 ms | 22.5 ms |
| optional-join-3-chain-2 | 18.6 ms | 628.4 ms | 51.3 ms | 486.5 ms | 204.3 ms | 38.4 ms |
| minus-join-small-large | 3.2 ms | 439.9 ms | 22.1 ms | 289.6 ms | 122.6 ms | 10.4 ms |
| minus-join-large-small | 3.0 ms | 137.3 ms | 48.5 ms | 238.2 ms | 141.5 ms | 22.4 ms |
| minus-join-large-large | 20.1 ms | 207.0 ms | 45.5 ms | 317.9 ms | 121.5 ms | 22.0 ms |
| minus-join-2-large-large-with-large-result | 13.8 ms | 389.0 ms | 33.0 ms | 313.0 ms | 113.4 ms | 12.9 ms |
| minus-join-2-large-large-with-small-join-result-1 | 5.9 ms | 47.7 ms | 13.4 ms | 55.9 ms | 21.6 ms | 7.7 ms |
| minus-join-2-large-large-with-small-join-result-2 | 6.0 ms | 32.0 ms | 16.0 ms | 54.7 ms | 23.3 ms | 7.5 ms |
| minus-join-3-star-1 | 26.5 ms | 526.5 ms | 38.0 ms | 196.3 ms | 80.4 ms | 21.8 ms |
| minus-join-3-star-2 | 18.1 ms | 401.2 ms | 33.4 ms | 168.0 ms | 87.3 ms | 14.9 ms |
| minus-join-3-chain-1 | 20.8 ms | 781.8 ms | 42.2 ms | 373.8 ms | 152.1 ms | 14.8 ms |
| minus-join-3-chain-2 | 18.3 ms | 375.5 ms | 46.9 ms | 277.5 ms | 79.0 ms | 14.4 ms |
| exists-join-small-large | 3.5 ms | 10.5 ms | 23.2 ms | 46.4 ms | 24.8 ms | 9.8 ms |
| exists-join-large-small | 3.2 ms | 2.12 s | 28.2 ms | 1.68 s | 2.34 s | 14.6 ms |
| exists-join-large-large | 20.7 ms | 2.16 s | 32.5 ms | 981.6 ms | 1.79 s | 22.0 ms |
| exists-join-2-large-large-with-large-result | 13.9 ms | 374.7 ms | 23.9 ms | 171.8 ms | 458.2 ms | 38.9 ms |
| exists-join-2-large-large-with-small-join-result-1 | 5.8 ms | 134.0 ms | 12.8 ms | 52.0 ms | 175.0 ms | 10.5 ms |
| exists-join-2-large-large-with-small-join-result-2 | 6.0 ms | 364.5 ms | 16.4 ms | 134.3 ms | 456.7 ms | 9.8 ms |
| exists-join-3-star-1 | 18.9 ms | 1.24 s | 50.3 ms | 565.3 ms | 274.7 ms | 45.9 ms |
| exists-join-3-star-2 | 21.5 ms | 676.3 ms | 24.2 ms | 298.2 ms | 284.9 ms | 39.9 ms |
| exists-join-3-chain-1 | 19.2 ms | 547.7 ms | 23.0 ms | 263.7 ms | 290.1 ms | 42.5 ms |
| exists-join-3-chain-2 | 19.2 ms | timeout | 36.1 ms | 320.5 ms | 299.6 ms | 39.8 ms |
| union-no-constraint | 2.6 ms | 202.9 ms | 10.4 ms | 148.0 ms | 172.6 ms | 39.2 ms |
| union-constraint-from-star | 19.6 ms | 543.8 ms | 29.6 ms | 928.2 ms | 272.2 ms | 38.0 ms |
| union-constraint-small-join | 8.2 ms | 548.9 ms | 25.1 ms | 74.8 ms | 25.0 ms | 10.1 ms |
| union-constraint-large-join | 19.1 ms | 698.7 ms | 32.6 ms | 948.3 ms | 251.4 ms | 37.7 ms |
| union-constraint-filter-restrictive | 2.5 ms | 1.99 s | 29.6 ms | 112.6 ms | 313.0 ms | 7.1 ms |
| multicolumn-join-small | 2.4 ms | 9.2 ms | 14.8 ms | 8.9 ms | 12.0 ms | 7.4 ms |
| multicolumn-join-large | 4.9 ms | 46.8 ms | 12.6 ms | 22.1 ms | 21.0 ms | 6.0 ms |
| group-by-count-object-high-multiplicity | 2.3 ms | 11.0 ms | 6.5 ms | 103.4 ms | 67.3 ms | 7.3 ms |
| group-by-count-object-low-multiplicity | 7.9 ms | 79.2 ms | 13.1 ms | 296.4 ms | 149.2 ms | 11.7 ms |
| group-by-count-object-wrong-sort-order | 12.0 ms | 180.3 ms | 24.2 ms | 142.1 ms | 51.2 ms | 11.4 ms |
| group-by-complex-aggregate | 91.9 ms | 487.5 ms | 35.7 ms | 220.0 ms | 196.3 ms | 13.2 ms |
| group-by-implicit-numeric-baseline | 2.8 ms | 3.7 ms | 7.6 ms | 12.6 ms | 9.0 ms | 4.4 ms |
| group-by-implicit-numeric-sum | 2.7 ms | 2.6 ms | 7.3 ms | 10.3 ms | 12.2 ms | 3.5 ms |
| group-by-implicit-numeric-min | 2.6 ms | 2.4 ms | 7.6 ms | 10.2 ms | 8.8 ms | 3.4 ms |
| group-by-implicit-numeric-max | 2.4 ms | 2.3 ms | 7.6 ms | 8.4 ms | 17.3 ms | 3.3 ms |
| group-by-implicit-numeric-avg | 2.8 ms | 2.3 ms | 7.5 ms | 18.9 ms | 12.0 ms | 3.5 ms |
| group-by-implicit-string-baseline | 2.5 ms | 20.9 ms | 5.0 ms | 734.5 ms | 40.8 ms | 7.0 ms |
| group-by-implicit-string-min | 45.0 ms | 64.9 ms | 6.9 ms | 138.4 ms | 164.8 ms | 6.0 ms |
| group-by-implicit-string-max | 53.8 ms | 79.9 ms | 7.0 ms | 104.2 ms | 108.3 ms | 5.7 ms |
| group-by-string-groupconcat | 63.8 ms | 131.9 ms | 189.9 ms | 173.3 ms | 225.0 ms | 69.6 ms |
| distinct-count-object-high-multiplicity | 4.2 ms | 11.1 ms | 5.4 ms | 16.9 ms | 24.1 ms | 8.0 ms |
| distinct-count-object-low-multiplicity | 3.7 ms | 28.5 ms | 9.6 ms | 79.1 ms | 32.0 ms | 7.0 ms |
| distinct-count-object-wrong-sort-order | 10.8 ms | 180.8 ms | 21.1 ms | 103.0 ms | 69.7 ms | 13.3 ms |
| transitive-path-plus | 15.7 ms | 149.0 ms | 121.2 ms | 377.3 ms | 117.4 ms | 73.0 ms |
| transitive-path-plus-fixed-subject | 2.5 ms | 2.7 ms | 6.5 ms | 6.5 ms | 8.1 ms | 65.9 ms |
| transitive-path-large-join-and-plus | 14.8 ms | 193.7 ms | 87.7 ms | 169.5 ms | 116.3 ms | 112.2 ms |
| transitive-path-small-join-and-plus | 15.4 ms | 153.7 ms | 75.9 ms | 133.9 ms | 90.4 ms | 84.0 ms |
| regex-3-contains | 6.8 ms | 68.9 ms | 152.3 ms | 74.5 ms | 179.0 ms | 13.7 ms |
| regex-3-fixed | 11.0 ms | 63.0 ms | 155.2 ms | 93.6 ms | 189.3 ms | 13.3 ms |
| regex-3 | 11.4 ms | 65.3 ms | 184.1 ms | 65.3 ms | 181.4 ms | 13.2 ms |
| regex-prefix-1 | 6.9 ms | 62.8 ms | 6.6 ms | 68.8 ms | 198.3 ms | 13.2 ms |
| regex-prefix-2 | 9.1 ms | 63.5 ms | 5.9 ms | 59.5 ms | 189.2 ms | 12.6 ms |
| regex-prefix-3 | 7.0 ms | 92.6 ms | 4.4 ms | 61.2 ms | 170.7 ms | 7.2 ms |
| strlen | 11.4 ms | 91.3 ms | 156.5 ms | 66.9 ms | 144.3 ms | 20.4 ms |
| strbefore | 13.8 ms | 66.2 ms | 189.4 ms | 84.4 ms | 191.6 ms | 21.2 ms |
| strafter | 14.3 ms | 67.5 ms | 161.6 ms | 80.6 ms | 141.1 ms | 21.1 ms |
| strstarts | 10.7 ms | 63.8 ms | 151.6 ms | 123.0 ms | 145.2 ms | 21.0 ms |
| strends | 10.3 ms | 95.2 ms | 151.7 ms | 100.6 ms | 165.7 ms | 13.0 ms |
| result-size-tiny | 2.6 ms | 2.8 ms | 7.2 ms | 6.6 ms | 6.4 ms | 3.9 ms |
| result-size-small | 4.1 ms | 6.5 ms | 14.3 ms | 25.0 ms | 18.3 ms | 18.6 ms |
| result-size-medium | 91.7 ms | 456.6 ms | 873.3 ms | 729.4 ms | 507.3 ms | 317.8 ms |
| result-size-large | 380.8 ms | 2.42 s | 4.19 s | 3.70 s | 3.08 s | 1.31 s |
| result-size-xlarge | 382.2 ms | 2.38 s | 4.15 s | 3.75 s | 3.11 s | 1.28 s |
| numeric-baseline | 2.2 ms | 6.6 ms | 7.5 ms | 7.9 ms | 11.2 ms | 2.8 ms |
| numeric-abs | 2.1 ms | 3.3 ms | 6.8 ms | 10.4 ms | 14.0 ms | 2.8 ms |
| numeric-ceil | 1.6 ms | 4.1 ms | 6.1 ms | 6.5 ms | 8.4 ms | 2.1 ms |
| numeric-floor | 1.3 ms | 1.7 ms | 6.1 ms | 6.6 ms | 7.8 ms | 1.9 ms |
| numeric-round | 1.5 ms | 3.0 ms | 6.0 ms | 5.9 ms | 7.8 ms | 2.1 ms |
| numeric-add | 1.5 ms | 2.4 ms | 5.0 ms | 6.7 ms | 13.8 ms | 2.1 ms |
| numeric-greater | 1.7 ms | 2.4 ms | 6.1 ms | 8.1 ms | 7.9 ms | 2.2 ms |
| filter-few-results | 1.3 ms | 1.60 s | 17.2 ms | 70.3 ms | 178.8 ms | 3.8 ms |
| filter-many-results | 1.6 ms | 1.64 s | 43.5 ms | 682.8 ms | 127.6 ms | 22.5 ms |
| filter-language-en | 7.4 ms | 66.5 ms | 4.2 ms | 123.6 ms | 58.3 ms | 12.2 ms |
| date-year | 1.3 ms | 2.6 ms | 3.6 ms | 9.8 ms | 7.4 ms | 2.5 ms |
| date-month | 1.2 ms | 2.3 ms | 3.9 ms | 5.5 ms | 11.1 ms | 2.3 ms |
| date-day | 1.2 ms | 2.2 ms | 3.9 ms | 5.5 ms | 9.3 ms | 2.3 ms |
| number-of-triples | 1.2 ms | 457.3 ms | 3.2 ms | 755.7 ms | 414.1 ms | 76.7 ms |
| number-of-subjects | 1.2 ms | 587.9 ms | 3.3 ms | 909.7 ms | 466.4 ms | 131.4 ms |
| number-of-predicates | 1.1 ms | 503.5 ms | 3.2 ms | 556.1 ms | 426.3 ms | 80.6 ms |
| number-of-objects | 1.1 ms | 639.8 ms | 3.1 ms | 2.24 s | 481.3 ms | 482.8 ms |
| number-of-literals | 1.1 ms | 2.86 s | 17.4 ms | 1.01 s | 372.1 ms | 43.7 ms |
| number-of-blank-nodes | 1.2 ms | 2.52 s | 4.6 ms | 672.6 ms | 291.8 ms | 15.1 ms |

</details>

Queries where engines disagree (row count, or the value of a one-row answer):

- union-constraint-filter-restrictive: graphdb differ (graphdb: ['598471']; majority: ['0'])
- group-by-complex-aggregate: no majority (tripletrail: ['http://publications.europa.eu/resource/authority/country/NOR', '117377', 'http, oxigraph: ['http://publications.europa.eu/resource/authority/country/NOR', '117377', 'http, qlever: ['http://publications.europa.eu/resource/authority/country/NOR', '117377', 'http, jena: ['http://publications.europa.eu/resource/authority/country/NOR', '117377', 'http, graphdb: ['http://publications.europa.eu/resource/authority/country/NOR', '117377', 'http, maplib: ['https://data.banenor.no/data/_undercrossing_fff650d8-d253-409e-aef6-a370644cc2)
- group-by-implicit-string-min: qlever, maplib differ (qlever: ['-1'], maplib: ['None']; majority: ['"466,885 ""Snarvei"""'])
- group-by-implicit-string-max: no majority (tripletrail: ['Landsomfattende LPS - korrigert fra associated positioning system'], oxigraph: ['Øysteinstul track 2 (SP2-O)'], qlever: ['YTTERHEI'], jena: ['Landsomfattende LPS - korrigert fra associated positioning system'], graphdb: ['Landsomfattende LPS - korrigert fra associated positioning system'], maplib: ['None'])
- group-by-string-groupconcat: maplib differ (maplib: ['732627']; majority: ['849533'])
- transitive-path-small-join-and-plus: maplib differ (maplib: ['5076']; majority: ['20057'])
- strbefore: maplib differ (maplib: ['582964']; majority: ['92299'])
- strafter: maplib differ (maplib: ['707557']; majority: ['216892'])
- numeric-greater: qlever, maplib differ (qlever: ['958'], maplib: ['958']; majority: ['None'])
- number-of-objects: qlever differ (qlever: ['467289']; majority: ['467302'])
- number-of-literals: qlever differ (qlever: ['281721']; majority: ['311870'])
