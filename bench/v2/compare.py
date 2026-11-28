#!/usr/bin/env python3
"""Compare every engine's results with the reference: PostGIS/pgRouting when it answered, else
the majority answer of the engines that answered (never one engine alone, TripleTrail included).

  compare.py <results>/<dataset>     -> correctness.csv and correctness.json in that folder

Runs are matched by run index (same parameters). Checks per result kind:
  ids      same set of IRIs (count of missing / extra reported)
  ranked   same set of the k nearest (order differences reported separately)
  groups   same keys; values equal within the query's relative tolerance
  scalars  values equal within the relative tolerance
  point    points within the tolerance in metres
  path     same total cost (relative tolerance) and same edge sequence; same cost with another
           edge sequence counts as "tie" (an equal-cost alternative), not as a mismatch
  costs    same number of paths, costs equal within the tolerance

Without PostGIS (the scale suite, OSM runs without it), the reference of each run is the answer a
strict majority of the engines that answered gave, and at least two of them: with two engines they
must agree, and one engine alone is never the reference. A run without such a majority counts
under no_reference, not as a mismatch of anyone (tripletrail-bench#96).

An engine whose load.json names another triple count than the reference's ran on another extract
(the scale suite downloads the newest OSM file): its differing answers are counted under
other_extract instead of mismatch, since they say nothing about either engine. Without PostGIS
the majority is taken among the engines on the extract most of them loaded.

verdicts() reads correctness.csv back for report.py and dashboard.py, which mark a mismatching
query and leave it out of means and speedups.
"""
import csv
import glob
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from workload import QUERIES  # noqa: E402


def rel_close(a, b, tol):
    if a is None or b is None:
        return a is None and b is None
    tol = tol or 0.0
    return abs(a - b) <= tol * max(abs(a), abs(b), 1e-12) + (1e-9 if tol == 0 else 0)


def hav(p, q):
    lat1, lat2 = math.radians(p[1]), math.radians(q[1])
    h = math.sin((lat2 - lat1) / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(math.radians(q[0] - p[0]) / 2) ** 2
    return 2 * 6371008.8 * math.asin(math.sqrt(h))


def cmp(kind, ref, got, tol):
    """Returns (verdict, note): verdict in match / tie / mismatch."""
    if kind == "ids":
        if ref["digest"] == got["digest"]:
            return "match", ""
        if "ids" in ref and "ids" in got:
            r, g = set(ref["ids"]), set(got["ids"])
            return "mismatch", f"ref {len(r)} got {len(g)}: {len(r - g)} missing, {len(g - r)} extra"
        return "mismatch", f"ref {ref['n']} got {got['n']}"
    if kind == "ranked":
        r, g = ref["ids"], got["ids"]
        if r == g:
            return "match", ""
        if set(r) == set(g):
            return "match", "same set, other order"
        return "mismatch", f"{len(set(r) & set(g))}/{len(r)} in common"
    if kind == "groups":
        r, g = ref["groups"], got["groups"]
        if set(r) != set(g):
            return "mismatch", f"keys differ ({len(r)} vs {len(g)})"
        bad = [k for k in r if not rel_close(r[k], g[k], tol)]
        if not bad:
            return "match", ""
        k = bad[0]
        return "mismatch", f"{len(bad)} groups differ, e.g. {k.rsplit('/', 1)[-1]}: {r[k]} vs {g[k]}"
    if kind == "scalars":
        r, g = ref["values"], got["values"]
        if len(r) == len(g) and all(rel_close(a, b, tol) for a, b in zip(r, g)):
            return "match", ""
        return "mismatch", f"{r} vs {g}"
    if kind == "point":
        r, g = ref["point"], got["point"]
        if r is None or g is None:
            return ("match", "") if r is g else ("mismatch", f"{r} vs {g}")
        d = hav(r, g)
        return ("match", f"{d:.3f} m") if d <= tol else ("mismatch", f"{d:.1f} m apart")
    if kind == "path":
        if ref["n"] == 0 and got["n"] == 0:
            return "match", "no path"
        if not rel_close(ref["total"], got["total"], tol):
            return "mismatch", f"cost {ref['total']} vs {got['total']} ({ref['n']} vs {got['n']} edges)"
        if ref["digest"] == got["digest"]:
            return "match", ""
        return "tie", f"same cost, other edges ({ref['n']} vs {got['n']})"
    if kind == "costs":
        r, g = ref["costs"], got["costs"]
        if len(r) == len(g) and all(rel_close(a, b, tol) for a, b in zip(r, g)):
            return "match", ""
        return "mismatch", f"{r} vs {g}"
    raise ValueError(kind)


def triples(folder):
    """Triples each engine loaded, from its load.json (engines without the field are left out)."""
    out = {}
    for p in glob.glob(os.path.join(folder, "*", "load.json")):
        try:
            n = json.load(open(p)).get("triples")
        except (OSError, ValueError):
            continue
        if isinstance(n, int):
            out[os.path.basename(os.path.dirname(p))] = n
    return out


def load(folder):
    res = {}
    for p in glob.glob(os.path.join(folder, "*", "*.json")):
        engine, name = os.path.basename(os.path.dirname(p)), os.path.basename(p)[:-5]
        if name == "load":
            continue
        with open(p) as f:
            res.setdefault(name, {})[engine] = json.load(f)
    return res


def agree(kind, a, b, tol):
    return cmp(kind, a, b, tol)[0] in ("match", "tie")


def majority(kind, answers, tol):
    """The answer most of the engines gave for one run: {engine: result} -> (result, engines
    that gave it), or (None, []) when no answer has a strict majority of at least two engines.
    One engine alone is never the reference, whatever it is."""
    best, side = None, []
    for e, a in sorted(answers.items()):
        with_e = [f for f, b in answers.items() if agree(kind, a, b, tol)]
        if len(with_e) > len(side):
            best, side = a, with_e
    if len(side) >= 2 and 2 * len(side) > len(answers):
        return best, sorted(side)
    return None, []


def main_extract(loaded):
    """The triple count most engines of the dataset loaded (the larger one on a tie), or None
    when they all loaded the same or say nothing."""
    by = {}
    for n in loaded.values():
        by[n] = by.get(n, 0) + 1
    return max(by, key=lambda n: (by[n], n)) if len(by) > 1 else None


def references(q, ok, loaded):
    """The reference answer of each run of one query: PostGIS/pgRouting when it answered, else
    the majority answer of the engines that answered (majority above), among the engines that
    loaded the extract most engines of the dataset loaded. Returns (name, {index: result},
    engines on another extract)."""
    if "postgis" in ok:
        return "postgis", {r["index"]: r["result"] for r in ok["postgis"]["runs"] if r.get("ok")}, set()
    # Engines on another extract than most say nothing about the others' answers.
    main_n = main_extract(loaded)
    pool = {e for e in ok if main_n is None or loaded.get(e, main_n) == main_n}
    runs = {}
    for e in pool:
        for r in ok[e]["runs"]:
            if r.get("ok"):
                runs.setdefault(r["index"], {})[e] = r["result"]
    ref = {}
    for i, answers in runs.items():
        a, _ = majority(q["kind"], answers, q["tol"])
        if a is not None:
            ref[i] = a
    return "majority", ref, set(ok) - pool


def main():
    folder = sys.argv[1]
    res = load(folder)
    loaded = triples(folder)
    rows, details = [], {}
    for qid, q in QUERIES.items():
        by = res.get(qid, {})
        ok = {e: r for e, r in by.items() if r.get("status", "").startswith("ok")}
        if not ok:
            continue
        ref_engine, ref_runs, elsewhere = references(q, ok, loaded)
        for e, rec in sorted(by.items()):
            if e == ref_engine:
                continue
            if not rec.get("status", "").startswith("ok"):
                rows.append(dict(qid=qid, engine=e, reference=ref_engine, compared=0, match=0, tie=0,
                                 mismatch=0, other_extract=0, no_reference=0,
                                 note=f"{rec.get('status')}: {rec.get('reason', '')}"[:200]))
                continue
            counts = {"match": 0, "tie": 0, "mismatch": 0, "no_reference": 0}
            notes, examples = {}, []
            for r in rec["runs"]:
                if not r.get("ok"):
                    continue
                if r["index"] not in ref_runs:
                    counts["no_reference"] += 1
                    continue
                v, note = cmp(q["kind"], ref_runs[r["index"]], r["result"], q["tol"])
                counts[v] += 1
                if note:
                    key = note if v != "match" else "match: " + note.split(":")[0]
                    notes[key if len(notes) < 50 else "..."] = notes.get(key, 0) + 1
                if v != "match" and len(examples) < 5:
                    examples.append({"index": r["index"], "verdict": v, "note": note})
            summary_note = "; ".join(f"{k} (x{n})" if n > 1 else k for k, n in list(notes.items())[:3])
            if counts["no_reference"]:
                summary_note = (f"{counts['no_reference']} runs without a majority answer"
                                + (f"; {summary_note}" if summary_note else ""))
            ref_n = loaded.get(ref_engine) if ref_engine != "majority" else None
            if e in elsewhere or (e in loaded and ref_n is not None and loaded[e] != ref_n):
                # Another extract: a differing answer says nothing about either engine.
                theirs = ref_n if ref_n is not None else main_extract(loaded)
                summary_note = (f"other extract ({loaded[e]:,} triples against {theirs:,}): "
                                f"{counts['match'] + counts['tie']} agree, "
                                f"{counts['mismatch'] + counts['no_reference']} differ") if theirs else "other extract"
                counts = {"match": counts["match"], "tie": counts["tie"], "mismatch": 0, "no_reference": 0,
                          "other_extract": counts["mismatch"] + counts["no_reference"]}
            rows.append(dict(qid=qid, engine=e, reference=ref_engine, compared=sum(counts.values()),
                             **{k: counts.get(k, 0) for k in ("match", "tie", "mismatch", "other_extract",
                                                              "no_reference")},
                             note=summary_note[:300]))
            details[f"{qid}/{e}"] = {"counts": counts, "examples": examples, "notes": notes}
    with open(os.path.join(folder, "correctness.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)
    with open(os.path.join(folder, "correctness.json"), "w") as f:
        json.dump(details, f, indent=1)
    for r in rows:
        print(f"{r['qid']:24s} {r['engine']:8s} vs {r['reference']:8s} {r['compared']:5d} compared: "
              f"{r['match']} match, {r['tie']} tie, {r['mismatch']} mismatch, {r['other_extract']} other extract, "
              f"{r['no_reference']} no reference  {r['note'][:150]}")


FIELDS = ["qid", "engine", "reference", "compared", "match", "tie", "mismatch", "other_extract", "no_reference",
          "note"]


def verdicts(folder):
    """{(qid, engine): (verdict, note)} from a dataset's correctness.csv, for the report and the
    dashboard: "mismatch" when any run differs from the reference, "unchecked" when no run could
    be compared (another extract, no majority), else "ok". Empty without the file."""
    out = {}
    path = os.path.join(folder, "correctness.csv")
    if not os.path.exists(path):
        return out
    with open(path, newline="") as f:
        for r in csv.DictReader(f):
            n = {k: int(r.get(k) or 0) for k in ("match", "tie", "mismatch", "other_extract", "no_reference")}
            if n["mismatch"]:
                v = "mismatch"
            elif n["match"] + n["tie"] == 0 and n["other_extract"] + n["no_reference"]:
                v = "unchecked"
            else:
                v = "ok"
            out[(r["qid"], r["engine"])] = (v, r.get("note", ""))
    return out


if __name__ == "__main__":
    main()
