// The benchmark dashboard: reads the CSV files of bench/v2/results/dashboard (copied to data/
// by pages.yml) and draws one bar chart per dataset and engine. No dependencies.
"use strict";

const OURS = "tripletrail";
const NAMES = {
  tripletrail: "TripleTrail", postgis: "PostGIS", qlever: "QLever", jena: "Jena",
  graphdb: "GraphDB", oxigraph: "Oxigraph", maplib: "maplib",
};
const REPO = "https://github.com/Matdata-eu/tripletrail-bench";

function parseCSV(text) {
  const lines = text.trim().split("\n").filter(Boolean);
  if (lines.length < 2) return [];
  const head = lines[0].split(",");
  return lines.slice(1).map((line) => {
    const cells = line.split(",");
    return Object.fromEntries(head.map((h, i) => [h, cells[i] ?? ""]));
  });
}

async function load(name) {
  try {
    const r = await fetch(`data/${name}`, { cache: "no-cache" });
    if (!r.ok) return [];
    return name.endsWith(".json") ? await r.json() : parseCSV(await r.text());
  } catch {
    return [];
  }
}

const el = (tag, attrs = {}, ...kids) => {
  const e = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (k === "text") e.textContent = v;
    else e.setAttribute(k, v);
  }
  for (const k of kids) if (k) e.append(k);
  return e;
};

const fmt = (v, unit) => {
  if (v == null || !isFinite(v)) return "–";
  const n = v >= 100 ? v.toFixed(0) : v >= 10 ? v.toFixed(1) : v.toFixed(2);
  return unit ? `${Number(n).toLocaleString("en")} ${unit}` : Number(n).toLocaleString("en");
};
const name = (e) => NAMES[e] || e;
const num = (x) => { const v = parseFloat(x); return isFinite(v) && v > 0 ? v : null; };

// One bar per engine; TripleTrail highlighted. Bars on a log scale when the spread is wide.
function bars(entries, unit) {
  const vals = entries.map((e) => e.value).filter((v) => v != null);
  if (!vals.length) return null;
  const max = Math.max(...vals), min = Math.min(...vals);
  const log = max / min > 50;
  const width = (v) => log
    ? 4 + 96 * (Math.log(v / min) + 0.1) / (Math.log(max / min) + 0.1)
    : 100 * v / max;
  const box = el("div", { class: "chart", role: "img",
    "aria-label": entries.map((e) => `${name(e.engine)} ${fmt(e.value, unit)}`).join(", ") });
  for (const e of entries) {
    const row = el("div", { class: "row" + (e.engine === OURS ? " ours" : "") },
      el("span", { class: "name", text: name(e.engine) }),
      el("div", { class: "track" }, e.value != null ? el("div", { class: "fill", style: `width:${width(e.value)}%` }) : null),
      el("span", { class: "val", text: e.value != null ? fmt(e.value, unit) : (e.note || "no answer") }));
    box.append(row);
  }
  if (log) box.append(el("p", { class: "note", text: "Log scale: the engines are far apart." }));
  return box;
}

function group(rows, key, engineKey, valueKey) {
  const out = new Map();
  for (const r of rows) {
    const k = typeof key === "function" ? key(r) : r[key];
    if (!out.has(k)) out.set(k, []);
    out.get(k).push({ engine: r[engineKey], value: num(r[valueKey]), note: r.note });
  }
  for (const list of out.values()) list.sort((a, b) => (a.value ?? Infinity) - (b.value ?? Infinity));
  return out;
}

function section(title, note, groups, unit, higherIsBetter) {
  const s = el("section", {}, el("h2", { text: title }));
  if (note) s.append(el("p", { class: "note", text: note }));
  for (const [k, list] of groups) {
    if (higherIsBetter) list.sort((a, b) => (b.value ?? -1) - (a.value ?? -1));
    s.append(el("h3", { text: k }), bars(list, unit));
  }
  return groups.size ? s : null;
}

function table(rows, cols) {
  const t = el("table");
  t.append(el("tr", {}, ...cols.map((c) => el("th", { text: c.label }))));
  for (const r of rows) {
    t.append(el("tr", {}, ...cols.map((c) => {
      const v = c.get(r);
      return el("td", { class: c.n ? "n" : "" }, v instanceof Node ? v : document.createTextNode(v ?? ""));
    })));
  }
  return el("div", { class: "tablewrap" }, t);
}

function overview(summary) {
  const s = el("section", {}, el("h2", { text: "Headline" }),
    el("p", { class: "note", text: "How many times faster TripleTrail is than each engine, per benchmark and dataset (geometric means over the queries both answered, or the suite's own score). Below 1× means slower." }));
  const cards = el("div", { class: "cards" });
  const labels = {
    sparqloscope_geomean_ms: "Sparqloscope, query time",
    bsbm_qmph: "BSBM, query mixes per hour",
    trainmarks_load_s: "Trainmarks, load",
    spatial_load_s: "Spatial, load",
    spatial_queries_p50_ms: "Spatial queries, median time",
  };
  for (const [suite, list] of Object.entries(summary.suites || {})) {
    for (const item of list) {
      for (const [engine, o] of Object.entries(item.others || {})) {
        cards.append(el("div", { class: "card" },
          el("div", { class: "big", text: `${o.speedup.toLocaleString("en")}×` }),
          el("div", { text: `vs ${name(engine)}` }),
          el("div", { class: "what", text: `${labels[suite] || suite} · ${item.dataset}` })));
      }
    }
  }
  s.append(cards);
  return cards.childElementCount ? s : null;
}

async function main() {
  const [summary, sq, cats, qmph, tload, tq, sload, squeries, prov, runs] = await Promise.all([
    load("summary.json"), load("summary.csv"), load("categories.csv"), load("bsbm_qmph.csv"),
    load("trainmarks_load.csv"), load("trainmarks_queries.csv"), load("spatial_load.csv"),
    load("spatial_queries.csv"), load("provenance.csv"), load("runs.json"),
  ]);

  const panels = [];
  const add = (label, ...sections) => {
    const kids = sections.filter(Boolean);
    if (kids.length) panels.push([label, kids]);
  };

  add("Overview", summary && summary.suites ? overview(summary) : null);
  add("Spatial",
    section("Load time", "Time to load each dataset (seconds).", group(sload, "dataset", "engine", "load_s"), "s"),
    section("Median query time per query family", "Geometric mean of the median time (p50) of each family's queries, over the answered ones (ms).",
      (() => {
        const m = new Map();
        const acc = new Map();
        for (const r of squeries) {
          const v = num(r.p50_ms);
          if (!v || (r.status && r.status !== "ok")) continue;
          const k = `${r.dataset} · ${r.family}`;
          if (!acc.has(k)) acc.set(k, new Map());
          const e = acc.get(k);
          if (!e.has(r.engine)) e.set(r.engine, []);
          e.get(r.engine).push(Math.log(v));
        }
        for (const [k, e] of acc) {
          m.set(k, [...e].map(([engine, ls]) => ({ engine, value: Math.exp(ls.reduce((a, b) => a + b, 0) / ls.length) }))
            .sort((a, b) => a.value - b.value));
        }
        return m;
      })(), "ms"));
  add("Sparqloscope",
    section("Geometric mean query time", "About 100 queries, each isolating one SPARQL feature (ms).", group(sq, "dataset", "engine", "geomean_ms"), "ms"),
    section("By category", "Geometric mean per feature category (ms).", group(cats, (r) => `${r.dataset} · ${r.category}`, "engine", "ms"), "ms"));
  add("BSBM",
    section("Query mixes per hour", "Berlin SPARQL Benchmark with its own test driver; higher is better.", group(qmph, (r) => `${r.scale} · ${r.usecase}`, "engine", "qmph"), "QMpH", true));
  add("Trainmarks",
    section("Load time", "Seconds.", group(tload, "scale", "engine", "load_s"), "s"),
    section("Warm query time", "Milliseconds.", group(tq, (r) => `${r.scale} · ${r.query}`, "engine", "warm_ms"), "ms"));
  if (prov.length || (Array.isArray(runs) && runs.length)) {
    const link = (run) => run.url ? el("a", { href: run.url, text: run.run }) : document.createTextNode(run.run);
    const commit = (c) => c ? el("a", { href: `https://github.com/Matdata-eu/tripletrail/commit/${c}`, text: c.slice(0, 8) }) : "";
    add("Runs",
      Array.isArray(runs) && runs.length ? el("section", {}, el("h2", { text: "Runs" }),
        el("p", { class: "note", text: "Every run of the workflow, with its logs, the TripleTrail commit it measured and the machine." }),
        table(runs, [
          { label: "Run", get: link }, { label: "Started", get: (r) => (r.started || "").slice(0, 16).replace("T", " ") },
          { label: "Request", get: (r) => r.request }, { label: "TripleTrail", get: (r) => commit(r.commit) },
          { label: "Machine", get: (r) => r.machine }, { label: "Jobs ok / failed / skipped", get: (r) => r.jobs },
        ])) : null,
      prov.length ? el("section", {}, el("h2", { text: "Where each result comes from" }),
        table(prov, [
          { label: "Suite", get: (r) => r.suite }, { label: "Dataset", get: (r) => r.dataset },
          { label: "Machine", get: (r) => r.machine }, { label: "CPUs", get: (r) => r.cpus, n: true },
          { label: "TripleTrail", get: (r) => commit(r.commit) }, { label: "Date", get: (r) => r.date },
        ])) : null);
  }

  if (!panels.length) {
    document.getElementById("empty").hidden = false;
    return;
  }
  const tabs = document.getElementById("tabs");
  const box = document.getElementById("panels");
  const show = (i) => {
    [...tabs.children].forEach((b, j) => b.setAttribute("aria-selected", String(i === j)));
    [...box.children].forEach((p, j) => { p.hidden = i !== j; });
    try { history.replaceState(null, "", `#${panels[i][0].toLowerCase()}`); } catch {}
  };
  panels.forEach(([label, kids], i) => {
    const b = el("button", { role: "tab", text: label });
    b.addEventListener("click", () => show(i));
    tabs.append(b);
    box.append(el("div", { role: "tabpanel" }, ...kids));
  });
  const want = panels.findIndex(([l]) => `#${l.toLowerCase()}` === location.hash);
  show(want >= 0 ? want : 0);
}

main();
