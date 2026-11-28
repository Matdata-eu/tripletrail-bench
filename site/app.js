// The benchmark dashboard: reads the CSV files of bench/v2/results/dashboard (copied to data/
// by build.py) and draws one tab per suite, each with a dataset-size toggle, a lead sentence and
// a grid of compact charts. Plain SVG, no dependencies.
"use strict";

const OURS = "tripletrail";
const ENGINES = ["tripletrail", "oxigraph", "qlever", "jena", "graphdb", "maplib", "postgis"];
const NAMES = {
  tripletrail: "TripleTrail", oxigraph: "Oxigraph", qlever: "QLever", jena: "Jena",
  graphdb: "GraphDB", maplib: "maplib", postgis: "PostGIS",
};
const name = (e) => NAMES[e] || e;
const color = (e) => ENGINES.includes(e) ? `var(--e-${e})` : "var(--e-other)";
const inOrder = (rows) => [...rows].sort((a, b) => rank(a.engine) - rank(b.engine));
const rank = (e) => { const i = ENGINES.indexOf(e); return i < 0 ? 99 : i; };

// ---------------------------------------------------------------------------------------------
// Data

function parseCSV(text) {
  const lines = text.trim().split(/\r?\n/).filter(Boolean);
  if (lines.length < 2) return [];
  const head = lines[0].split(",");
  return lines.slice(1).map((line) => {
    const cells = line.split(",");
    // The last column may hold free text with commas (bsbm_qmph's note): keep it whole.
    if (cells.length > head.length) cells.splice(head.length - 1, cells.length, cells.slice(head.length - 1).join(","));
    return Object.fromEntries(head.map((h, i) => [h, cells[i] ?? ""]));
  });
}

// The results shown: data/ is the latest; data/v/<commit>/ an earlier snapshot (versions.json,
// written by build.py --history, and the ?v= parameter of the page's URL).
let BASE = "data/";

async function load(file, base = BASE) {
  try {
    const r = await fetch(`${base}${file}`, { cache: "no-cache" });
    if (!r.ok) return [];
    return file.endsWith(".json") ? await r.json() : parseCSV(await r.text());
  } catch {
    return [];
  }
}

const num = (x) => { const v = parseFloat(x); return isFinite(v) && v > 0 ? v : null; };
const gmean = (xs) => { xs = xs.filter((x) => x > 0); return xs.length ? Math.exp(xs.reduce((a, x) => a + Math.log(x), 0) / xs.length) : null; };
const uniq = (xs) => [...new Set(xs)];
const ordered = (values, order) => uniq(values).sort((a, b) => {
  const i = order.indexOf(a), j = order.indexOf(b);
  return (i < 0 ? 99 : i) - (j < 0 ? 99 : j) || String(a).localeCompare(String(b));
});

// ---------------------------------------------------------------------------------------------
// Formatting and DOM

function fmt(v) {
  if (v == null || !isFinite(v)) return "–";
  const d = v >= 100 ? 0 : v >= 10 ? 1 : 2;
  return v.toLocaleString("en", { maximumFractionDigits: d, minimumFractionDigits: 0 });
}
const times = (r) => `${r >= 10 ? Math.round(r).toLocaleString("en") : r.toFixed(1)}×`;

const el = (tag, attrs = {}, ...kids) => {
  const e = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (v == null) continue;
    if (k === "text") e.textContent = v;
    else if (k === "class") e.className = v;
    else e.setAttribute(k, v);
  }
  for (const k of kids.flat(Infinity)) if (k != null && k !== false) e.append(k);
  return e;
};
const b = (text) => el("b", { text });
const SVGNS = "http://www.w3.org/2000/svg";
const svg = (tag, attrs = {}, text) => {
  const e = document.createElementNS(SVGNS, tag);
  for (const [k, v] of Object.entries(attrs)) e.setAttribute(k, v);
  if (text != null) e.textContent = text;
  return e;
};

const measureCtx = document.createElement("canvas").getContext("2d");
function textWidth(s, bold) {
  measureCtx.font = `${bold ? "600 " : ""}12px system-ui, -apple-system, "Segoe UI", sans-serif`;
  return measureCtx.measureText(s).width;
}

// A tooltip inside a chart box. lines: [[color|null, key, value]] or [null, text] for a wrapped note.
function tooltip(box) {
  const tip = el("div", { class: "tip", hidden: "" });
  box.append(tip);
  return {
    show(ev, title, lines) {
      tip.replaceChildren(el("div", { class: "t", text: title }));
      for (const line of lines) {
        if (line.length === 2) { tip.append(el("div", { class: "w", text: line[1] })); continue; }
        const [c, k, v] = line;
        tip.append(el("div", { class: "r" }, c ? el("span", { class: "sw", style: `background:${c}` }) : null,
          el("span", { text: k }), el("span", { text: v })));
      }
      tip.hidden = false;
      const r = box.getBoundingClientRect();
      const x = ev.clientX - r.left, y = ev.clientY - r.top;
      tip.style.left = `${Math.max(0, Math.min(x + 12, box.clientWidth - tip.offsetWidth))}px`;
      tip.style.top = `${y + 14}px`;
    },
    hide() { tip.hidden = true; },
  };
}

function niceStep(span, n) {
  const raw = span / Math.max(1, n);
  const p = 10 ** Math.floor(Math.log10(raw));
  const m = raw / p;
  return (m >= 5 ? 10 : m >= 2 ? 5 : m >= 1 ? 2 : 1) * p;
}

// A chart is a box whose drawing runs once it is in the page (it needs its width), and again
// when the window is resized.
function chart(draw) {
  const box = el("div", { class: "chart" });
  box._draw = () => { box.replaceChildren(); draw(box, Math.max(240, box.clientWidth)); };
  return box;
}

// Horizontal bars, one per engine. rows: [{engine, v (number or null), ...}]
function bars(rows, { label, tip, empty = "No results" } = {}) {
  return chart((box, W) => {
    if (!rows.length) { box.append(el("p", { class: "empty", text: empty })); return; }
    const bh = 18, gap = 8, H = rows.length * (bh + gap) + 18;
    const lw = Math.max(...rows.map((r) => textWidth(name(r.engine), r.engine === OURS)));
    const vw = Math.max(...rows.map((r) => textWidth(label(r))));
    const ml = lw + 10, mr = vw + 10;
    const max = Math.max(0, ...rows.map((r) => r.v || 0)) || 1;
    const x = (v) => ml + (W - ml - mr) * v / max;
    const s = svg("svg", { width: W, height: H, viewBox: `0 0 ${W} ${H}`, role: "img",
      "aria-label": rows.map((r) => `${name(r.engine)} ${label(r)}`).join(", ") });
    const step = niceStep(max, W < 400 ? 3 : 4);
    for (let t = 0; t <= max * 1.0001; t += step) {
      s.append(svg("line", { x1: x(t), x2: x(t), y1: 0, y2: H - 16, stroke: "var(--grid)" }));
      s.append(svg("text", { x: x(t), y: H - 3, "text-anchor": "middle" }, Number(t.toPrecision(6)).toLocaleString("en")));
    }
    const t = tooltip(box);
    rows.forEach((r, i) => {
      const y = i * (bh + gap);
      const ours = r.engine === OURS;
      s.append(svg("text", { x: ml - 10, y: y + bh / 2, dy: "0.35em", "text-anchor": "end", class: ours ? "ours" : "lab" }, name(r.engine)));
      if (r.v != null) s.append(svg("rect", { x: ml, y, height: bh, width: Math.max(2, x(r.v) - ml), rx: 3, fill: color(r.engine) }));
      s.append(svg("text", { x: (r.v == null ? ml : x(r.v)) + 6, y: y + bh / 2, dy: "0.35em", class: ours ? "ours" : "" }, label(r)));
      const hit = svg("rect", { x: 0, y: y - gap / 2, width: W, height: bh + gap, fill: "transparent" });
      hit.addEventListener("pointermove", (ev) => t.show(ev, name(r.engine), tip ? tip(r) : [[null, "Value", label(r)]]));
      hit.addEventListener("pointerleave", () => t.hide());
      s.append(hit);
    });
    box.append(s);
  });
}

// One row per group, one dot per engine, on a log scale. rows: [{group, engine, v, extra?}]
function dots(rows, groups, unit, { empty = "No timed runs" } = {}) {
  rows = rows.filter((r) => r.v != null && isFinite(r.v) && r.v > 0);
  return chart((box, W) => {
    if (!rows.length) { box.append(el("p", { class: "empty", text: empty })); return; }
    const by = new Map(groups.map((g) => [g, []]));
    for (const r of rows) if (by.has(r.group)) by.get(r.group).push(r);
    const shown = groups.filter((g) => by.get(g).length);
    const rh = 24, H = shown.length * rh + 20;
    const lw = Math.min(W * 0.45, Math.max(...shown.map((g) => textWidth(g))));
    const ml = lw + 12, mr = 14;
    const lo = Math.min(...rows.map((r) => r.v)) * 0.8, hi = Math.max(...rows.map((r) => r.v)) * 1.25;
    const x = (v) => ml + (W - ml - mr) * Math.log(v / lo) / Math.log(hi / lo);
    const s = svg("svg", { width: W, height: H, viewBox: `0 0 ${W} ${H}`, role: "img",
      "aria-label": `Log-scale times in ${unit} per row; hover a row for every engine's value` });
    const inside = (ts) => ts.filter((v) => v >= lo && v <= hi);
    const crowded = (ts) => ts.length > 2 && (W - ml - mr) / ts.length < 56;
    let ticks = inside([-3, -2, -1, 0, 1, 2, 3, 4, 5, 6, 7].flatMap((p) => [1, 2, 5].map((m) => Number((m * 10 ** p).toPrecision(1)))));
    if (crowded(ticks)) ticks = inside([-3, -2, -1, 0, 1, 2, 3, 4, 5, 6, 7].map((p) => Number((10 ** p).toPrecision(1))));
    while (crowded(ticks)) ticks = ticks.filter((_, i) => i % 2 === 0);
    ticks.forEach((v, i) => {
      s.append(svg("line", { x1: x(v), x2: x(v), y1: 0, y2: H - 16, stroke: "var(--grid)" }));
      s.append(svg("text", { x: x(v), y: H - 3, "text-anchor": "middle" }, v.toLocaleString("en")));
    });
    const t = tooltip(box);
    shown.forEach((g, i) => {
      const y = i * rh, list = by.get(g);
      const row = svg("g", {});
      const hl = svg("rect", { x: ml - 6, y: y + 2, width: W - ml - mr + 12, height: rh - 4, rx: 4, fill: "var(--grid)", opacity: 0 });
      row.append(hl);
      let labelText = g;
      while (textWidth(labelText) > lw && labelText.length > 4) labelText = labelText.slice(0, -2) + "…";
      row.append(svg("text", { x: ml - 12, y: y + rh / 2, dy: "0.35em", "text-anchor": "end", class: "lab" }, labelText));
      const vs = list.map((r) => r.v);
      row.append(svg("line", { x1: x(Math.min(...vs)), x2: x(Math.max(...vs)), y1: y + rh / 2, y2: y + rh / 2, stroke: "var(--axis)" }));
      // TripleTrail last, so it is drawn on top.
      for (const r of [...list].sort((a, b) => rank(b.engine) - rank(a.engine))) {
        row.append(svg("circle", { cx: x(r.v), cy: y + rh / 2, r: r.engine === OURS ? 6 : 4.5, fill: color(r.engine),
          stroke: "var(--panel)", "stroke-width": 1.5 }));
      }
      const hit = svg("rect", { x: 0, y, width: W, height: rh, fill: "transparent" });
      hit.addEventListener("pointermove", (ev) => {
        hl.setAttribute("opacity", 0.8);
        t.show(ev, g, [...list].sort((a, b) => a.v - b.v).map((r) => [color(r.engine), name(r.engine), `${fmt(r.v)} ${unit}${r.extra || ""}`]));
      });
      hit.addEventListener("pointerleave", () => { hl.setAttribute("opacity", 0); t.hide(); });
      row.append(hit);
      s.append(row);
    });
    box.append(s);
  });
}

function table(rows, cols) {
  const t = el("table", {}, el("thead", {}, el("tr", {}, cols.map((c) => el("th", { class: c.l ? "l" : null, text: c.label })))));
  const body = el("tbody");
  for (const r of rows) {
    body.append(el("tr", { class: r.engine === OURS ? "ours" : null }, cols.map((c) => {
      const v = c.get(r);
      return el("td", { class: [c.l ? "l" : "", c.cls ? c.cls(r) : ""].join(" ").trim() || null },
        v instanceof Node ? v : document.createTextNode(v ?? ""));
    })));
  }
  t.append(body);
  return el("div", { class: "tablewrap" }, t);
}

const card = (id, title, note, ...body) => el("section", { class: "card", id }, el("h2", { text: title }),
  note ? el("p", { class: "note" }, note) : null, ...body);
const grid = (cls, ...cards) => el("div", { class: `grid ${cls || ""}`.trim() }, ...cards);

// "TripleTrail X; the fastest other engine, E, Y: TripleTrail is k× faster." One clause.
function versus(rows, { field, lower = true, unit, what }) {
  const ours = rows.find((r) => r.engine === OURS);
  const others = rows.filter((r) => r.engine !== OURS && r[field] != null);
  if (!ours || ours[field] == null || !others.length) return null;
  const best = others.sort((a, b) => lower ? a[field] - b[field] : b[field] - a[field])[0];
  const ratio = lower ? best[field] / ours[field] : ours[field] / best[field];
  const u = unit ? ` ${unit}` : "";
  return [
    `${what} TripleTrail `, b(`${fmt(ours[field])}${u}`), `, the best other engine (${name(best.engine)}) `,
    b(`${fmt(best[field])}${u}`), ": TripleTrail is ",
    b(ratio >= 1 ? `${times(ratio)} ${lower ? "faster" : "ahead"}` : `${times(1 / ratio)} ${lower ? "slower" : "behind"}`), ". ",
  ];
}

// Where a tab's results ran. A later run of some engines only (TripleTrail alone, say) replaces
// only their results, so a tab can come from several runs: name each with its engines.
function provLine(prov, suite, dataset) {
  const ps = prov.filter((r) => r.suite === suite && r.dataset === dataset);
  if (!ps.length) return null;
  const commit = (p) => p.commit ? el("a", { href: `https://github.com/Matdata-eu/tripletrail/commit/${p.commit}`, text: p.commit.slice(0, 8) }) : "an unrecorded commit";
  const machines = uniq(ps.map((p) => `${p.machine || "?"}${p.cpus ? ` (${p.cpus} vCPU)` : ""}`));
  const at = (p) => [commit(p), p.date ? `, ${p.date}` : ""];
  if (ps.length === 1) return el("p", { class: "prov" }, "Ran on ", b(machines[0]), " with TripleTrail at ", ...at(ps[0]), ".");
  // The run that measured TripleTrail first, then the others.
  const sorted = [...ps].sort((x, y) => (y.engines || "").split(" ").includes(OURS) - (x.engines || "").split(" ").includes(OURS));
  const parts = sorted.map((p) => {
    const es = (p.engines || "").split(" ").filter(Boolean);
    return [" ", b(`${inOrder(es.map((engine) => ({ engine }))).map((r) => name(r.engine)).join(", ") || "Other engines"}:`),
      " run of ", p.date || "an unrecorded date", " with TripleTrail at ", commit(p), "."];
  });
  return el("p", { class: "prov" }, "Ran on ", b(machines.join(", ")), ".", ...parts.flat());
}

// ---------------------------------------------------------------------------------------------
// Suites. Each returns {label, sizes: [[value, label]], build(size) -> nodes} or null.

const SQ_SIZES = { "bsbm-2785": "BSBM 1M (synthetic)", "rinf-0076": "RINF 0076 (1.6M real triples)" };
const BSBM_SIZES = { "bsbm-2785": "1M triples (2,785 products)", "bsbm-28480": "10M triples (28,480 products)" };
const TM_SIZES = { medium: "Medium (98K triples)", large: "Large (1M)", xlarge: "XLarge (10M)" };
const SP_SIZES = { small: "Small (0.8M, synthetic rail)", large: "Large (10.5M, synthetic rail)",
  osm_norway: "OSM Norway (1.5M)", osm_benelux: "OSM Benelux", osm_europe: "OSM Europe (1B)" };
const RS_SIZES = { "rinf-all": "RINF, all countries" };
// The size each tab opens on: the main dataset of each suite.
const DEFAULT_SIZE = { sparqloscope: "bsbm-2785", bsbm: "bsbm-2785", trainmarks: "large", spatial: "large", routing: "large", rinfshapes: "rinf-all" };
const sizeList = (values, labels) => ordered(values, Object.keys(labels)).map((v) => [v, labels[v] || v.replace(/^bsbm-(\d+)$/, "$1 products")]);

function sparqloscope(D) {
  if (!D.sq.length) return null;
  return {
    label: "Sparqloscope", toggleLabel: "Dataset",
    sizes: sizeList(D.sq.map((r) => r.dataset), SQ_SIZES),
    build(ds) {
      const rows = inOrder(D.sq.filter((r) => r.dataset === ds)).map((r) => ({
        engine: r.engine, geomean_ms: num(r.geomean_ms), load_s: num(r.load_s),
        answered: +r.answered || 0, timed_out: +r.timed_out || 0, failed: +r.failed || 0,
      }));
      const tipLines = (r) => [[null, "Geometric mean", `${fmt(r.geomean_ms)} ms`], [null, "Load", `${fmt(r.load_s)} s`],
        [null, "Answered", `${r.answered} of ${r.answered + r.timed_out + r.failed}`], [null, "Timed out", String(r.timed_out)]];
      const cats = D.cats.filter((r) => r.dataset === ds).map((r) => ({ group: r.category, engine: r.engine, v: num(r.ms) }));
      return [
        el("p", { class: "lead" }, versus(rows, { field: "geomean_ms", unit: "ms", what: "Geometric mean over the feature-isolating queries:" }),
          "Lower is better."),
        provLine(D.prov, "sparqloscope", ds),
        grid("three",
          card("sq-geomean", "Geometric mean per engine", "All queries, cold, ms.",
            bars(rows.map((r) => ({ ...r, v: r.geomean_ms })), { label: (r) => `${fmt(r.v)} ms`, tip: tipLines })),
          card("sq-load", "Load time", "Bulk load into the engine's store, seconds.",
            bars(rows.map((r) => ({ ...r, v: r.load_s })), { label: (r) => `${fmt(r.v)} s`, tip: tipLines })),
          card("sq-table", "Answers", "A query counts as timed out after the suite's limit.",
            table(rows, [
              { label: "Engine", l: true, get: (r) => name(r.engine) },
              { label: "Answered", get: (r) => String(r.answered) },
              { label: "Timed out", get: (r) => String(r.timed_out) },
              { label: "Failed", get: (r) => String(r.failed) },
            ]))),
        card("sq-categories", "Geometric mean per query category", "ms per category, log scale. Hover a row for every engine.",
          dots(cats, uniq(cats.map((r) => r.group)), "ms")),
      ];
    },
  };
}

function bsbm(D) {
  if (!D.qmph.length) return null;
  return {
    label: "BSBM", toggleLabel: "Scale",
    sizes: sizeList(D.qmph.map((r) => r.scale), BSBM_SIZES),
    build(scale) {
      const uc = (u) => inOrder(D.qmph.filter((r) => r.scale === scale && r.usecase === u))
        .map((r) => ({ engine: r.engine, qmph: num(r.qmph), note: r.note }));
      const qmphBars = (u) => bars(uc(u).map((r) => ({ ...r, v: r.qmph })), {
        label: (r) => r.v == null ? "not run" : `${Math.round(r.v).toLocaleString("en")}${r.note ? " *" : ""}`,
        tip: (r) => [[null, "QMpH", r.v == null ? "not run" : Math.round(r.v).toLocaleString("en")]].concat(r.note ? [[null, r.note]] : []),
      });
      // Full mixes only for the lead sentence: an engine that skipped templates ran a lighter mix.
      const full = (u) => uc(u).filter((r) => !r.note);
      const aqet = D.aqet.filter((r) => r.scale === scale && num(r.ms));
      const geo = (u) => {
        const rows = aqet.filter((r) => r.usecase === u);
        const engines = uniq(rows.map((r) => r.engine));
        const common = uniq(rows.map((r) => r.query)).filter((q) => engines.every((e) => rows.some((r) => r.query === q && r.engine === e)));
        return inOrder(engines.map((e) => ({ engine: e, n: common.length,
          v: gmean(rows.filter((r) => r.engine === e && common.includes(r.query)).map((r) => num(r.ms))) })));
      };
      const geoBars = (u) => bars(geo(u), { label: (r) => `${fmt(r.v)} ms`,
        tip: (r) => [[null, "Geometric mean", `${fmt(r.v)} ms`], [null, "Over templates", String(r.n)]] });
      const perTemplate = (u) => {
        const rows = aqet.filter((r) => r.usecase === u).map((r) => ({ group: r.query, engine: r.engine, v: num(r.ms) }));
        const qs = uniq(rows.map((r) => r.group)).sort((a, c) => parseInt(a.slice(1)) - parseInt(c.slice(1)));
        return dots(rows, qs, "ms");
      };
      const nGeo = (u) => geo(u)[0]?.n ?? "the";
      return [
        el("p", { class: "lead" },
          versus(full("explore"), { field: "qmph", lower: false, what: "Explore mixes per hour:" }),
          versus(full("bi"), { field: "qmph", lower: false, what: "Business intelligence mixes per hour:" }),
          "Higher is better; engines that skipped templates (marked *) are left out of this comparison."),
        provLine(D.prov, "bsbm", scale.replace(/^bsbm-/, "")),
        grid("three",
          card("bsbm-explore", "Explore", "Query mixes per hour, higher is better. * = ran without some templates; hover for why.", qmphBars("explore")),
          card("bsbm-bi", "Business intelligence", "Query mixes per hour, higher is better.", qmphBars("bi")),
          card("bsbm-update", "Explore and update", "Query mixes per hour, higher is better.", qmphBars("update"))),
        grid("",
          card("bsbm-geo-explore", "Explore: geometric mean per engine", `Average time per template, ms, over the ${nGeo("explore")} templates every engine ran.`, geoBars("explore")),
          card("bsbm-geo-bi", "Business intelligence: geometric mean per engine", `Average time per template, ms, over the ${nGeo("bi")} templates every engine ran.`, geoBars("bi"))),
        grid("",
          card("bsbm-aqet-explore", "Explore: time per template", "Average query execution time, ms, log scale.", perTemplate("explore")),
          card("bsbm-aqet-bi", "Business intelligence: time per template", "Average query execution time, ms, log scale.", perTemplate("bi"))),
      ];
    },
  };
}

const plural = (n, one, many) => `${n} ${n === 1 ? one : many}`;
const ratioText = (r) => r >= 1 ? `${times(r)} faster than` : `${times(1 / r)} slower than`;

// Trainmarks: geometric mean of the warm medians of the read queries (the update left out).
function tmGeo(D, scale) {
  const q = D.tq.filter((r) => r.scale === scale);
  const isRead = (r) => !/delete|insert|update/i.test(r.query);
  const reads = q.filter((r) => isRead(r) && num(r.warm_ms));
  const nq = uniq(q.filter(isRead).map((r) => r.query)).length;
  return inOrder(uniq(reads.map((r) => r.engine)).map((e) => {
    const rs = reads.filter((r) => r.engine === e);
    return { engine: e, geomean_ms: gmean(rs.map((r) => num(r.warm_ms))), answered: rs.length, of: nq };
  }));
}

// Spatial: answered queries of one dataset, and two ways to compare engines on them.
const spOk = (q) => q.filter((r) => (r.status || "ok") === "ok" && num(r.p50_ms));
// Over the queries every engine answered, so each engine is timed on the same questions.
function spCommon(q) {
  const ok = spOk(q);
  const engines = ordered(q.map((r) => r.engine), ENGINES);
  const common = uniq(ok.map((r) => r.query)).filter((qq) => engines.every((e) => ok.some((r) => r.query === qq && r.engine === e)));
  const geo = engines.map((e) => ({ engine: e, geomean_ms: gmean(ok.filter((r) => r.engine === e && common.includes(r.query)).map((r) => num(r.p50_ms))), n: common.length }))
    .filter((r) => r.geomean_ms != null);
  return { common, geo };
}
// Pairwise: TripleTrail against each engine over the queries both answered (as summary.py does).
function spPairwise(q) {
  const ok = spOk(q);
  const time = (e, qq) => num(ok.find((r) => r.engine === e && r.query === qq)?.p50_ms);
  return ordered(ok.map((r) => r.engine), ENGINES).filter((e) => e !== OURS).map((e) => {
    const both = uniq(ok.map((r) => r.query)).filter((qq) => time(OURS, qq) && time(e, qq));
    if (!both.length) return null;
    const ours = gmean(both.map((qq) => time(OURS, qq))), theirs = gmean(both.map((qq) => time(e, qq)));
    return { engine: e, n: both.length, ours, theirs, speedup: theirs / ours };
  }).filter(Boolean);
}

function trainmarks(D) {
  if (!D.tload.length && !D.tq.length) return null;
  return {
    label: "Trainmarks", toggleLabel: "Scale",
    sizes: sizeList([...D.tload, ...D.tq].map((r) => r.scale), TM_SIZES),
    build(scale) {
      const loads = inOrder(D.tload.filter((r) => r.scale === scale).map((r) => ({ engine: r.engine, load_s: num(r.load_s) })));
      const q = D.tq.filter((r) => r.scale === scale);
      const geo = tmGeo(D, scale);
      const perQuery = q.map((r) => ({ group: r.query, engine: r.engine, v: num(r.warm_ms),
        extra: num(r.cold_ms) ? ` (cold ${fmt(num(r.cold_ms))})` : "" }));
      return [
        el("p", { class: "lead" },
          versus(loads, { field: "load_s", unit: "s", what: "Load:" }),
          versus(geo.filter((r) => r.answered === r.of), { field: "geomean_ms", unit: "ms", what: "Geometric mean of the warm read queries:" }),
          "Lower is better."),
        provLine(D.prov, "trainmarks", scale),
        grid("",
          card("tm-geo", "Geometric mean of query times", "Warm medians of the read queries, ms. * = did not answer all of them.",
            bars(geo.map((r) => ({ ...r, v: r.geomean_ms })), { label: (r) => `${fmt(r.v)} ms${r.answered < r.of ? " *" : ""}`,
              tip: (r) => [[null, "Geometric mean", `${fmt(r.v)} ms`], [null, "Queries answered", `${r.answered} of ${r.of}`]] })),
          card("tm-load", "Load time", "Bulk load of the N-Triples file, seconds.",
            bars(loads.map((r) => ({ ...r, v: r.load_s })), { label: (r) => `${fmt(r.v)} s` }))),
        card("tm-queries", "Time per query", "Median of the warm runs, ms, log scale; the update runs once. Hover for the cold run.",
          dots(perQuery, uniq(perQuery.map((r) => r.group)), "ms")),
      ];
    },
  };
}

const FAMILIES = [
  ["1 selection", "Features inside a bounding box or polygon, or within a distance of a point: the spatial index on a filter."],
  ["2 knn", "The nearest signals and operational points to a random point, in order."],
  ["3 join", "Spatial joins between two whole classes, such as signals within 20 m of a network element."],
  ["4 aggregate", "Geometry arithmetic over many features: lengths per region, total length, area of a union of buffers."],
  ["5 linear referencing", "Railway kilometre positions: the point at a kilometre, the assets between two kilometres."],
  ["6 routing", "Network analysis on the track graph, the same functions as pgRouting. Only TripleTrail and PostGIS/pgRouting run it."],
  ["7 mixed", "Routing and spatial in one query: the signals near a shortest route."],
  ["8 osm", "Spatial joins on real OpenStreetMap data: stations per area, track length per land use, tracks near tracks."],
  ["9 scale", "Scans, groups and lookups on a store larger than its memory limit."],
];

function spatial(D) {
  if (!D.sload.length && !D.squeries.length) return null;
  return {
    label: "Spatial", toggleLabel: "Dataset",
    sizes: sizeList([...D.sload, ...D.squeries].map((r) => r.dataset), SP_SIZES),
    build(ds) {
      const loads = inOrder(D.sload.filter((r) => r.dataset === ds).map((r) => ({
        engine: r.engine, load_s: num(r.load_s), disk_gib: num(r.disk_gib), triples: num(r.triples) })));
      const q = D.squeries.filter((r) => r.dataset === ds);
      const ok = spOk(q);
      const engines = ordered(q.map((r) => r.engine), ENGINES);
      const { common, geo } = spCommon(q);
      const pairs = spPairwise(q);
      const nCommon = plural(common.length, "query", "queries");
      const total = uniq(q.map((r) => r.query)).length;
      const summary = engines.map((e) => {
        const mine = q.filter((r) => r.engine === e);
        const l = loads.find((r) => r.engine === e) || {};
        return { engine: e, answered: mine.filter((r) => (r.status || "ok") === "ok").length, of: total,
          timeout: mine.filter((r) => /time/i.test(r.status)).length, load_s: l.load_s, disk_gib: l.disk_gib,
          geomean_ms: geo.find((g) => g.engine === e)?.geomean_ms };
      });
      const fams = [];
      for (const [fam, rows] of groupBy(q, (r) => r.family)) {
        const of = uniq(rows.map((r) => r.query)).length;
        for (const e of engines) {
          const rs = rows.filter((r) => r.engine === e && (r.status || "ok") === "ok" && num(r.p50_ms));
          if (rs.length) fams.push({ group: fam, engine: e, v: gmean(rs.map((r) => num(r.p50_ms))), extra: ` (${rs.length} of ${of})` });
        }
      }
      const famOrder = uniq(fams.map((r) => r.group)).sort();
      const perQuery = ok.map((r) => ({ group: r.query, engine: r.engine, v: num(r.p50_ms), family: r.family,
        extra: num(r.cold_ms) ? ` (cold ${fmt(num(r.cold_ms))})` : "" }));
      const queryOrder = uniq([...q].sort((a, c) => a.family.localeCompare(c.family)).map((r) => r.query));
      const ourLoad = loads.find((r) => r.engine === OURS);
      return [
        el("p", { class: "lead" },
          ourLoad?.triples ? ["The dataset holds ", b(Math.round(ourLoad.triples).toLocaleString("en")), " triples. "] : null,
          versus(geo, { field: "geomean_ms", unit: "ms", what: `Geometric mean of the warm medians over the ${nCommon} every engine answered:` }),
          pairs.length ? ["Pairwise, over the queries TripleTrail and each engine both answered (routing only runs on PostGIS), TripleTrail is ",
            pairs.flatMap((p, i) => [i ? (i === pairs.length - 1 ? " and " : ", ") : "", b(ratioText(p.speedup)), ` ${name(p.engine)} (${plural(p.n, "query", "queries")})`]), ". "] : null,
          versus(loads, { field: "load_s", unit: "s", what: "Load:" }),
          "Lower is better."),
        provLine(D.prov, "v2", ds),
        grid("three",
          card("sp-geomean", "Geometric mean per engine", `Warm medians, ms, over the ${nCommon} every engine answered.`,
            bars(geo.map((r) => ({ ...r, v: r.geomean_ms })), { label: (r) => `${fmt(r.v)} ms`, empty: "No query every engine answered",
              tip: (r) => [[null, "Geometric mean", `${fmt(r.v)} ms`], [null, "Over queries", String(r.n)]] })),
          card("sp-load", "Load time", "Bulk load into the engine's store, seconds. PostGIS loads tables, not triples.",
            bars(loads.map((r) => ({ ...r, v: r.load_s })), { label: (r) => `${fmt(r.v)} s`,
              tip: (r) => [[null, "Load", `${fmt(r.v)} s`], [null, "On disk", `${fmt(r.disk_gib)} GiB`]]
                .concat(r.triples ? [[null, "Triples", Math.round(r.triples).toLocaleString("en")]] : []) })),
          card("sp-table", "Answers", "Queries answered of those asked on this dataset; the rest were not supported, failed or timed out.",
            table(summary, [
              { label: "Engine", l: true, get: (r) => name(r.engine) },
              { label: "Answered", get: (r) => `${r.answered} / ${r.of}` },
              { label: "Timed out", get: (r) => String(r.timeout) },
              { label: "On disk", get: (r) => r.disk_gib ? `${fmt(r.disk_gib)} GiB` : "–" },
            ]))),
        grid("",
          card("sp-families", "Geometric mean per query family", "Warm medians, ms, log scale, over the family's queries each engine answered (hover for how many).",
            dots(fams, famOrder, "ms"),
            el("details", {}, el("summary", { text: "What the families measure" }),
              el("dl", {}, FAMILIES.filter(([f]) => famOrder.includes(f)).flatMap(([f, d]) => [el("dt", { text: f }), el("dd", { text: d })])))),
          card("sp-queries", "Time per query", "Warm median, ms, log scale; hover for the cold first run. Queries an engine did not answer are left out.",
            dots(perQuery, queryOrder, "ms"))),
      ];
    },
  };
}

// Routing: the routing and mixed families of the spatial benchmark on their own, TripleTrail
// against pgRouting, warm and cold side by side. The RDF engines have no routing, so on the
// Spatial tab these queries hide among the others.
const RT_FAMILIES = ["6 routing", "7 mixed"];
function routing(D) {
  const all = D.squeries.filter((r) => RT_FAMILIES.includes(r.family) && (r.engine === OURS || r.engine === "postgis"));
  if (!all.some((r) => r.engine === OURS && num(r.p50_ms))) return null;
  return {
    id: "routing", label: "Routing", toggleLabel: "Dataset",
    sizes: sizeList(all.map((r) => r.dataset), SP_SIZES),
    build(ds) {
      const q = all.filter((r) => r.dataset === ds);
      const get = (e, qq) => q.find((r) => r.engine === e && r.query === qq) || {};
      const queries = uniq(q.map((r) => r.query));
      const rows = queries.map((qq) => {
        const t = get(OURS, qq), p = get("postgis", qq);
        return { query: qq, t_warm: num(t.p50_ms), t_cold: num(t.cold_ms), p_warm: num(p.p50_ms), p_cold: num(p.cold_ms),
          p_status: p.status || "not run" };
      });
      const both = rows.filter((r) => r.t_warm && r.p_warm);
      const ratio = (a, b2) => a && b2 ? ratioText(b2 / a) : "–";
      const gw = both.length ? gmean(both.map((r) => r.p_warm)) / gmean(both.map((r) => r.t_warm)) : null;
      const bc = both.filter((r) => r.t_cold && r.p_cold);
      const gc = bc.length ? gmean(bc.map((r) => r.p_cold)) / gmean(bc.map((r) => r.t_cold)) : null;
      const ms = (v) => v ? `${fmt(v)} ms` : "–";
      const perQuery = spOk(q).map((r) => ({ group: r.query, engine: r.engine, v: num(r.p50_ms),
        extra: num(r.cold_ms) ? ` (cold ${fmt(num(r.cold_ms))})` : "" }));
      return [
        el("p", { class: "lead" },
          "TripleTrail's routing functions against PostGIS with pgRouting, on the same track graph and the same route pairs; the RDF engines have no routing. ",
          gw ? ["Over the ", b(plural(both.length, "query", "queries")), " both answered, TripleTrail is ", b(ratioText(gw)),
            " pgRouting warm (geometric mean of the warm medians)", gc ? [" and ", b(ratioText(gc)), " pgRouting on the cold first run"] : "", ". "] : null,
          "Lower is better."),
        el("p", { class: "note" },
          "How they differ: pgRouting builds its graph from an SQL edge query on every call, which is most of its time on a single route. ",
          "TripleTrail builds a named network once, on the first routing query after a restart, and keeps it in memory: that build is in TripleTrail's cold time, not in its warm times. ",
          "route_ch uses contraction hierarchies, which pgRouting does not have; it has no pgRouting time."),
        provLine(D.prov, "v2", ds),
        card("rt-table", "Per query", "Warm median and cold first run, ms. The ratio compares the warm medians.",
          table(rows, [
            { label: "Query", l: true, get: (r) => r.query },
            { label: "TripleTrail warm", get: (r) => ms(r.t_warm) },
            { label: "TripleTrail cold", get: (r) => ms(r.t_cold) },
            { label: "pgRouting warm", get: (r) => r.p_warm ? ms(r.p_warm) : r.p_status },
            { label: "pgRouting cold", get: (r) => ms(r.p_cold) },
            { label: "TripleTrail is", get: (r) => ratio(r.t_warm, r.p_warm) },
          ])),
        card("rt-queries", "Time per query", "Warm median, ms, log scale; hover for the cold first run.",
          dots(perQuery, queries, "ms")),
      ];
    },
  };
}

// RINF shapes: the suite's queries grouped by shape, each ablation control right after the
// query it controls.
const RS_SHAPES = {
  facet: "Facet over a big class", topk: "Top-k over a star", star: "Star with combined filters",
  chain: "Chain", wide: "Wide table with OPTIONALs", anti: "Anti-join", control: "Ablation controls",
};
const rsAnswered = (r) => r.status === "ok" || r.status === "forms differ";

function rsQueries(q) {
  const first = new Map();
  q.forEach((r, i) => { if (!first.has(r.query)) first.set(r.query, { ...r, i }); });
  const all = [...first.values()];
  const shapeRank = (s) => { const i = Object.keys(RS_SHAPES).indexOf(s); return i < 0 ? 99 : i; };
  const main = all.filter((r) => !r.control_of || !first.has(r.control_of))
    .sort((a, c) => shapeRank(a.shape) - shapeRank(c.shape) || a.i - c.i);
  const out = [];
  for (const r of main) {
    out.push(r);
    out.push(...all.filter((c) => c.control_of === r.query).sort((a, c) => a.i - c.i));
  }
  return out;
}

function rinfshapes(D) {
  if (!D.rs.length) return null;
  return {
    id: "rinfshapes", label: "RINF shapes", toggleLabel: "Dataset",
    sizes: sizeList(D.rs.map((r) => r.dataset), RS_SIZES),
    build(ds) {
      const q = D.rs.filter((r) => r.dataset === ds);
      const engines = ordered(q.map((r) => r.engine), ENGINES);
      const queries = rsQueries(q);
      const cell = (qid, e) => q.find((r) => r.query === qid && r.engine === e);
      const ok = q.filter((r) => rsAnswered(r) && num(r.rows_ms));
      const common = queries.map((r) => r.query).filter((qid) => engines.every((e) => ok.some((r) => r.query === qid && r.engine === e)));
      const geo = inOrder(engines.map((e) => ({ engine: e, n: common.length,
        v: gmean(ok.filter((r) => r.engine === e && common.includes(r.query)).map((r) => num(r.rows_ms))) })).filter((r) => r.v != null));
      const label = (r) => (r.control_of ? `↳ ${r.query}` : r.query);
      const perQuery = ok.map((r) => {
        const head = queries.find((x) => x.query === r.query);
        return { group: label(head), engine: r.engine, v: num(r.rows_ms),
          extra: num(r.count_ms) ? ` (count ${fmt(num(r.count_ms))})` : "" };
      });
      // The rows each engine returned, and whether they agree.
      const rowsOf = (qid) => engines.map((e) => cell(qid, e)).filter((r) => r && rsAnswered(r) && r.rows !== "");
      const differ = (qid) => uniq(rowsOf(qid).map((r) => r.rows)).length > 1;
      const nDiffer = queries.filter((r) => differ(r.query)).length;
      const rows = queries.map((r) => ({ ...r }));
      const time = (r, e) => {
        const c = cell(r.query, e);
        if (!c) return "–";
        if (!rsAnswered(c)) return c.status || "–";
        return `${fmt(num(c.rows_ms))} / ${fmt(num(c.count_ms))}${c.status === "forms differ" ? " *" : ""}`;
      };
      return [
        el("p", { class: "lead" },
          versus(geo, { field: "v", unit: "ms", what: `Geometric mean of the rows form's warm medians over the ${plural(common.length, "query", "queries")} every engine answered:` }),
          nDiffer ? ["The engines return different rows on ", b(plural(nDiffer, "query", "queries")), " (flagged in the table). "] : null,
          "Lower is better."),
        provLine(D.prov, "rinfshapes", ds),
        card("rs-queries", "Time per query", "Warm median of the rows form, ms, log scale; hover for the count form. ↳ marks an ablation control, under the query it repeats with patterns taken out.",
          dots(perQuery, uniq(queries.map(label)), "ms")),
        card("rs-table", "Rows and count form per query", "Warm medians, ms: the rows form (the answer as a client gets it) / the count form (the same solutions counted on the server). * = the two forms count different solutions.",
          table(rows, [
            // The shape once, on the first query of each.
            { label: "Shape", l: true, get: (r) => r.control_of || rows.find((x) => x.shape === r.shape && !x.control_of) !== r ? "" : (RS_SHAPES[r.shape] || r.shape) },
            { label: "Query", l: true, get: (r) => el("span", { title: r.title || null, text: label(r) }) },
            ...engines.map((e) => ({ label: name(e), get: (r) => time(r, e) })),
            { label: "Rows", get: (r) => differ(r.query)
                ? rowsOf(r.query).map((c) => `${name(c.engine)} ${Number(c.rows).toLocaleString("en")}`).join(", ")
                : (rowsOf(r.query)[0] ? Number(rowsOf(r.query)[0].rows).toLocaleString("en") : "–"),
              cls: (r) => differ(r.query) ? "down" : null },
          ])),
      ];
    },
  };
}

function groupBy(xs, key) {
  const m = new Map();
  for (const x of xs) { const k = key(x); if (!m.has(k)) m.set(k, []); m.get(k).push(x); }
  return m;
}

// The overview: one row per suite and dataset, one column per engine, with how many times
// faster TripleTrail is. A row links to its tab with that dataset selected.
const SUITES = {
  sparqloscope_geomean_ms: ["Sparqloscope, query time", "sparqloscope", (d) => d],
  bsbm_qmph: ["BSBM, query mixes per hour", "bsbm", (d) => d.split(" ")[0]],
  trainmarks_load_s: ["Trainmarks, load", "trainmarks", (d) => d],
  trainmarks_queries: ["Trainmarks, query time", "trainmarks", (d) => d],
  spatial_queries_p50_ms: ["Spatial, query time", "spatial", (d) => d],
  spatial_load_s: ["Spatial, load", "spatial", (d) => d],
};
const LABELS = { sparqloscope: SQ_SIZES, bsbm: BSBM_SIZES, trainmarks: TM_SIZES, spatial: SP_SIZES, rinfshapes: RS_SIZES };

// Rows the page works out from the CSV files itself, the same way as on the suite's tab.
function computedItems(D, suite) {
  if (suite === "trainmarks_queries") {
    // Engines that answered every read query, as in the Trainmarks tab's lead.
    return ordered(D.tq.map((r) => r.scale), Object.keys(TM_SIZES)).map((scale) => {
      const geo = tmGeo(D, scale).filter((r) => r.answered === r.of);
      const ours = geo.find((r) => r.engine === OURS);
      if (!ours) return null;
      return { dataset: scale, others: Object.fromEntries(geo.filter((r) => r.engine !== OURS)
        .map((r) => [r.engine, { speedup: r.geomean_ms / ours.geomean_ms }])) };
    }).filter(Boolean);
  }
  if (suite === "spatial_queries_p50_ms") {
    return ordered(D.squeries.map((r) => r.dataset), Object.keys(SP_SIZES)).map((ds) => ({
      dataset: ds, others: Object.fromEntries(spPairwise(D.squeries.filter((r) => r.dataset === ds))
        .map((p) => [p.engine, { speedup: p.speedup, n: p.n }])),
    }));
  }
  return null;
}

function overview(summary, D) {
  const rows = [];
  for (const [suite, [label, tab, sizeOf]] of Object.entries(SUITES)) {
    for (const item of computedItems(D, suite) || (summary.suites || {})[suite] || []) {
      const size = sizeOf(item.dataset);
      const rest = item.dataset.slice(size.length).trim();
      rows.push({ label, tab, size, what: `${LABELS[tab][size] || size}${rest ? ` · ${rest}` : ""}`, others: item.others || {} });
    }
  }
  if (!rows.length) return null;
  const engines = ordered(rows.flatMap((r) => Object.keys(r.others)), ENGINES);
  const all = rows.flatMap((r) => Object.values(r.others).map((o) => o.speedup)).filter((v) => v > 0);
  const wins = all.filter((v) => v >= 1).length;
  const best = (suite) => {
    const r = rows.filter((x) => x.label === suite);
    const v = r.flatMap((x) => Object.values(x.others).map((o) => o.speedup)).filter((s) => s > 0);
    return v.length ? gmean(v) : null;
  };
  const tiles = Object.values(SUITES).map(([label]) => [label, best(label)]).filter(([, v]) => v != null);
  return [
    el("p", { class: "lead" }, "TripleTrail is faster in ", b(`${wins} of ${all.length}`),
      " comparisons below. Each cell is how many times faster TripleTrail is than that engine (geometric means over the queries both answered, or the suite's own score); below 1× means slower. Click a row for its charts."),
    el("div", { class: "kpis" }, tiles.map(([label, v]) => el("div", { class: "card kpi" },
      el("div", { class: "big", text: times(v) }), el("div", { text: label }),
      el("div", { class: "what", text: "geometric mean of the speedups over every engine and dataset" })))),
    card("overview-table", "How many times faster TripleTrail is", null,
      table(rows, [
        { label: "Benchmark", l: true, get: (r) => r.label },
        { label: "Dataset", l: true, get: (r) => el("a", { href: `#${r.tab}/${r.size}`, text: r.what }) },
        ...engines.map((e) => ({
          label: name(e),
          get: (r) => r.others[e] ? times(r.others[e].speedup) + (r.others[e].n ? ` (${r.others[e].n})` : "") : "–",
          cls: (r) => !r.others[e] ? "na" : r.others[e].speedup >= 1 ? "up" : "down",
        })),
      ]),
      spatialNote(D)),
  ];
}

// Spatial query time in the table is pairwise; the Spatial tab also compares all engines on the
// queries every one of them answered. Where the two disagree, say so with both numbers.
function spatialNote(D) {
  const flips = [];
  for (const ds of ordered(D.squeries.map((r) => r.dataset), Object.keys(SP_SIZES))) {
    const q = D.squeries.filter((r) => r.dataset === ds);
    const { common, geo } = spCommon(q);
    const ours = geo.find((r) => r.engine === OURS);
    if (!ours) continue;
    for (const p of spPairwise(q)) {
      const g = geo.find((r) => r.engine === p.engine);
      if (!g) continue;
      const all = g.geomean_ms / ours.geomean_ms;
      if ((all >= 1) !== (p.speedup >= 1)) {
        flips.push([`${SP_SIZES[ds] || ds}: TripleTrail is `, b(ratioText(p.speedup)), ` ${name(p.engine)} pairwise over ${plural(p.n, "query", "queries")}, but `,
          b(ratioText(all)), ` it over the ${plural(common.length, "query", "queries")} every engine answered`]);
      }
    }
  }
  return el("p", { class: "note", style: "margin-top:10px" },
    "Spatial query time is pairwise: each cell is over the queries TripleTrail and that engine both answered (their number in brackets). For PostGIS that includes routing, which the RDF engines do not run. The Spatial tab also compares every engine on only the queries all of them answered, which can give the opposite result. ",
    flips.length ? ["Where it does: ", flips.flatMap((f, i) => [i ? "; " : "", ...f]), "."] : null);
}

function runs(D) {
  if (!D.prov.length && !(Array.isArray(D.runs) && D.runs.length)) return null;
  const link = (run) => run.url ? el("a", { href: run.url, text: run.run }) : document.createTextNode(run.run);
  const commit = (c) => c ? el("a", { href: `https://github.com/Matdata-eu/tripletrail/commit/${c}`, text: c.slice(0, 8) }) : "";
  return [
    Array.isArray(D.runs) && D.runs.length ? card("runs", "Runs", "Every run of the workflow, with its logs, the TripleTrail commit it measured and the machine.",
      table(D.runs, [
        { label: "Run", l: true, get: link }, { label: "Started", l: true, get: (r) => (r.started || "").slice(0, 16).replace("T", " ") },
        { label: "Request", l: true, get: (r) => r.request }, { label: "TripleTrail", l: true, get: (r) => commit(r.commit) },
        { label: "Machine", l: true, get: (r) => r.machine }, { label: "Jobs ok / failed / skipped", get: (r) => r.jobs },
      ])) : null,
    D.prov.length ? card("provenance", "Where each result comes from", null,
      table(D.prov, [
        { label: "Suite", l: true, get: (r) => r.suite }, { label: "Dataset", l: true, get: (r) => r.dataset },
        { label: "Machine", l: true, get: (r) => r.machine }, { label: "CPUs", get: (r) => r.cpus },
        { label: "TripleTrail", l: true, get: (r) => commit(r.commit) }, { label: "Date", l: true, get: (r) => r.date },
        { label: "Engines", l: true, get: (r) => (r.engines || "").split(" ").filter(Boolean).map(name).join(", ") || "–" },
      ])) : null,
  ];
}

// ---------------------------------------------------------------------------------------------
// Page: tabs, a size toggle per tab, and the state in the URL hash (#spatial/large).

// Which snapshot the page opens on without ?v=: "latest" (the newest results, tagged or not) or
// "tagged" (the newest results tag, results-*, falling back to the latest when there is none).
const DEFAULT_VERSION = "latest";

const versionLabel = (v) => [
  v.id === "latest" ? "Latest" : v.date,
  v.version ? `TripleTrail ${v.version}` : v.tripletrail ? `TripleTrail ${v.tripletrail.slice(0, 8)}` : null,
  v.tags && v.tags.length ? `★ ${v.tags.join(", ")}` : null,
].filter(Boolean).join(" · ");

// Picks the snapshot from ?v= (an id, a commit or a tag), fills the picker and, for an earlier
// snapshot, says so above the tabs. Returns the chosen version (or null without versions.json).
async function chooseVersion() {
  const versions = await load("versions.json", "data/");
  if (!Array.isArray(versions) || !versions.length) return null;
  const want = new URLSearchParams(location.search).get("v");
  const tagged = versions.find((v) => v.tags && v.tags.length);
  const v = (want && versions.find((x) => x.id === want || (x.bench_commit || "").startsWith(want) || (x.tags || []).includes(want)))
    || (DEFAULT_VERSION === "tagged" && tagged) || versions[0];
  BASE = v.path;

  const select = document.getElementById("version");
  for (const x of versions) {
    const o = el("option", { value: x.id, text: versionLabel(x) });
    if (x === v) o.selected = true;
    select.append(o);
  }
  select.addEventListener("change", () => {
    const u = new URL(location.href);
    if (select.value === versions[0].id && DEFAULT_VERSION === "latest") u.searchParams.delete("v");
    else u.searchParams.set("v", select.value);
    location.assign(u.toString());
  });
  document.getElementById("version-box").hidden = false;

  if (v !== versions[0]) {
    const u = new URL(location.href);
    u.searchParams.delete("v");
    const commit = v.tripletrail ? el("a", { href: `https://github.com/Matdata-eu/tripletrail/commit/${v.tripletrail}`, text: v.tripletrail.slice(0, 8) }) : null;
    const box = document.getElementById("older");
    box.append(...["These are the results as of ", b(v.date || "an earlier commit"),
      commit ? [", whose newest run measured TripleTrail ", v.version ? `${v.version} (` : "", commit, v.version ? ")" : ""] : null,
      v.tags && v.tags.length ? [", tagged ", b(v.tags.join(", "))] : null,
      ". ", el("a", { href: u.toString(), text: "Show the latest results" }), "."].flat().filter((x) => x != null && x !== ""));
    box.hidden = false;
  }
  return v;
}

async function main() {
  await chooseVersion();
  const [summary, sq, cats, qmph, aqet, tload, tq, sload, squeries, rs, prov, runList] = await Promise.all([
    load("summary.json"), load("summary.csv"), load("categories.csv"), load("bsbm_qmph.csv"), load("bsbm_aqet.csv"),
    load("trainmarks_load.csv"), load("trainmarks_queries.csv"), load("spatial_load.csv"),
    load("spatial_queries.csv"), load("rinfshapes_queries.csv"), load("provenance.csv"), load("runs.json"),
  ]);
  const D = { sq, cats, qmph, aqet, tload, tq, sload, squeries, rs, prov, runs: runList };

  const legendEngines = ordered([sq, qmph, tload, sload, squeries, rs].flat().map((r) => r.engine).filter(Boolean), ENGINES);
  document.getElementById("legend").append(...legendEngines.map((e) =>
    el("li", { class: e === OURS ? "ours" : null }, el("span", { class: "sw", style: `background:${color(e)}` }), name(e))));

  const suites = [sparqloscope(D), bsbm(D), trainmarks(D), spatial(D), routing(D), rinfshapes(D)].filter(Boolean);
  const tabs = [];
  const ov = summary && summary.suites ? overview(summary, D) : null;
  if (ov) tabs.push({ id: "overview", label: "Overview", build: () => ov });
  for (const s of suites) tabs.push({ id: s.id || s.label.toLowerCase(), ...s });
  const rn = runs(D);
  if (rn) tabs.push({ id: "runs", label: "Runs", build: () => rn });

  if (!tabs.length) { document.getElementById("empty").hidden = false; return; }

  const nav = document.getElementById("tabs");
  const box = document.getElementById("panels");
  const chosen = {}; // tab id -> size
  let current = null;

  const parse = () => {
    const [t, s] = decodeURIComponent(location.hash.slice(1)).split("/");
    const tab = tabs.find((x) => x.id === t) || tabs[0];
    if (tab.sizes && tab.sizes.some(([v]) => v === s)) chosen[tab.id] = s;
    return tab;
  };

  const render = () => {
    const tab = current;
    [...nav.children].forEach((btn) => btn.setAttribute("aria-selected", String(btn.dataset.tab === tab.id)));
    const panel = el("div", { class: "panel", role: "tabpanel", id: `panel-${tab.id}` });
    let size = null;
    if (tab.sizes) {
      size = chosen[tab.id] || DEFAULT_SIZE[tab.id];
      if (!tab.sizes.some(([v]) => v === size)) size = tab.sizes[0][0];
      chosen[tab.id] = size;
      const group = el("div", { class: "toggle", role: "group", "aria-label": tab.toggleLabel });
      for (const [v, label] of tab.sizes) {
        const btn = el("button", { type: "button", "aria-pressed": String(v === size), text: label });
        btn.addEventListener("click", () => go(tab.id, v));
        group.append(btn);
      }
      panel.append(el("div", { class: "toolbar" }, el("span", { class: "label", text: tab.toggleLabel }), group));
    }
    panel.append(...(tab.build(size) || []).filter(Boolean));
    box.replaceChildren(panel);
    panel.querySelectorAll(".chart").forEach((c) => c._draw());
  };

  const go = (id, size) => {
    const tab = tabs.find((x) => x.id === id);
    if (size) chosen[id] = size;
    const s = tab.sizes ? chosen[id] : null;
    const hash = `#${id}${s ? `/${s}` : ""}`;
    try { history.replaceState(null, "", hash); } catch {}
    current = tab;
    render();
  };

  for (const t of tabs) {
    const btn = el("button", { role: "tab", type: "button", "data-tab": t.id, text: t.label });
    btn.addEventListener("click", () => go(t.id));
    nav.append(btn);
  }
  window.addEventListener("hashchange", () => { current = parse(); render(); });
  let timer = null, lastW = window.innerWidth;
  window.addEventListener("resize", () => {
    if (window.innerWidth === lastW) return;
    lastW = window.innerWidth;
    clearTimeout(timer);
    timer = setTimeout(() => box.querySelectorAll(".chart").forEach((c) => c._draw()), 120);
  });
  current = parse();
  render();
}

main();
