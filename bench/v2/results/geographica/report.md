| Engine | Load (s) | Index / start (s) | On disk |
|---|---|---|---|
| tripletrail | 2.2 | 0.6 | 634 MiB |
| GraphDB | 20.8 | 14.7 | 671 MiB |
| Jena GeoSPARQL | 16.6 | 2.2 | 1,256 MiB |
| QLever | 8.9 | 0.5 | 220 MiB |

| Engine | Answered | Answered, some values unbound | Timeout | Error | Fastest complete answer |
|---|---|---|---|---|---|
| tripletrail | 40 | 3 | 0 | 0 | 37 |
| GraphDB | 26 | 3 | 11 | 3 | 1 |
| Jena GeoSPARQL | 31 | 6 | 3 | 3 | 2 |
| QLever | 25 | 3 | 1 | 14 | 0 |

43 queries; timeout 300 s. Cold / best warm time in ms (`s` = seconds), row count in brackets.

| Workload | Query | tripletrail | GraphDB | Jena GeoSPARQL | QLever |
|---|---|---|---|---|---|
| micro nontopological | 1 Boundary_CLC | **1.60 s / 1.59 s** (44,834) | timeout | 18 s / 16 s (44,834) | error [1] |
| micro nontopological | 2 Envelope_CLC | **226 / 189** (44,834) | 6.31 s / 6.23 s (44,834) | 6.55 s / 6.55 s (44,834) | 351 / 252 (44,834) |
| micro nontopological | 3 ConvexHull_CLC | **521 / 529** (44,834) | 12 s / 11 s (44,834) | 8.06 s / 8.02 s (44,834) | error [2] |
| micro nontopological | 4 Buffer_GeoNames | **206 / 199** (21,990) | 1.75 s / 1.56 s (21,990) | error [3] | error [4] |
| micro nontopological | 5 Buffer_LGD | **693 / 680** (12,097) | 4.98 s / 4.82 s (12,097) | error [5] | error [6] |
| micro nontopological | 6 Area_CLC | 658 / 131 (44,834) | error [7] | 76 / 53 (44,834, 44,834 unbound) | 254 / 185 (44,834, 14 unbound) |
| micro selections | 7 Equals_LGD_GivenLine | **46 / 39** (1) | 2.08 s / 1.97 s (1) | 536 / 89 (1) | 58 / 54 (1) |
| micro selections | 8 Equals_GAG_GivenPolygon | **66 / 62** (1) | 755 / 725 (1) | 718 / 67 (1) | 143 / 140 (1) |
| micro selections | 9 Intersects_LGD_GivenPolygon | **96 / 44** (216) | 12 s / 12 s (216) | 157 / 103 (216) | 122 / 121 (216) |
| micro selections | 10 Intersects_CLC_GivenLine | **8.2 / 8.6** (20) | 9.04 s / 8.98 s (20) | 6.07 s / 6.06 s (20) | 606 / 588 (20) |
| micro selections | 11 Overlaps_CLC_GivenPolygon | **77 / 66** (132) | 51 s / 51 s (132) | 6.40 s / 6.42 s (132) | 911 / 827 (132) |
| micro selections | 12 Crosses_LGD_GivenLine | 108 / 105 (14) | 326 / 322 (14) | **141 / 34** (14) | 88 / 86 (14) |
| micro selections | 13 Within_GeoNames_GivenPolygon | **40 / 38** (136) | 22 s / 22 s (136) | 524 / 141 (136) | 67 / 65 (136) |
| micro selections | 14 Within_GeoNames_Point_Buffer | **128 / 132** (1) | 1.02 s / 1.00 s (150 *) | error [8] | error [9] |
| micro selections | 15 GeoNames_Point_Distance | **29 / 28** (153) | 230 / 126 (153) | 86 / 53 (153) | error [10] |
| micro selections | 16 Disjoint_GeoNames_GivenPolygon | **235 / 199** (21,854) | 22 s / 22 s (21,854) | 509 / 264 (21,854) | error [11] |
| micro selections | 17 Disjoint_LGD_GivenPolygon | **150 / 137** (11,881) | 13 s / 13 s (11,881) | 491 / 355 (11,881) | error [12] |
| micro joins | 18 Equals_GeoNames_DBPedia | **21 / 18** (91) | timeout | 218 s / - (0 *) | 151 / 142 (91) |
| micro joins | 19 Intersects_GeoNames_LGD | **21 / 20** (0) | timeout | timeout | 341 / 339 (0) |
| micro joins | 20 Intersects_GeoNames_GAG | **113 / 66** (18,689) | timeout | 8.87 s / 8.18 s (18,689) | 1.82 s / 1.83 s (18,689) |
| micro joins | 21 Intersects_LGD_GAG | **58 / 70** (13,318) | timeout | 5.09 s / 5.17 s (13,318) | 2.04 s / 2.03 s (13,321 *) |
| micro joins | 22 Within_GeoNames_GAG | **87 / 88** (18,689) | timeout | 17 s / 17 s (18,689) | 1.83 s / 1.83 s (18,689) |
| micro joins | 23 Within_LGD_GAG | **68 / 68** (10,673) | timeout | 8.88 s / 8.31 s (10,673) | 2.05 s / 1.98 s (10,676 *) |
| micro joins | 24 Within_CLC_GAG | **379 / 353** (34,083) | timeout | 42 s / 43 s (34,083) | 5.93 s / 5.81 s (34,083) |
| micro joins | 25 Crosses_LGD_GAG | **258 / 247** (2,645) | timeout | 8.57 s / 8.47 s (2,645) | 1.87 s / 1.89 s (2,639 *) |
| micro joins | 26 Touches_GAG_GAG | **385 / 380** (1,022) | 199 s / - (1,022) | 1.26 s / 1.25 s (1,022) | 3.27 s / 3.30 s (236 *) |
| micro joins | 27 Overlaps_GAG_CLC | **2.93 s / 2.99 s** (17,005 *) | timeout | timeout | 5.84 s / 5.86 s (17,160) |
| micro aggregations | 28 Extent_GAG | 271 / 16 (1) | error [13] | 6.5 / 5.0 (325, 325 unbound) | error [14] |
| micro aggregations | 29 Union_GAG | 462 / 461 (1) | error [15] | 5.3 / 5.4 (325, 325 unbound) | error [16] |
| macro reversegeocoding | 0 Find_Closest_Populated_Place | 222 / 224 (1) | 226 / 127 (1) | **175 / 98** (1) | error [17] |
| macro reversegeocoding | 1 Find_Closest_Motorway | 204 / 194 (1, 1 unbound) | 122 / 85 (1, 1 unbound) | 117 / 47 (1, 1 unbound) | error [18] |
| macro mapsearch | 0 Thematic_Search | 15 / 13 (1) | **7.5 / 5.0** (1) | 16 / 6.4 (1) | 70 / 68 (1) |
| macro mapsearch | 1 Get_Around_POIs | **22 / 17** (13) | 202 / 178 (13) | 286 / 272 (13) | 158 / 124 (13) |
| macro mapsearch | 2 Get_Around_Roads | 70 / 71 (132, 60 unbound) | 221 / 213 (132, 60 unbound) | 1.05 s / 750 (132, 60 unbound) | 85 / 78 (132, 60 unbound) |
| macro rapidmapping | 0 Get_CLC_areas | **689 / 695** (30,453) | 180 s / - (30,453) | 14 s / 13 s (30,453) | timeout |
| macro rapidmapping | 1 Get_highways | **57 / 28** (4,559) | 203 / 194 (4,559) | 189 / 158 (4,559) | 360 / 332 (4,559) |
| macro rapidmapping | 2 Get_municipalities | **134 / 130** (248) | 2.76 s / 2.72 s (248) | 1.31 s / 693 (248) | error [19] |
| macro rapidmapping | 3 Get_hotspots | 2.41 s / 2.42 s (902,195, 902,195 unbound) | 82 s / 82 s (902,195, 902,195 unbound) | 26 s / 25 s (902,195, 902,195 unbound) | 29 s / 28 s (902,195, 902,195 unbound) |
| macro rapidmapping | 4 Get_coniferous_forests_in_fire | **14 / 13** (50) | 12 s / 12 s (50) | 928 / 544 (50) | 944 / 931 (50) |
| macro rapidmapping | 5 Get_road_segments_affected_by_fire | 186 / 183 (17,275) | timeout | timeout | error [20] |
| macro computestatistics | 0 Count_CLC_categories | **24 / 9.9** (12) | 5.39 s / 5.34 s (12) | 6.33 s / 6.35 s (12) | 658 / 636 (12) |
| macro computestatistics | 1 Count_GeoNames_categories | **13 / 10** (8) | 184 / 182 (8) | 273 / 210 (8) | 102 / 94 (8) |
| macro computestatistics | 2 Count_GeoNames_categories_in_ContinuousUrbanFabric | **56 / 45** (1) | 14 s / 14 s (1) | 209 / 204 (1) | 146 / 145 (1) |

Errors:

1. QLever 1 Boundary_CLC: Not supported: Function "<http://www.opengis.net/def/function/geosparql/boundary>" is currently not supported by QLever.
2. QLever 3 ConvexHull_CLC: Not supported: Function "<http://www.opengis.net/def/function/geosparql/convexHull>" is currently not supported by QLever.
3. Jena GeoSPARQL 4 Buffer_GeoNames: HTTP 500: Function 'BufferFF' takes three arguments
4. QLever 4 Buffer_GeoNames: Not supported: Function "<http://www.opengis.net/def/function/geosparql/buffer>" is currently not supported by QLever.
5. Jena GeoSPARQL 5 Buffer_LGD: HTTP 500: Function 'BufferFF' takes three arguments
6. QLever 5 Buffer_LGD: Not supported: Function "<http://www.opengis.net/def/function/geosparql/buffer>" is currently not supported by QLever.
7. GraphDB 6 Area_CLC: HTTP 500: Query evaluation error: Unknown function 'http://www.opengis.net/def/function/geosparql/metricArea'
8. Jena GeoSPARQL 14 Within_GeoNames_Point_Buffer: HTTP 500: Function 'BufferFF' takes three arguments
9. QLever 14 Within_GeoNames_Point_Buffer: Not supported: Function "<http://www.opengis.net/def/function/geosparql/buffer>" is currently not supported by QLever.
10. QLever 15 GeoNames_Point_Distance: Unsupported unit of measurement for distance.
11. QLever 16 Disjoint_GeoNames_GivenPolygon: Not supported: Function "<http://www.opengis.net/def/function/geosparql/sfDisjoint>" is currently not supported by QLever.
12. QLever 17 Disjoint_LGD_GivenPolygon: Not supported: Function "<http://www.opengis.net/def/function/geosparql/sfDisjoint>" is currently not supported by QLever.
13. GraphDB 28 Extent_GAG: HTTP 500: Query evaluation error: Unknown function 'http://www.opengis.net/def/function/geosparql/aggBoundingBox'
14. QLever 28 Extent_GAG: Not supported: Function "<http://www.opengis.net/def/function/geosparql/aggBoundingBox>" is currently not supported by QLever.
15. GraphDB 29 Union_GAG: HTTP 500: Query evaluation error: Unknown function 'http://www.opengis.net/def/function/geosparql/aggUnion'
16. QLever 29 Union_GAG: Not supported: Function "<http://www.opengis.net/def/function/geosparql/aggUnion>" is currently not supported by QLever.
17. QLever 0 Find_Closest_Populated_Place: Unsupported unit of measurement for distance.
18. QLever 1 Find_Closest_Motorway: Unsupported unit of measurement for distance.
19. QLever 2 Get_municipalities: Not supported: Function "<http://www.opengis.net/def/function/geosparql/boundary>" is currently not supported by QLever.
20. QLever 5 Get_road_segments_affected_by_fire: Not supported: Function "<http://www.opengis.net/def/function/geosparql/difference>" is currently not supported by QLever.
