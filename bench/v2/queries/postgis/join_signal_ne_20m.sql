SELECT count(*) FROM signal s JOIN ne e ON ST_DWithin(s.geom::geography, e.geom::geography, 20)
