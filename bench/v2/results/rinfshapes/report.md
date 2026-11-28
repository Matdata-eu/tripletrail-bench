# RINF query-shape suite

Queries on public RINF data grouped by shape (`suites/rinfshapes/queries.py`), each in a rows form and a count form. Times in ms: the median of the warm runs, over HTTP with every row read. Engines that give different row counts are flagged; a count form whose number differs from its rows form's row count is flagged too. An ablation control repeats a top-k or facet query with patterns taken out.

## rinf-all (42,888,801 triples)

| query | tripletrail rows | tripletrail count | oxigraph rows | oxigraph count | qlever rows | qlever count | jena rows | jena count | rows |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| load (s) | 86.61 |  | 171.74 |  | 84.076 |  | 266.723 |  |
| **Facet over a big class** | | | | | | | | | |
| facet-gauging-deu | 30.4 | 38.3 | 2,857 | 2,805 | 41.1 | 39.7 | 956 | 929 | 6 |
| facet-sol-length | 17.0 | 16.2 | 846 | 891 | 25.0 | 23.2 | 484 | 490 | 28 |
| **Top-k over a star** | | | | | | | | | |
| topk-speed-label | 2.7 | 3.1 | 3,459 | 3,331 | 30.9 | 33.3 | 1,279 | 1,315 | 20 |
| topk-cant-speed | 3.4 | 2.7 | 3,441 | 3,604 | 31.7 | 39.6 | 1,327 | 1,338 | 20 |
| **Star with combined filters** | | | | | | | | | |
| star-speed-cant-deu | 4.7 | 4.7 | 2,912 | 2,893 | 27.4 | 28.2 | 869 | 924 | 122 |
| star-bool-range | 9.0 | 6.4 | 912 | 941 | 39.1 | 16.2 | 1,143 | 1,086 | 4,811 |
| **Chain** | | | | | | | | | |
| chain-track-op | 54.9 | 21.6 | 4,043 | 3,521 | 317 | 47.3 | 1,847 | 1,285 | 19,692 |
| chain-op-wkt | 176 | 28.1 | 5,370 | 2,613 | 898 | 59.5 | 2,902 | 837 | **differ:** tripletrail=88,907, oxigraph=88,907, qlever=88,875, jena=88,907 |
| **Wide table with OPTIONALs** | | | | | | | | | |
| wide-track-optional | 648 | 65.5 | 14,051 | 7,953 | 3,714 | 97.6 | 14,572 | 6,605 | 412,885 |
| wide-op | 150 | 37.0 | 3,099 | 1,500 | 842 | 32.6 | 2,502 | 787 | 54,108 |
| **Anti-join** | | | | | | | | | |
| anti-track-no-speed | 256 | 20.2 | 5,399 | 2,734 | 618 | 22.9 | 3,264 | 1,342 | 304,739 |
| **Valid on a day** | | | | | | | | | |
| valid-day-sol | 489 | 410 | 2,415 | 2,341 | 1,060 | 977 | 1,664 | 1,403 | 35,108 |
| valid-day-op | 340 | 360 | 2,483 | 2,149 | 1,029 | 944 | 1,678 | 1,453 | 35,983 |
| valid-day-track | 701 | 647 | 15,293 | 13,305 | 6,389 | 5,997 | 12,428 | 10,620 | 218,327 |
| valid-day-any | 1,442 | 993 | 23,317 | 23,309 | 13,442 | 12,445 | 23,548 | 21,015 | 488,380 |
| **Ablation controls** | | | | | | | | | |
| control-topk-speed (of topk-speed-label) | 1.7 | 1.6 | 126 | 133 | 3.6 | 4.6 | 317 | 296 | 20 |
| control-topk-cant (of topk-cant-speed) | 1.7 | 1.8 | 95.3 | 96.0 | 4.3 | 4.9 | 418 | 376 | 20 |
| control-facet-gauging-join (of facet-gauging-deu) | 69.2 | 34.3 | 3,798 | 2,838 | 543 | 33.9 | 2,195 | 1,072 | 103,364 |
| control-facet-gauging-noclass (of facet-gauging-deu) | 20.8 | 25.7 | 1,920 | 1,931 | 23.0 | 23.3 | 969 | 946 | 6 |
| control-valid-track-join (of valid-day-track) | 276 | 150 | 14,352 | 12,085 | 877 | 176 | 14,496 | 9,960 | 319,335 |
| control-facet-sol-join (of facet-sol-length) | 60.9 | 10.6 | 1,714 | 809 | 570 | 20.9 | 1,751 | 378 | 69,711 |

Count time as a share of rows time (the rest is writing and reading the rows):

| query | tripletrail | oxigraph | qlever | jena |
|---|---:|---:|---:|---:|
| facet-gauging-deu | 1.26 | 0.98 | 0.97 | 0.97 |
| facet-sol-length | 0.95 | 1.05 | 0.93 | 1.01 |
| topk-speed-label | 1.17 | 0.96 | 1.08 | 1.03 |
| topk-cant-speed | 0.80 | 1.05 | 1.25 | 1.01 |
| star-speed-cant-deu | 1.02 | 0.99 | 1.03 | 1.06 |
| star-bool-range | 0.71 | 1.03 | 0.41 | 0.95 |
| chain-track-op | 0.39 | 0.87 | 0.15 | 0.70 |
| chain-op-wkt | 0.16 | 0.49 | 0.07 | 0.29 |
| wide-track-optional | 0.10 | 0.57 | 0.03 | 0.45 |
| wide-op | 0.25 | 0.48 | 0.04 | 0.31 |
| anti-track-no-speed | 0.08 | 0.51 | 0.04 | 0.41 |
| valid-day-sol | 0.84 | 0.97 | 0.92 | 0.84 |
| valid-day-op | 1.06 | 0.87 | 0.92 | 0.87 |
| valid-day-track | 0.92 | 0.87 | 0.94 | 0.85 |
| valid-day-any | 0.69 | 1.00 | 0.93 | 0.89 |
| control-topk-speed | 0.92 | 1.06 | 1.26 | 0.94 |
| control-topk-cant | 1.06 | 1.01 | 1.13 | 0.90 |
| control-facet-gauging-join | 0.50 | 0.75 | 0.06 | 0.49 |
| control-facet-gauging-noclass | 1.24 | 1.01 | 1.01 | 0.98 |
| control-valid-track-join | 0.54 | 0.84 | 0.20 | 0.69 |
| control-facet-sol-join | 0.17 | 0.47 | 0.04 | 0.22 |
