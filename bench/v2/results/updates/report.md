# Update throughput by update size

Batches of held-out triples of the dataset sent one at a time as INSERT DATA, then the same batches as DELETE DATA (#496). Cells: microseconds per triple over all batches of that size, with the median batch time in ms in brackets; `!` marks a failed update or a count check that did not match. Derive: INSERT { } WHERE { } minting one node (3 triples plus one per type of the subject) per row, then DELETE WHERE, in ms.

## bsbm-28480 (8,246,418 triples in the base data)

| | tripletrail | oxigraph | jena |
|---|---:|---:|---:|
| load (s) | 4.34 | 9.569 | 36.175 |
| insert 10 | 414 (4.05) | 209 (2.07) | 4,735 (44.7) |
| insert 100 | 58.5 (6.00) | 41.4 (4.31) | 836 (84.6) |
| insert 1,000 | 24.9 (24.2) | 16.9 (16.9) | 210 (214) |
| insert 10,000 | 12.7 (125) | 11.7 (124) | 121 (1,226) |
| insert 100,000 | 12.5 (1,235) | 13.6 (1,347) | 83.3 (8,336) |
| insert 1,000,000 | 4.91 (4,914) |  ()! | 55.8 (55,800) |
| delete 10 | 382 (3.96) | 238 (2.36) | 3,722 (37.4) |
| delete 100 | 61.1 (6.02) | 33.7 (3.54) | 695 (68.8) |
| delete 1,000 | 19.7 (19.6) | 8.70 (7.54) | 190 (184) |
| delete 10,000 | 9.92 (99.9) | 7.80 (73.1) | 115 (1,160) |
| delete 100,000 | 9.34 (923) | 8.71 (889) | 79.3 (7,973) |
| delete 1,000,000 | 5.31 (5,309) |  ()! | 54.0 (54,039) |
| derive-1000 (760 rows) | 29.1 / 31.6 | 46.4 / 39.2 | 227 / 138 |
| derive-10000 (10,998 rows) | 834 / 338 | 768 / 614 | 1,097 / 718 |
| derive-100000 (39,528 rows) | 720 / 1,020 | 3,414 / 2,302 | 3,700 / 2,715 |
| store after (MB) | 1,220 | 2,013 | 13,372 |
