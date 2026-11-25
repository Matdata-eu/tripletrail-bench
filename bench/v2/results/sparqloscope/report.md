# Sparqloscope results

One cold run per query after an engine restart (QLever's cache cleared before each query), at the client, HTTP included. Failed and timed-out queries count as 2 x the timeout in the geometric means, as on the QLever evaluation site. Engines whose result sizes differ from the majority are listed per query in the last section.

## bsbm-2785 (102 queries)

| | tripletrail | oxigraph | qlever | jena | graphdb | maplib |
|---|---:|---:|---:|---:|---:|---:|
| load (s) | 1.082 | 1.957 | 1.724 | 6.48 | 13.421 | 0.408 |
| answered | 102 | 101 | 102 | 102 | 102 | 102 |
| failed | 0 | 0 | 0 | 0 | 0 | 0 |
| timed out | 0 | 1 | 0 | 0 | 0 | 0 |
| **geometric mean** | **2.5 ms** | **76.4 ms** | **6.1 ms** | **106.7 ms** | **73.5 ms** | **4.8 ms** |
| join | 2.4 ms | 59.4 ms | 7.8 ms | 70.5 ms | 51.7 ms | 4.8 ms |
| optional | 2.3 ms | 177.4 ms | 8.2 ms | 389.0 ms | 112.4 ms | 4.9 ms |
| minus | 2.2 ms | 96.3 ms | 6.0 ms | 138.3 ms | 53.7 ms | 3.8 ms |
| exists | 2.5 ms | 379.4 ms | 6.6 ms | 117.3 ms | 186.6 ms | 6.7 ms |
| union | 2.5 ms | 288.6 ms | 5.9 ms | 120.2 ms | 155.6 ms | 4.1 ms |
| group by / distinct | 3.1 ms | 42.0 ms | 3.8 ms | 99.4 ms | 61.7 ms | 3.4 ms |
| property path | 1.6 ms | 30.5 ms | 3.4 ms | 62.4 ms | 12.1 ms | 9.8 ms |
| regex / string | 1.8 ms | 12.5 ms | 10.6 ms | 30.4 ms | 34.1 ms | 2.7 ms |
| result size | 13.4 ms | 65.7 ms | 82.6 ms | 163.9 ms | 148.4 ms | 29.3 ms |
| numeric | 3.8 ms | 24.9 ms | 3.0 ms | 58.5 ms | 47.9 ms | 3.5 ms |
| filter / language | 1.3 ms | 172.8 ms | 3.0 ms | 55.6 ms | 47.6 ms | 2.9 ms |
| date | 5.7 ms | 33.5 ms | 3.3 ms | 84.5 ms | 92.7 ms | 3.0 ms |
| count | 0.9 ms | 511.0 ms | 1.9 ms | 541.2 ms | 306.2 ms | 12.1 ms |

<details><summary>Per query</summary>

| query | tripletrail | oxigraph | qlever | jena | graphdb | maplib |
|---|---:|---:|---:|---:|---:|---:|
| join-2-small-large | 4.0 ms | 19.4 ms | 10.6 ms | 90.6 ms | 212.6 ms | 8.6 ms |
| join-2-large-small | 1.4 ms | 7.6 ms | 6.2 ms | 46.8 ms | 23.9 ms | 4.7 ms |
| join-2-large-large | 3.6 ms | 478.8 ms | 8.3 ms | 535.9 ms | 183.9 ms | 5.2 ms |
| join-2-largest-result | 2.7 ms | 193.0 ms | 5.1 ms | 168.9 ms | 69.8 ms | 5.6 ms |
| join-2-large-large-with-large-result | 2.6 ms | 191.2 ms | 4.8 ms | 146.3 ms | 47.4 ms | 5.3 ms |
| join-2-large-large-with-small-result | 1.9 ms | 91.6 ms | 8.1 ms | 54.8 ms | 45.2 ms | 3.0 ms |
| join-3-star-largest-sum-of-join-sizes | 3.0 ms | 558.3 ms | 8.8 ms | 313.2 ms | 100.3 ms | 7.3 ms |
| join-3-chain-largest-sum-of-join-sizes | 3.6 ms | 324.1 ms | 7.8 ms | 186.6 ms | 71.6 ms | 5.3 ms |
| join-xlarge-star-on-small-predicates | 1.1 ms | 6.6 ms | 12.4 ms | 11.9 ms | 10.9 ms | 6.5 ms |
| join-xlarge-chain-on-small-predicates | 1.2 ms | 3.3 ms | 10.6 ms | 9.8 ms | 20.5 ms | 2.6 ms |
| optional-join-small-large | 1.4 ms | 4.4 ms | 8.0 ms | 83.5 ms | 27.6 ms | 3.9 ms |
| optional-join-large-small | 1.2 ms | 338.0 ms | 7.5 ms | 1.50 s | 205.1 ms | 3.9 ms |
| optional-join-large-large | 3.6 ms | 383.2 ms | 7.2 ms | 554.7 ms | 138.0 ms | 4.4 ms |
| optional-join-2-large-large-with-large-result | 1.8 ms | 231.0 ms | 5.3 ms | 311.0 ms | 237.5 ms | 5.8 ms |
| optional-join-2-large-large-with-small-join-result-1 | 1.6 ms | 93.3 ms | 9.3 ms | 140.4 ms | 64.2 ms | 3.1 ms |
| optional-join-2-large-large-with-small-join-result-2 | 1.6 ms | 86.7 ms | 9.3 ms | 137.5 ms | 53.2 ms | 3.2 ms |
| optional-join-3-star-1 | 5.9 ms | 701.3 ms | 12.2 ms | 882.2 ms | 174.2 ms | 7.6 ms |
| optional-join-3-star-2 | 4.9 ms | 306.9 ms | 8.4 ms | 860.0 ms | 189.8 ms | 9.9 ms |
| optional-join-3-chain-1 | 2.8 ms | 366.7 ms | 7.9 ms | 480.4 ms | 121.3 ms | 5.0 ms |
| optional-join-3-chain-2 | 2.1 ms | 364.8 ms | 8.0 ms | 520.1 ms | 127.2 ms | 5.3 ms |
| minus-join-small-large | 1.2 ms | 94.2 ms | 5.0 ms | 119.4 ms | 70.5 ms | 2.5 ms |
| minus-join-large-small | 1.3 ms | 27.1 ms | 5.7 ms | 91.9 ms | 52.2 ms | 4.1 ms |
| minus-join-large-large | 3.8 ms | 107.7 ms | 5.7 ms | 156.5 ms | 46.6 ms | 4.3 ms |
| minus-join-2-large-large-with-large-result | 1.7 ms | 72.6 ms | 3.8 ms | 100.9 ms | 53.4 ms | 2.6 ms |
| minus-join-2-large-large-with-small-join-result-1 | 1.6 ms | 19.5 ms | 5.7 ms | 57.9 ms | 25.8 ms | 2.5 ms |
| minus-join-2-large-large-with-small-join-result-2 | 1.6 ms | 17.2 ms | 5.7 ms | 47.9 ms | 28.6 ms | 2.5 ms |
| minus-join-3-star-1 | 5.3 ms | 457.5 ms | 9.5 ms | 451.9 ms | 106.7 ms | 6.0 ms |
| minus-join-3-star-2 | 4.7 ms | 271.1 ms | 7.4 ms | 305.7 ms | 57.4 ms | 6.3 ms |
| minus-join-3-chain-1 | 2.8 ms | 273.6 ms | 6.7 ms | 215.3 ms | 50.3 ms | 4.8 ms |
| minus-join-3-chain-2 | 1.7 ms | 302.8 ms | 6.5 ms | 178.7 ms | 95.1 ms | 4.1 ms |
| exists-join-small-large | 1.4 ms | 5.4 ms | 4.4 ms | 18.4 ms | 39.7 ms | 4.8 ms |
| exists-join-large-small | 1.2 ms | 367.1 ms | 5.7 ms | 192.2 ms | 342.9 ms | 5.7 ms |
| exists-join-large-large | 4.0 ms | 409.1 ms | 7.6 ms | 213.5 ms | 468.1 ms | 7.5 ms |
| exists-join-2-large-large-with-large-result | 2.2 ms | 178.6 ms | 4.2 ms | 105.5 ms | 177.5 ms | 9.0 ms |
| exists-join-2-large-large-with-small-join-result-1 | 2.1 ms | 92.3 ms | 5.5 ms | 52.3 ms | 89.3 ms | 5.5 ms |
| exists-join-2-large-large-with-small-join-result-2 | 3.3 ms | 87.7 ms | 5.5 ms | 46.5 ms | 91.3 ms | 4.2 ms |
| exists-join-3-star-1 | 4.7 ms | 678.4 ms | 10.3 ms | 289.4 ms | 259.7 ms | 8.3 ms |
| exists-join-3-star-2 | 5.0 ms | 663.4 ms | 9.2 ms | 276.6 ms | 446.8 ms | 8.2 ms |
| exists-join-3-chain-1 | 2.6 ms | 325.8 ms | 7.8 ms | 165.7 ms | 214.2 ms | 8.0 ms |
| exists-join-3-chain-2 | 1.9 ms | timeout | 8.5 ms | 191.8 ms | 222.6 ms | 7.8 ms |
| union-no-constraint | 1.1 ms | 82.1 ms | 2.6 ms | 73.5 ms | 95.9 ms | 3.4 ms |
| union-constraint-from-star | 3.9 ms | 415.4 ms | 5.8 ms | 312.7 ms | 243.2 ms | 5.4 ms |
| union-constraint-small-join | 4.6 ms | 208.9 ms | 14.6 ms | 75.3 ms | 68.3 ms | 3.8 ms |
| union-constraint-large-join | 5.1 ms | 413.1 ms | 6.5 ms | 319.4 ms | 306.2 ms | 5.3 ms |
| union-constraint-filter-restrictive | 1.0 ms | 679.9 ms | 4.8 ms | 45.3 ms | 186.9 ms | 3.0 ms |
| multicolumn-join-small | 1.1 ms | 8.1 ms | 5.6 ms | 9.0 ms | 16.6 ms | 2.6 ms |
| multicolumn-join-large | 7.8 ms | 257.0 ms | 8.7 ms | 79.3 ms | 97.8 ms | 4.6 ms |
| group-by-count-object-high-multiplicity | 1.3 ms | 19.0 ms | 3.2 ms | 140.5 ms | 64.5 ms | 2.5 ms |
| group-by-count-object-low-multiplicity | 3.3 ms | 58.1 ms | 3.4 ms | 896.0 ms | 165.9 ms | 4.1 ms |
| group-by-count-object-wrong-sort-order | 4.2 ms | 255.3 ms | 7.1 ms | 203.9 ms | 87.8 ms | 4.8 ms |
| group-by-complex-aggregate | 41.3 ms | 433.1 ms | 8.5 ms | 261.1 ms | 261.3 ms | 6.2 ms |
| group-by-implicit-numeric-baseline | 1.4 ms | 16.7 ms | 2.3 ms | 55.8 ms | 26.9 ms | 2.8 ms |
| group-by-implicit-numeric-sum | 2.4 ms | 17.4 ms | 2.6 ms | 42.0 ms | 55.6 ms | 2.5 ms |
| group-by-implicit-numeric-min | 2.5 ms | 16.7 ms | 2.5 ms | 47.7 ms | 63.1 ms | 2.7 ms |
| group-by-implicit-numeric-max | 1.9 ms | 16.7 ms | 2.5 ms | 22.4 ms | 23.2 ms | 2.6 ms |
| group-by-implicit-numeric-avg | 2.6 ms | 17.5 ms | 2.6 ms | 57.4 ms | 34.2 ms | 2.7 ms |
| group-by-implicit-string-baseline | 1.0 ms | 10.1 ms | 1.9 ms | 373.9 ms | 24.4 ms | 2.2 ms |
| group-by-implicit-string-min | 1.8 ms | 54.9 ms | 2.1 ms | 74.6 ms | 118.2 ms | 2.4 ms |
| group-by-implicit-string-max | 1.9 ms | 53.6 ms | 2.1 ms | 55.8 ms | 118.9 ms | 2.3 ms |
| group-by-string-groupconcat | 32.0 ms | 177.6 ms | 79.3 ms | 175.0 ms | 246.0 ms | 17.1 ms |
| distinct-count-object-high-multiplicity | 2.5 ms | 16.8 ms | 2.7 ms | 41.7 ms | 23.8 ms | 3.6 ms |
| distinct-count-object-low-multiplicity | 1.9 ms | 23.0 ms | 3.2 ms | 63.4 ms | 25.7 ms | 2.8 ms |
| distinct-count-object-wrong-sort-order | 3.6 ms | 263.1 ms | 4.9 ms | 131.6 ms | 47.1 ms | 4.2 ms |
| transitive-path-plus | 1.0 ms | 4.0 ms | 2.8 ms | 21.8 ms | 14.2 ms | 4.4 ms |
| transitive-path-plus-fixed-subject | 1.0 ms | 3.0 ms | 2.6 ms | 9.6 ms | 7.3 ms | 4.2 ms |
| transitive-path-large-join-and-plus | 2.4 ms | 272.3 ms | 4.4 ms | 274.2 ms | 14.7 ms | 23.2 ms |
| transitive-path-small-join-and-plus | 2.5 ms | 271.8 ms | 4.1 ms | 264.8 ms | 14.2 ms | 22.3 ms |
| regex-3-contains | 2.5 ms | 16.0 ms | 17.3 ms | 98.5 ms | 31.3 ms | 3.3 ms |
| regex-3-fixed | 2.1 ms | 13.7 ms | 17.5 ms | 48.3 ms | 32.6 ms | 3.3 ms |
| regex-3 | 3.3 ms | 13.1 ms | 17.9 ms | 20.8 ms | 33.7 ms | 2.9 ms |
| regex-prefix-1 | 1.2 ms | 12.1 ms | 2.8 ms | 22.9 ms | 23.7 ms | 2.6 ms |
| regex-prefix-2 | 1.2 ms | 11.9 ms | 3.3 ms | 18.5 ms | 21.9 ms | 2.5 ms |
| regex-prefix-3 | 1.5 ms | 11.7 ms | 2.6 ms | 15.0 ms | 21.6 ms | 2.3 ms |
| strlen | 1.8 ms | 11.7 ms | 16.6 ms | 18.8 ms | 55.6 ms | 2.6 ms |
| strbefore | 1.9 ms | 12.3 ms | 17.8 ms | 41.4 ms | 58.9 ms | 2.9 ms |
| strafter | 1.7 ms | 12.2 ms | 18.3 ms | 36.1 ms | 34.5 ms | 2.8 ms |
| strstarts | 1.6 ms | 11.9 ms | 17.1 ms | 33.7 ms | 37.6 ms | 2.4 ms |
| strends | 1.5 ms | 11.9 ms | 16.8 ms | 35.0 ms | 44.1 ms | 2.5 ms |
| result-size-tiny | 0.9 ms | 2.3 ms | 2.3 ms | 9.2 ms | 8.9 ms | 2.0 ms |
| result-size-small | 1.8 ms | 6.8 ms | 8.6 ms | 36.8 ms | 32.1 ms | 3.6 ms |
| result-size-medium | 63.1 ms | 420.9 ms | 590.8 ms | 700.4 ms | 688.9 ms | 166.5 ms |
| result-size-large | 66.7 ms | 441.2 ms | 577.9 ms | 700.9 ms | 590.2 ms | 134.6 ms |
| result-size-xlarge | 63.2 ms | 426.4 ms | 570.6 ms | 715.2 ms | 618.9 ms | 136.8 ms |
| numeric-baseline | 4.1 ms | 42.9 ms | 3.4 ms | 54.6 ms | 56.2 ms | 4.7 ms |
| numeric-abs | 3.4 ms | 42.3 ms | 3.6 ms | 62.5 ms | 77.4 ms | 4.2 ms |
| numeric-ceil | 3.6 ms | 29.4 ms | 3.1 ms | 52.4 ms | 39.2 ms | 3.4 ms |
| numeric-floor | 3.0 ms | 17.6 ms | 2.9 ms | 51.6 ms | 39.1 ms | 3.1 ms |
| numeric-round | 2.8 ms | 18.1 ms | 2.9 ms | 69.0 ms | 63.8 ms | 3.0 ms |
| numeric-add | 3.7 ms | 19.8 ms | 2.6 ms | 58.8 ms | 76.0 ms | 3.1 ms |
| numeric-greater | 7.4 ms | 17.7 ms | 2.8 ms | 63.0 ms | 17.9 ms | 3.5 ms |
| filter-few-results | 1.2 ms | 294.0 ms | 3.2 ms | 22.7 ms | 49.4 ms | 3.0 ms |
| filter-many-results | 1.1 ms | 298.9 ms | 3.8 ms | 130.3 ms | 69.1 ms | 3.2 ms |
| filter-language-en | 1.6 ms | 58.7 ms | 2.2 ms | 58.3 ms | 31.6 ms | 2.4 ms |
| date-year | 6.0 ms | 35.0 ms | 3.3 ms | 103.0 ms | 111.6 ms | 3.0 ms |
| date-month | 5.2 ms | 32.5 ms | 3.3 ms | 93.7 ms | 95.7 ms | 3.0 ms |
| date-day | 6.1 ms | 33.0 ms | 3.2 ms | 62.6 ms | 74.6 ms | 3.0 ms |
| number-of-triples | 0.9 ms | 273.1 ms | 1.4 ms | 364.1 ms | 268.8 ms | 1.5 ms |
| number-of-subjects | 0.9 ms | 313.7 ms | 1.3 ms | 402.7 ms | 365.1 ms | 22.5 ms |
| number-of-predicates | 1.0 ms | 293.0 ms | 1.3 ms | 321.7 ms | 510.6 ms | 14.7 ms |
| number-of-objects | 0.9 ms | 355.4 ms | 1.3 ms | 2.43 s | 281.1 ms | 96.1 ms |
| number-of-literals | 1.0 ms | 1.33 s | 10.2 ms | 706.4 ms | 289.1 ms | 10.9 ms |
| number-of-blank-nodes | 0.9 ms | 1.51 s | 1.7 ms | 310.2 ms | 202.6 ms | 6.0 ms |

</details>

Queries where engines disagree (row count, or the value of a one-row answer):

- union-constraint-filter-restrictive: graphdb differ (graphdb: ['181781']; majority: ['89'])
- group-by-implicit-string-min: maplib differ (maplib: ['trimotors flabbergasting birdhouse misfile houseboys rediscovered biasness cen; majority: ['aah disgusts resourcefully supines collinses bluebottles reorientation interca)
- group-by-implicit-string-max: maplib differ (maplib: ['comedones coverages phaeton skydives overtures']; majority: ['zymoplastic contuses reattachment irately tuber postbags metalling fearfully o)
- regex-prefix-1: qlever differ (qlever: ['669']; majority: ['0'])
- regex-prefix-2: qlever differ (qlever: ['259']; majority: ['0'])
- regex-prefix-3: qlever differ (qlever: ['54']; majority: ['0'])
- numeric-greater: qlever, maplib differ (qlever: ['53840'], maplib: ['53840']; majority: ['None'])

## rinf-0076 (102 queries)

| | tripletrail | oxigraph | qlever | jena | graphdb | maplib |
|---|---:|---:|---:|---:|---:|---:|
| load (s) | 1.608 | 3.28 | 2.608 | 10.697 | 17.509 | 0.741 |
| answered | 102 | 101 | 102 | 102 | 102 | 102 |
| failed | 0 | 0 | 0 | 0 | 0 | 0 |
| timed out | 0 | 1 | 0 | 0 | 0 | 0 |
| **geometric mean** | **3.0 ms** | **111.1 ms** | **10.4 ms** | **126.4 ms** | **97.5 ms** | **6.6 ms** |
| join | 2.7 ms | 87.6 ms | 15.3 ms | 77.9 ms | 69.6 ms | 6.4 ms |
| optional | 3.9 ms | 434.3 ms | 11.8 ms | 552.8 ms | 221.4 ms | 7.1 ms |
| minus | 3.5 ms | 273.5 ms | 11.5 ms | 207.4 ms | 101.9 ms | 5.5 ms |
| exists | 3.6 ms | 875.1 ms | 11.0 ms | 252.0 ms | 300.6 ms | 8.6 ms |
| union | 2.6 ms | 619.4 ms | 7.1 ms | 256.4 ms | 162.2 ms | 4.8 ms |
| group by / distinct | 3.4 ms | 26.9 ms | 4.3 ms | 67.7 ms | 44.3 ms | 4.7 ms |
| property path | 4.1 ms | 60.6 ms | 28.2 ms | 90.0 ms | 49.3 ms | 22.0 ms |
| regex / string | 3.5 ms | 69.6 ms | 42.8 ms | 84.0 ms | 153.6 ms | 4.4 ms |
| result size | 25.5 ms | 140.1 ms | 181.6 ms | 295.7 ms | 258.4 ms | 63.8 ms |
| numeric | 1.4 ms | 2.8 ms | 3.1 ms | 9.0 ms | 10.0 ms | 2.5 ms |
| filter / language | 1.5 ms | 575.1 ms | 7.5 ms | 190.1 ms | 124.5 ms | 2.8 ms |
| date | 0.9 ms | 2.2 ms | 1.8 ms | 11.0 ms | 11.8 ms | 1.8 ms |
| count | 0.9 ms | 930.6 ms | 1.9 ms | 917.5 ms | 411.6 ms | 22.3 ms |

<details><summary>Per query</summary>

| query | tripletrail | oxigraph | qlever | jena | graphdb | maplib |
|---|---:|---:|---:|---:|---:|---:|
| join-2-small-large | 2.9 ms | 36.8 ms | 12.8 ms | 118.0 ms | 218.0 ms | 9.8 ms |
| join-2-large-small | 1.5 ms | 14.9 ms | 8.1 ms | 32.7 ms | 39.9 ms | 5.1 ms |
| join-2-large-large | 8.7 ms | 467.9 ms | 8.6 ms | 420.9 ms | 147.4 ms | 5.4 ms |
| join-2-largest-result | 3.6 ms | 471.7 ms | 7.0 ms | 273.4 ms | 106.8 ms | 6.8 ms |
| join-2-large-large-with-large-result | 3.2 ms | 482.4 ms | 7.1 ms | 204.0 ms | 105.7 ms | 6.5 ms |
| join-2-large-large-with-small-result | 2.5 ms | 162.0 ms | 6.1 ms | 77.0 ms | 42.9 ms | 3.8 ms |
| join-3-star-largest-sum-of-join-sizes | 6.4 ms | 679.0 ms | 10.6 ms | 277.5 ms | 176.4 ms | 9.0 ms |
| join-3-chain-largest-sum-of-join-sizes | 5.3 ms | 618.0 ms | 14.6 ms | 287.9 ms | 138.2 ms | 9.5 ms |
| join-xlarge-star-on-small-predicates | 1.4 ms | 14.9 ms | 116.7 ms | 25.0 ms | 41.2 ms | 13.7 ms |
| join-xlarge-chain-on-small-predicates | 1.2 ms | 4.7 ms | 1.39 s | 13.7 ms | 21.4 ms | 8.3 ms |
| optional-join-small-large | 1.3 ms | 7.3 ms | 9.2 ms | 88.0 ms | 22.9 ms | 4.6 ms |
| optional-join-large-small | 1.6 ms | 2.18 s | 16.2 ms | 6.33 s | 913.9 ms | 6.0 ms |
| optional-join-large-large | 8.2 ms | 2.24 s | 16.2 ms | 1.86 s | 760.1 ms | 7.2 ms |
| optional-join-2-large-large-with-large-result | 4.9 ms | 455.0 ms | 7.9 ms | 246.5 ms | 281.5 ms | 7.8 ms |
| optional-join-2-large-large-with-small-join-result-1 | 2.4 ms | 135.2 ms | 7.5 ms | 115.0 ms | 89.9 ms | 4.8 ms |
| optional-join-2-large-large-with-small-join-result-2 | 2.7 ms | 372.3 ms | 8.1 ms | 287.9 ms | 159.8 ms | 4.4 ms |
| optional-join-3-star-1 | 5.8 ms | 1.28 s | 14.4 ms | 1.54 s | 560.2 ms | 9.3 ms |
| optional-join-3-star-2 | 6.3 ms | 538.0 ms | 11.2 ms | 808.1 ms | 182.4 ms | 9.1 ms |
| optional-join-3-chain-1 | 6.0 ms | 661.0 ms | 13.5 ms | 524.6 ms | 204.6 ms | 10.0 ms |
| optional-join-3-chain-2 | 7.6 ms | 644.1 ms | 21.5 ms | 481.0 ms | 210.3 ms | 11.3 ms |
| minus-join-small-large | 1.3 ms | 503.5 ms | 8.6 ms | 292.3 ms | 116.7 ms | 4.5 ms |
| minus-join-large-small | 1.3 ms | 139.1 ms | 16.6 ms | 249.1 ms | 132.9 ms | 5.8 ms |
| minus-join-large-large | 6.9 ms | 214.3 ms | 15.6 ms | 336.8 ms | 176.5 ms | 5.9 ms |
| minus-join-2-large-large-with-large-result | 4.6 ms | 499.9 ms | 12.3 ms | 285.6 ms | 116.6 ms | 4.9 ms |
| minus-join-2-large-large-with-small-join-result-1 | 2.2 ms | 50.2 ms | 6.0 ms | 63.2 ms | 47.1 ms | 3.9 ms |
| minus-join-2-large-large-with-small-join-result-2 | 2.1 ms | 68.8 ms | 5.9 ms | 61.5 ms | 50.5 ms | 4.3 ms |
| minus-join-3-star-1 | 4.7 ms | 574.9 ms | 11.7 ms | 215.7 ms | 112.1 ms | 7.7 ms |
| minus-join-3-star-2 | 5.6 ms | 452.1 ms | 11.1 ms | 207.1 ms | 87.3 ms | 6.2 ms |
| minus-join-3-chain-1 | 6.2 ms | 827.7 ms | 15.9 ms | 476.4 ms | 151.1 ms | 5.6 ms |
| minus-join-3-chain-2 | 7.1 ms | 420.2 ms | 20.1 ms | 254.9 ms | 106.9 ms | 6.9 ms |
| exists-join-small-large | 1.4 ms | 11.4 ms | 7.1 ms | 32.7 ms | 28.3 ms | 5.5 ms |
| exists-join-large-small | 1.2 ms | 2.17 s | 9.1 ms | 1.74 s | 3.29 s | 6.2 ms |
| exists-join-large-large | 8.0 ms | 2.22 s | 14.4 ms | 971.3 ms | 1.56 s | 9.4 ms |
| exists-join-2-large-large-with-large-result | 5.0 ms | 386.6 ms | 8.4 ms | 163.4 ms | 229.6 ms | 9.1 ms |
| exists-join-2-large-large-with-small-join-result-1 | 2.3 ms | 168.4 ms | 4.8 ms | 51.4 ms | 106.6 ms | 4.8 ms |
| exists-join-2-large-large-with-small-join-result-2 | 2.3 ms | 386.3 ms | 5.0 ms | 135.5 ms | 228.4 ms | 5.7 ms |
| exists-join-3-star-1 | 5.1 ms | 1.28 s | 26.1 ms | 586.8 ms | 315.6 ms | 11.9 ms |
| exists-join-3-star-2 | 5.5 ms | 725.4 ms | 14.6 ms | 334.6 ms | 276.4 ms | 11.6 ms |
| exists-join-3-chain-1 | 5.5 ms | 569.0 ms | 14.3 ms | 266.2 ms | 284.3 ms | 14.2 ms |
| exists-join-3-chain-2 | 7.6 ms | timeout | 26.5 ms | 313.7 ms | 299.4 ms | 13.7 ms |
| union-no-constraint | 0.9 ms | 203.8 ms | 3.3 ms | 148.8 ms | 191.5 ms | 4.7 ms |
| union-constraint-from-star | 6.5 ms | 545.1 ms | 9.4 ms | 940.6 ms | 220.1 ms | 6.2 ms |
| union-constraint-small-join | 3.0 ms | 570.9 ms | 7.5 ms | 75.3 ms | 31.7 ms | 4.6 ms |
| union-constraint-large-join | 6.6 ms | 698.5 ms | 9.3 ms | 978.4 ms | 245.6 ms | 6.3 ms |
| union-constraint-filter-restrictive | 1.0 ms | 2.06 s | 8.2 ms | 107.5 ms | 342.1 ms | 3.0 ms |
| multicolumn-join-small | 1.0 ms | 9.6 ms | 5.7 ms | 11.4 ms | 25.6 ms | 3.2 ms |
| multicolumn-join-large | 2.2 ms | 76.6 ms | 4.4 ms | 23.1 ms | 38.1 ms | 3.3 ms |
| group-by-count-object-high-multiplicity | 0.9 ms | 11.7 ms | 2.4 ms | 103.2 ms | 67.6 ms | 2.9 ms |
| group-by-count-object-low-multiplicity | 3.1 ms | 81.3 ms | 4.5 ms | 309.5 ms | 169.8 ms | 4.9 ms |
| group-by-count-object-wrong-sort-order | 4.0 ms | 181.3 ms | 7.7 ms | 208.8 ms | 50.4 ms | 20.5 ms |
| group-by-complex-aggregate | 50.3 ms | 500.1 ms | 10.2 ms | 254.4 ms | 190.9 ms | 23.4 ms |
| group-by-implicit-numeric-baseline | 1.4 ms | 3.9 ms | 2.5 ms | 15.7 ms | 6.6 ms | 2.5 ms |
| group-by-implicit-numeric-sum | 1.0 ms | 3.2 ms | 2.6 ms | 8.7 ms | 19.0 ms | 2.5 ms |
| group-by-implicit-numeric-min | 1.0 ms | 3.3 ms | 2.6 ms | 15.7 ms | 9.3 ms | 2.3 ms |
| group-by-implicit-numeric-max | 1.0 ms | 3.1 ms | 2.8 ms | 7.3 ms | 8.6 ms | 2.3 ms |
| group-by-implicit-numeric-avg | 0.9 ms | 3.2 ms | 2.8 ms | 17.2 ms | 12.9 ms | 2.4 ms |
| group-by-implicit-string-baseline | 0.9 ms | 43.5 ms | 1.9 ms | 776.8 ms | 40.4 ms | 2.8 ms |
| group-by-implicit-string-min | 18.1 ms | 94.1 ms | 2.5 ms | 140.9 ms | 187.3 ms | 2.7 ms |
| group-by-implicit-string-max | 19.9 ms | 73.1 ms | 2.6 ms | 112.1 ms | 111.3 ms | 2.7 ms |
| group-by-string-groupconcat | 43.7 ms | 111.8 ms | 142.5 ms | 197.7 ms | 232.0 ms | 24.3 ms |
| distinct-count-object-high-multiplicity | 2.1 ms | 11.1 ms | 2.4 ms | 17.7 ms | 21.7 ms | 3.5 ms |
| distinct-count-object-low-multiplicity | 2.8 ms | 29.8 ms | 3.4 ms | 87.7 ms | 46.4 ms | 4.3 ms |
| distinct-count-object-wrong-sort-order | 6.3 ms | 183.8 ms | 7.1 ms | 113.1 ms | 79.6 ms | 17.0 ms |
| transitive-path-plus | 6.8 ms | 150.0 ms | 98.5 ms | 385.5 ms | 112.8 ms | 24.0 ms |
| transitive-path-plus-fixed-subject | 1.1 ms | 3.0 ms | 2.6 ms | 7.2 ms | 7.9 ms | 9.8 ms |
| transitive-path-large-join-and-plus | 6.4 ms | 193.6 ms | 54.2 ms | 171.4 ms | 92.4 ms | 35.2 ms |
| transitive-path-small-join-and-plus | 6.1 ms | 154.3 ms | 44.6 ms | 136.8 ms | 72.4 ms | 28.2 ms |
| regex-3-contains | 2.6 ms | 70.5 ms | 118.6 ms | 75.1 ms | 166.9 ms | 4.2 ms |
| regex-3-fixed | 3.3 ms | 65.3 ms | 125.2 ms | 96.4 ms | 136.8 ms | 3.6 ms |
| regex-3 | 3.1 ms | 94.9 ms | 127.3 ms | 75.8 ms | 148.3 ms | 3.8 ms |
| regex-prefix-1 | 2.4 ms | 65.3 ms | 2.8 ms | 77.1 ms | 113.7 ms | 3.5 ms |
| regex-prefix-2 | 2.2 ms | 63.5 ms | 2.4 ms | 69.8 ms | 141.5 ms | 3.0 ms |
| regex-prefix-3 | 2.7 ms | 66.1 ms | 2.3 ms | 68.4 ms | 144.2 ms | 3.0 ms |
| strlen | 4.5 ms | 67.7 ms | 120.2 ms | 85.0 ms | 192.6 ms | 3.1 ms |
| strbefore | 5.7 ms | 71.0 ms | 131.2 ms | 96.6 ms | 157.1 ms | 14.0 ms |
| strafter | 5.3 ms | 70.7 ms | 131.3 ms | 96.9 ms | 167.2 ms | 12.1 ms |
| strstarts | 4.5 ms | 67.0 ms | 122.1 ms | 101.5 ms | 173.1 ms | 3.4 ms |
| strends | 4.5 ms | 67.6 ms | 119.7 ms | 90.5 ms | 163.4 ms | 3.3 ms |
| result-size-tiny | 1.0 ms | 2.7 ms | 2.7 ms | 7.5 ms | 6.9 ms | 1.9 ms |
| result-size-small | 1.5 ms | 6.9 ms | 8.7 ms | 26.6 ms | 31.9 ms | 3.3 ms |
| result-size-medium | 64.9 ms | 481.2 ms | 678.9 ms | 795.5 ms | 516.2 ms | 201.8 ms |
| result-size-large | 353.5 ms | 2.43 s | 3.52 s | 3.81 s | 3.13 s | 977.8 ms |
| result-size-xlarge | 330.2 ms | 2.48 s | 3.55 s | 3.74 s | 3.24 s | 870.5 ms |
| numeric-baseline | 2.0 ms | 3.8 ms | 4.9 ms | 9.5 ms | 9.6 ms | 3.7 ms |
| numeric-abs | 2.3 ms | 3.6 ms | 3.8 ms | 11.0 ms | 14.4 ms | 3.3 ms |
| numeric-ceil | 1.3 ms | 2.6 ms | 2.9 ms | 10.5 ms | 10.0 ms | 2.3 ms |
| numeric-floor | 1.4 ms | 2.5 ms | 2.8 ms | 6.7 ms | 9.1 ms | 2.3 ms |
| numeric-round | 1.1 ms | 2.4 ms | 2.7 ms | 7.4 ms | 8.5 ms | 2.1 ms |
| numeric-add | 1.0 ms | 2.5 ms | 2.6 ms | 7.2 ms | 14.8 ms | 2.1 ms |
| numeric-greater | 1.1 ms | 2.4 ms | 2.7 ms | 12.1 ms | 6.2 ms | 2.1 ms |
| filter-few-results | 1.0 ms | 1.66 s | 6.8 ms | 77.0 ms | 157.1 ms | 2.6 ms |
| filter-many-results | 1.0 ms | 1.67 s | 23.3 ms | 727.8 ms | 139.6 ms | 2.6 ms |
| filter-language-en | 3.4 ms | 68.6 ms | 2.6 ms | 122.7 ms | 88.0 ms | 3.2 ms |
| date-year | 0.9 ms | 2.0 ms | 2.0 ms | 16.4 ms | 13.4 ms | 2.0 ms |
| date-month | 0.9 ms | 2.2 ms | 1.8 ms | 7.4 ms | 10.5 ms | 1.8 ms |
| date-day | 0.9 ms | 2.7 ms | 1.6 ms | 11.0 ms | 11.7 ms | 1.7 ms |
| number-of-triples | 0.9 ms | 458.3 ms | 1.4 ms | 753.2 ms | 425.7 ms | 1.3 ms |
| number-of-subjects | 0.8 ms | 595.8 ms | 1.3 ms | 901.0 ms | 472.0 ms | 43.2 ms |
| number-of-predicates | 0.9 ms | 488.4 ms | 1.4 ms | 529.4 ms | 434.4 ms | 39.3 ms |
| number-of-objects | 0.9 ms | 638.2 ms | 1.7 ms | 2.35 s | 488.1 ms | 229.1 ms |
| number-of-literals | 1.1 ms | 2.98 s | 5.6 ms | 1.01 s | 392.1 ms | 20.1 ms |
| number-of-blank-nodes | 0.9 ms | 2.56 s | 1.9 ms | 700.9 ms | 290.9 ms | 12.1 ms |

</details>

Queries where engines disagree (row count, or the value of a one-row answer):

- union-constraint-filter-restrictive: graphdb differ (graphdb: ['598471']; majority: ['0'])
- group-by-complex-aggregate: no majority (tripletrail: ['http://publications.europa.eu/resource/authority/country/NOR', '117377', 'http, oxigraph: ['http://publications.europa.eu/resource/authority/country/NOR', '117377', 'http, qlever: ['http://publications.europa.eu/resource/authority/country/NOR', '117377', 'http, jena: ['http://publications.europa.eu/resource/authority/country/NOR', '117377', 'http, graphdb: ['http://publications.europa.eu/resource/authority/country/NOR', '117377', 'http, maplib: ['http://publications.europa.eu/resource/authority/country/NOR', '117377', 'http)
- group-by-implicit-string-min: qlever, maplib differ (qlever: ['-1'], maplib: ['None']; majority: ['"466,885 ""Snarvei"""'])
- group-by-implicit-string-max: no majority (tripletrail: ['Landsomfattende LPS - korrigert fra associated positioning system'], oxigraph: ['Øysteinstul track 2 (SP2-O)'], qlever: ['YTTERHEI'], jena: ['Landsomfattende LPS - korrigert fra associated positioning system'], graphdb: ['Landsomfattende LPS - korrigert fra associated positioning system'], maplib: ['None'])
- transitive-path-small-join-and-plus: maplib differ (maplib: ['5076']; majority: ['20057'])
- numeric-greater: qlever, maplib differ (qlever: ['958'], maplib: ['958']; majority: ['None'])
- number-of-objects: qlever differ (qlever: ['467289']; majority: ['467302'])
- number-of-literals: qlever differ (qlever: ['281721']; majority: ['311870'])
