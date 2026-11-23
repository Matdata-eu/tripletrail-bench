# Update throughput by update size

Batches of held-out triples of the dataset sent one at a time as INSERT DATA, then the same batches as DELETE DATA (#496). Cells: microseconds per triple over all batches of that size, with the median batch time in ms in brackets; `!` marks a failed update or a count check that did not match. Derive: INSERT { } WHERE { } minting one node (3 triples plus one per type of the subject) per row, then DELETE WHERE, in ms.

## bsbm-28480 (8,246,418 triples in the base data)

| | tripletrail | oxigraph | jena | graphdb |
|---|---:|---:|---:|---:|
| load (s) | 4.299 | 13.651 | 37.69 | 42.56 |
| insert 10 | 432 (4.26) | 226 (2.27) | 4,722 (44.7) | 4,916 (48.5) |
| insert 100 | 62.9 (6.31) | 34.4 (3.29) | 847 (84.0) | 559 (45.4) |
| insert 1,000 | 24.6 (23.6) | 18.9 (19.2) | 197 (194) | 239 (235) |
| insert 10,000 | 12.5 (129) | 12.4 (122) | 120 (1,195) | 175 (1,700) |
| insert 100,000 | 13.1 (1,327) | 13.9 (1,402) | 82.9 (8,322) | 64.1 (6,444) |
| insert 1,000,000 | 5.12 (5,118) |  ()! | 55.5 (55,528) | 31.6 (31,575) |
| delete 10 | 413 (4.13) | 221 (2.21) | 3,837 (38.0) | 2,696 (26.2) |
| delete 100 | 59.9 (5.94) | 32.0 (3.31) | 672 (66.8) | 250 (22.6) |
| delete 1,000 | 21.3 (21.7) | 10.6 (8.04) | 170 (162) | 102 (99.5) |
| delete 10,000 | 12.3 (123) | 8.40 (87.2) | 114 (1,145) | 67.0 (671) |
| delete 100,000 | 10.2 (1,019) | 9.23 (923) | 80.5 (8,044) | 27.5 (2,684) |
| delete 1,000,000 | 5.79 (5,787) |  ()! | 54.4 (54,447) | 21.3 (21,326) |
| derive-1000 (760 rows) | 24.6 / 27.8 | 71.0 / 66.1 | 218 / 136 | 166 / 79.9 |
| derive-10000 (10,998 rows) | 890 / 353 | 768 / 645 | 1,101 / 1,010 | 727 / 382 |
| derive-100000 (39,528 rows) | 732 / 1,044 | 3,487 / 2,375 | 3,731 / 3,577 | 1,877 / 1,114 |
| store after (MB) | 1,326 | 2,013 | 13,372 | 2,786 |
