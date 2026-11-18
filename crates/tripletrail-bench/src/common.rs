//! Helpers shared by the benchmark binaries.

use std::collections::hash_map::DefaultHasher;
use std::hash::{Hash, Hasher};
use std::time::{Duration, Instant};
use tripletrail::Engine;
use tripletrail::oxigraph::sparql::QueryResults;

pub struct Rng(pub u64);

impl Rng {
    pub fn below(&mut self, n: usize) -> usize {
        self.0 ^= self.0 << 13;
        self.0 ^= self.0 >> 7;
        self.0 ^= self.0 << 17;
        (self.0 % n as u64) as usize
    }
}

pub fn count(e: &Engine, q: &str) -> (usize, Duration) {
    let (n, t, _) = count_digest(e, q);
    (n, t)
}

/// Runs `q` and returns the number of solutions, the time and a digest of the solutions that
/// does not depend on their order (a sum of per-row hashes), taken after the clock stops.
pub fn count_digest(e: &Engine, q: &str) -> (usize, Duration, u64) {
    let t = Instant::now();
    let QueryResults::Solutions(s) = e.query(q).unwrap() else {
        panic!()
    };
    let rows: Vec<_> = s.map(|r| r.unwrap()).collect();
    let elapsed = t.elapsed();
    let digest = rows.iter().fold(0u64, |acc, r| {
        let mut h = DefaultHasher::new();
        for (v, t) in r.iter() {
            v.as_str().hash(&mut h);
            t.to_string().hash(&mut h);
        }
        acc.wrapping_add(h.finish())
    });
    (rows.len(), elapsed, digest)
}

#[allow(dead_code)] // used by the rinf binary only
pub fn rss_mb() -> Option<f64> {
    let s = std::fs::read_to_string("/proc/self/status").ok()?;
    let line = s.lines().find(|l| l.starts_with("VmRSS:"))?;
    Some(line.split_whitespace().nth(1)?.parse::<f64>().ok()? / 1024.0)
}

pub fn first_value(e: &Engine, q: &str) -> (String, Duration) {
    let t = Instant::now();
    let QueryResults::Solutions(mut s) = e.query(q).unwrap() else {
        panic!()
    };
    let v = s.next().unwrap().unwrap().values()[0]
        .as_ref()
        .map_or("unbound".into(), |t| t.to_string());
    (v, t.elapsed())
}

pub fn ms(d: Duration) -> String {
    format!("{:.1} ms", d.as_secs_f64() * 1000.0)
}

pub fn percentile(v: &mut [Duration], p: f64) -> Duration {
    v.sort();
    v[((v.len() - 1) as f64 * p).round() as usize]
}

pub fn peak_rss_mb() -> Option<f64> {
    let s = std::fs::read_to_string("/proc/self/status").ok()?;
    let line = s.lines().find(|l| l.starts_with("VmHWM:"))?;
    Some(line.split_whitespace().nth(1)?.parse::<f64>().ok()? / 1024.0)
}

/// A network profile split into its PREFIX lines and its SELECT, so the SELECT can be nested as
/// the edge sub-select of a pgr SERVICE call.
pub fn split_profile(profile: &str) -> (String, String) {
    let (prefixes, select): (Vec<&str>, Vec<&str>) = profile
        .lines()
        .filter(|l| !l.starts_with('#'))
        .partition(|l| l.starts_with("PREFIX"));
    (prefixes.join("\n"), select.join("\n"))
}
