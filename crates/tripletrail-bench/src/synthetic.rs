//! The generated ERA-shaped network shared by the benchmark binaries.

use tripletrail::oxigraph::model::vocab::{rdf, xsd};
use tripletrail::oxigraph::model::{GraphName, Literal, NamedNode, Quad, Term};

pub const ERA: &str = "http://data.europa.eu/949/";
pub const NAV: &str = "http://data.europa.eu/949/concepts/navigabilities/";
pub const GSP: &str = "http://www.opengis.net/ont/geosparql#";
pub const BASE: &str = "http://example.org/synthetic/";

pub struct Gen {
    pub quads: Vec<Quad>,
    pub elements: usize,
    pub relations: usize,
}

impl Gen {
    fn nn(s: String) -> NamedNode {
        NamedNode::new_unchecked(s)
    }

    fn add(&mut self, s: &NamedNode, p: &str, o: impl Into<Term>) {
        self.quads.push(Quad::new(
            s.clone(),
            Self::nn(p.to_owned()),
            o,
            GraphName::DefaultGraph,
        ));
    }

    /// One net element from `a` to `b` (lon, lat), split into `pts` vertices.
    fn element(&mut self, a: (f64, f64), b: (f64, f64)) -> NamedNode {
        let id = self.elements;
        self.elements += 1;
        let ne = Self::nn(format!("{BASE}ne/{id}"));
        let geom = Self::nn(format!("{BASE}ne/{id}/geom"));
        let mid = ((a.0 + b.0) / 2.0 + 0.0003, (a.1 + b.1) / 2.0);
        let length = haversine(a, mid) + haversine(mid, b);
        self.add(
            &ne,
            rdf::TYPE.as_str(),
            Self::nn(format!("{ERA}LinearElement")),
        );
        self.add(
            &ne,
            &format!("{ERA}lengthOfNetLinearElement"),
            Literal::new_typed_literal(format!("{length:.1}"), xsd::DOUBLE),
        );
        self.add(&ne, &format!("{GSP}hasGeometry"), geom.clone());
        self.add(
            &geom,
            &format!("{GSP}asWKT"),
            Literal::new_typed_literal(
                format!(
                    "LINESTRING({:.6} {:.6}, {:.6} {:.6}, {:.6} {:.6})",
                    a.0, a.1, mid.0, mid.1, b.0, b.1
                ),
                Self::nn(format!("{GSP}wktLiteral")),
            ),
        );
        ne
    }

    /// Net relation between the end (`origin_a = false`) or origin of `a` and of `b`.
    fn relation(
        &mut self,
        a: &NamedNode,
        origin_a: bool,
        b: &NamedNode,
        origin_b: bool,
        nav: &str,
    ) {
        let id = self.relations;
        self.relations += 1;
        let nr = Self::nn(format!("{BASE}nr/{id}"));
        self.add(
            &nr,
            rdf::TYPE.as_str(),
            Self::nn(format!("{ERA}NetRelation")),
        );
        self.add(&nr, &format!("{ERA}elementA"), a.clone());
        self.add(&nr, &format!("{ERA}elementB"), b.clone());
        self.add(
            &nr,
            &format!("{ERA}isOnOriginOfElementA"),
            Literal::from(origin_a),
        );
        self.add(
            &nr,
            &format!("{ERA}isOnOriginOfElementB"),
            Literal::from(origin_b),
        );
        self.add(
            &nr,
            &format!("{ERA}navigability"),
            Self::nn(format!("{NAV}{nav}")),
        );
    }
}

fn haversine(a: (f64, f64), b: (f64, f64)) -> f64 {
    let (lat1, lat2) = (a.1.to_radians(), b.1.to_radians());
    let h = ((lat2 - lat1) / 2.0).sin().powi(2)
        + lat1.cos() * lat2.cos() * ((b.0 - a.0).to_radians() / 2.0).sin().powi(2);
    2.0 * 6_371_008.8 * h.sqrt().asin()
}

/// A grid of `h` east-west and `v` north-south double-ended lines, `k` elements between
/// crossings, and at every crossing a link element with a switch at each end.
pub fn generate(h: usize, v: usize, k: usize) -> Gen {
    let mut g = Gen {
        quads: Vec::new(),
        elements: 0,
        relations: 0,
    };
    let (lon0, lat0) = (5.0, 58.0);
    // ~500 m elements at 60°N, squeezed north-south for very large grids so latitudes stay valid.
    let dlon = 0.009;
    let dlat = 0.0045_f64.min(25.0 / ((h + 1) * k) as f64);
    let span = k as f64;
    // horizontal[i][j] = element j on line i; crossing c of line i is at element (c+1)*k - 1's end.
    let mut horizontal = Vec::with_capacity(h);
    for i in 0..h {
        let lat = lat0 + (i as f64 + 0.5) * span * dlat;
        let n = (v + 1) * k;
        let line: Vec<NamedNode> = (0..n)
            .map(|j| {
                g.element(
                    (lon0 + j as f64 * dlon, lat),
                    (lon0 + (j + 1) as f64 * dlon, lat),
                )
            })
            .collect();
        for w in line.windows(2) {
            g.relation(&w[0], false, &w[1], true, "Both");
        }
        horizontal.push(line);
    }
    let mut vertical = Vec::with_capacity(v);
    for c in 0..v {
        let lon = lon0 + ((c + 1) * k) as f64 * dlon + 0.5 * dlon;
        let n = (h + 1) * k;
        let line: Vec<NamedNode> = (0..n)
            .map(|j| {
                let lat = |j: usize| lat0 + j as f64 * dlat - 0.5 * span * dlat + 0.5 * span * dlat;
                g.element((lon, lat(j)), (lon, lat(j + 1)))
            })
            .collect();
        for w in line.windows(2) {
            g.relation(&w[0], false, &w[1], true, "Both");
        }
        vertical.push(line);
    }
    // At every crossing four link elements, one per turn, each with a switch at both ends:
    // the trunk is navigable onto the link, the straight-through leg to the link is not.
    for i in 0..h {
        for c in 0..v {
            let xh = horizontal[i][(c + 1) * k - 1].clone();
            let sh = horizontal[i][(c + 1) * k].clone();
            let xv = vertical[c][(i + 1) * k - 1].clone();
            let sv = vertical[c][(i + 1) * k].clone();
            let p = (
                lon0 + ((c + 1) * k) as f64 * dlon,
                lat0 + (i as f64 + 0.5) * span * dlat,
            );
            let q = (p.0 + 0.3 * dlon, p.1 + 0.3 * dlat);
            // east -> north (and south -> west)
            let l1 = g.element(p, q);
            g.relation(&xh, false, &l1, true, "Both");
            g.relation(&l1, false, &sv, true, "Both");
            g.relation(&sh, true, &l1, true, "None");
            // north -> east (and west -> south)
            let l2 = g.element(q, p);
            g.relation(&xv, false, &l2, true, "Both");
            g.relation(&l2, false, &sh, true, "Both");
            g.relation(&sv, true, &l2, true, "None");
            // east -> south (and north -> west)
            let l3 = g.element(p, (q.0, p.1 - 0.3 * dlat));
            g.relation(&xh, false, &l3, true, "Both");
            g.relation(&l3, false, &xv, false, "Both");
            g.relation(&sh, true, &l3, true, "None");
            // west -> north (and south -> east)
            let l4 = g.element(p, (p.0 - 0.3 * dlon, q.1));
            g.relation(&sh, true, &l4, true, "Both");
            g.relation(&l4, false, &sv, true, "Both");
            g.relation(&xh, false, &l4, true, "None");
        }
    }
    g
}
