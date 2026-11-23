| Engine | Load (s) | Index / start (s) | On disk |
|---|---|---|---|
| tripletrail | 2.8 | 0.6 | 592 MiB |
| GraphDB | 22.2 | 15.1 | 671 MiB |
| Jena GeoSPARQL | 16.4 | 3.3 | 1,256 MiB |
| QLever | 9.0 | 0.5 | 220 MiB |

| Engine | Answered | Answered, some values unbound | Timeout | Error | Fastest complete answer |
|---|---|---|---|---|---|
| tripletrail | 40 | 3 | 0 | 0 | 34 |
| GraphDB | 26 | 3 | 11 | 3 | 1 |
| Jena GeoSPARQL | 31 | 6 | 3 | 3 | 4 |
| QLever | 25 | 3 | 1 | 14 | 1 |

43 queries; timeout 300 s. Cold / best warm time in ms (`s` = seconds), row count in brackets.

| Workload | Query | tripletrail | GraphDB | Jena GeoSPARQL | QLever |
|---|---|---|---|---|---|
| micro nontopological | 1 Boundary_CLC | **1.68 s / 1.53 s** (44,834) | timeout | 19 s / 16 s (44,834) | error [1] |
| micro nontopological | 2 Envelope_CLC | **242 / 228** (44,834) | 6.66 s / 6.24 s (44,834) | 6.66 s / 6.57 s (44,834) | 466 / 378 (44,834) |
| micro nontopological | 3 ConvexHull_CLC | **565 / 535** (44,834) | 11 s / 11 s (44,834) | 8.22 s / 8.09 s (44,834) | error [2] |
| micro nontopological | 4 Buffer_GeoNames | **229 / 209** (21,990) | 1.75 s / 1.57 s (21,990) | error [3] | error [4] |
| micro nontopological | 5 Buffer_LGD | **779 / 742** (12,097) | 4.97 s / 4.81 s (12,097) | error [5] | error [6] |
| micro nontopological | 6 Area_CLC | 677 / 134 (44,834) | error [7] | 77 / 52 (44,834, 44,834 unbound) | 232 / 186 (44,834, 14 unbound) |
| micro selections | 7 Equals_LGD_GivenLine | **50 / 17** (1) | 2.01 s / 1.95 s (1) | 557 / 111 (1) | 47 / 52 (1) |
| micro selections | 8 Equals_GAG_GivenPolygon | 356 / 352 (1) | 728 / 753 (1) | **695 / 70** (1) | 145 / 142 (1) |
| micro selections | 9 Intersects_LGD_GivenPolygon | **66 / 57** (216) | 13 s / 13 s (216) | 158 / 127 (216) | 115 / 110 (216) |
| micro selections | 10 Intersects_CLC_GivenLine | **14 / 10** (20) | 9.10 s / 9.00 s (20) | 6.23 s / 6.11 s (20) | 584 / 577 (20) |
| micro selections | 11 Overlaps_CLC_GivenPolygon | **88 / 70** (132) | 51 s / 51 s (132) | 6.52 s / 6.61 s (132) | 895 / 844 (132) |
| micro selections | 12 Crosses_LGD_GivenLine | 108 / 104 (14) | 329 / 297 (14) | **169 / 37** (14) | 87 / 82 (14) |
| micro selections | 13 Within_GeoNames_GivenPolygon | **45 / 41** (136) | 22 s / 22 s (136) | 559 / 144 (136) | 71 / 63 (136) |
| micro selections | 14 Within_GeoNames_Point_Buffer | **129 / 137** (1) | 996 / 977 (150 *) | error [8] | error [9] |
| micro selections | 15 GeoNames_Point_Distance | **32 / 28** (153) | 256 / 121 (153) | 87 / 73 (153) | error [10] |
| micro selections | 16 Disjoint_GeoNames_GivenPolygon | **248 / 245** (21,854) | 22 s / 22 s (21,854) | 534 / 292 (21,854) | error [11] |
| micro selections | 17 Disjoint_LGD_GivenPolygon | **240 / 239** (11,881) | 13 s / 13 s (11,881) | 517 / 375 (11,881) | error [12] |
| micro joins | 18 Equals_GeoNames_DBPedia | **23 / 20** (91) | timeout | 246 s / - (0 *) | 112 / 107 (91) |
| micro joins | 19 Intersects_GeoNames_LGD | **23 / 21** (0) | timeout | timeout | 310 / 317 (0) |
| micro joins | 20 Intersects_GeoNames_GAG | **111 / 87** (18,689) | timeout | 8.70 s / 8.24 s (18,689) | 1.79 s / 1.70 s (18,689) |
| micro joins | 21 Intersects_LGD_GAG | **57 / 62** (13,318) | timeout | 5.26 s / 5.08 s (13,318) | 1.98 s / 1.89 s (13,321 *) |
| micro joins | 22 Within_GeoNames_GAG | **90 / 84** (18,689) | timeout | 17 s / 17 s (18,689) | 1.73 s / 1.74 s (18,689) |
| micro joins | 23 Within_LGD_GAG | **60 / 70** (10,673) | timeout | 9.44 s / 8.29 s (10,673) | 1.83 s / 1.88 s (10,676 *) |
| micro joins | 24 Within_CLC_GAG | **485 / 420** (34,083) | timeout | 43 s / 41 s (34,083) | 5.22 s / 5.16 s (34,083) |
| micro joins | 25 Crosses_LGD_GAG | **341 / 322** (2,645) | timeout | 8.53 s / 8.48 s (2,645) | 1.81 s / 1.80 s (2,639 *) |
| micro joins | 26 Touches_GAG_GAG | 1.79 s / 1.78 s (1,022) | 200 s / - (1,022) | **1.30 s / 1.22 s** (1,022) | 3.27 s / 3.31 s (1,192 *) |
| micro joins | 27 Overlaps_GAG_CLC | 5.54 s / 5.49 s (17,005 *) | timeout | timeout | **5.14 s / 5.04 s** (17,160) |
| micro aggregations | 28 Extent_GAG | 357 / 186 (1) | error [13] | 4.3 / 2.8 (325, 325 unbound) | error [14] |
| micro aggregations | 29 Union_GAG | 660 / 632 (1) | error [15] | 2.9 / 2.8 (325, 325 unbound) | error [16] |
| macro reversegeocoding | 0 Find_Closest_Populated_Place | 270 / 262 (1) | 192 / 128 (1) | **152 / 100** (1) | error [17] |
| macro reversegeocoding | 1 Find_Closest_Motorway | 285 / 249 (1, 1 unbound) | 132 / 78 (1, 1 unbound) | 76 / 47 (1, 1 unbound) | error [18] |
| macro mapsearch | 0 Thematic_Search | 15 / 14 (1) | **6.1 / 4.9** (1) | 8.2 / 6.2 (1) | 78 / 77 (1) |
| macro mapsearch | 1 Get_Around_POIs | **34 / 15** (13) | 215 / 208 (13) | 290 / 263 (13) | 134 / 123 (13) |
| macro mapsearch | 2 Get_Around_Roads | 76 / 75 (132, 60 unbound) | 225 / 192 (132, 60 unbound) | 1.06 s / 749 (132, 60 unbound) | 80 / 80 (132, 60 unbound) |
| macro rapidmapping | 0 Get_CLC_areas | **676 / 720** (30,453) | 184 s / - (30,453) | 14 s / 13 s (30,453) | timeout |
| macro rapidmapping | 1 Get_highways | **85 / 85** (4,559) | 204 / 172 (4,559) | 177 / 129 (4,559) | 349 / 344 (4,559) |
| macro rapidmapping | 2 Get_municipalities | **642 / 614** (248) | 2.79 s / 2.77 s (248) | 1.37 s / 692 (248) | error [19] |
| macro rapidmapping | 3 Get_hotspots | 3.37 s / 2.91 s (902,195, 902,195 unbound) | 84 s / 83 s (902,195, 902,195 unbound) | 25 s / 25 s (902,195, 902,195 unbound) | 29 s / 29 s (902,195, 902,195 unbound) |
| macro rapidmapping | 4 Get_coniferous_forests_in_fire | **16 / 14** (50) | 12 s / 12 s (50) | 958 / 577 (50) | 939 / 941 (50) |
| macro rapidmapping | 5 Get_road_segments_affected_by_fire | 372 / 345 (17,275) | timeout | timeout | error [20] |
| macro computestatistics | 0 Count_CLC_categories | **44 / 9.2** (12) | 5.49 s / 5.43 s (12) | 6.25 s / 6.25 s (12) | 650 / 625 (12) |
| macro computestatistics | 1 Count_GeoNames_categories | **17 / 14** (8) | 187 / 156 (8) | 259 / 223 (8) | 98 / 100 (8) |
| macro computestatistics | 2 Count_GeoNames_categories_in_ContinuousUrbanFabric | **62 / 50** (1) | 14 s / 14 s (1) | 200 / 193 (1) | 138 / 138 (1) |

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
