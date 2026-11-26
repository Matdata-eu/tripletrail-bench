#!/usr/bin/env python3
"""Seeded violations for the SHACL suite: breaks a share of the focus nodes of a RINF data file
in known ways, so that each engine's recall and precision on them can be measured (tracker #31).

  inject.py DATA SHAPES OUT_DIR [--seed N] [--rate R]

DATA is the suite's N-Triples file (RINF plus the ontology and code lists), SHAPES a profile of
the ERA shapes (era-local: the code lists are checked by SPARQL constraints). It writes:

  OUT_DIR/mutated.nt     DATA with the mutations
  OUT_DIR/expected.tsv   one line per injected violation: focus node, path, constraint component
  OUT_DIR/touched.txt    the nodes the mutations touch (for precision, see score)
  OUT_DIR/manifest.json  seed, rate, the focus nodes considered and changed, counts by kind

Of the instances of the classes the shapes target (rdf:type, not through subclasses), a share R
(0.01) is drawn with the seed, and each drawn node gets one mutation that its class's shapes and
its own triples allow, the kinds taken in turn:

  datatype   a value of a property shape with sh:datatype (not xsd:string) gets xsd:string
             (same lexical form): sh:DatatypeConstraintComponent
  missing    every value of a property shape with sh:minCount >= 1 is removed:
             sh:MinCountConstraintComponent
  code-list  the value of a property whose SPARQL constraint checks skos:inScheme becomes an IRI
             in no scheme: sh:SPARQLConstraintComponent
  pattern    a value of a property shape with sh:pattern gets a lexical form the pattern rejects
             and the datatype still accepts ("0" in front of an integer, "#" after a string):
             sh:PatternConstraintComponent
  duplicate  a property shape with sh:maxCount 1 and one value (an IRI, an integer or a string)
             gets a second, different value: sh:MaxCountConstraintComponent

The expected file and the mutated data hold RINF values: they stay in the work directory. Only
the manifest's counts are published.
"""
import argparse
import json
import os
import random
import re
import sys

SH = "http://www.w3.org/ns/shacl#"
RDF_TYPE = "http://www.w3.org/1999/02/22-rdf-syntax-ns#type"
XSD = "http://www.w3.org/2001/XMLSchema#"
ERA = "http://data.europa.eu/949/"
KINDS = ["datatype", "missing", "code-list", "pattern", "duplicate"]
COMPONENT = {"datatype": SH + "DatatypeConstraintComponent", "missing": SH + "MinCountConstraintComponent",
             "code-list": SH + "SPARQLConstraintComponent", "pattern": SH + "PatternConstraintComponent",
             "duplicate": SH + "MaxCountConstraintComponent"}
UPSTREAM = 3
NOT_IN_LIST = "http://example.org/tripletrail-bench/not-in-any-list"
NT = re.compile(r'^(<[^>]*>|_:\S+) <([^>]*)> (.*) \.\s*$')
LIT = re.compile(r'^"((?:[^"\\]|\\.)*)"(?:\^\^<([^>]*)>|@(\S+))?$')
INTEGERS = {XSD + t for t in ("integer", "int", "long", "short", "byte", "nonNegativeInteger",
                              "positiveInteger", "unsignedInt", "unsignedLong", "unsignedShort")}


def rules(shapes_path):
    """Per targeted class: the mutations its shapes allow, as (kind, path, detail)."""
    import rdflib
    from rdflib.namespace import RDF
    g = rdflib.Graph().parse(shapes_path)
    S = rdflib.Namespace(SH)
    out = {}
    for ns, cls in g.subject_objects(S.targetClass):
        if (ns, S.deactivated, rdflib.Literal(True)) in g:
            continue
        found = out.setdefault(str(cls), [])
        for ps in g.objects(ns, S.property):
            path = g.value(ps, S.path)
            if not isinstance(path, rdflib.URIRef) or (ps, S.deactivated, rdflib.Literal(True)) in g:
                continue
            p = str(path)
            dt = g.value(ps, S.datatype)
            if dt is not None and str(dt) != XSD + "string":
                found.append(("datatype", p, str(dt)))
            mn = g.value(ps, S.minCount)
            if mn is not None and int(mn) >= 1:
                found.append(("missing", p, None))
            pat = g.value(ps, S.pattern)
            if pat is not None and g.value(ps, S.flags) is None:
                found.append(("pattern", p, str(pat)))
            mx = g.value(ps, S.maxCount)
            if mx is not None and int(mx) == 1:
                found.append(("duplicate", p, None))
        for c in g.objects(ns, S.sparql):
            select = str(g.value(c, S.select) or "")
            prop = g.value(c, rdflib.URIRef(ERA + "affectedProperty"))
            if "inScheme" in select and prop is not None and (c, S.deactivated, rdflib.Literal(True)) not in g:
                found.append(("code-list", str(prop), None))
    return {c: sorted(set(r)) for c, r in out.items() if r}


def parse(line):
    m = NT.match(line)
    return m.groups() if m else None


def literal(o):
    """(lexical as written, datatype, language) of a literal, or None for an IRI or blank node."""
    m = LIT.match(o)
    if not m:
        return None
    return m.group(1), m.group(2) or (None if m.group(3) else XSD + "string"), m.group(3)


def mutate(kind, path, detail, triples, rng):
    """For one focus node's triples (subject, predicate, object as written): the lines to drop and
    to add, or None when the node does not allow this mutation."""
    values = [(i, t) for i, t in enumerate(triples) if t[1] == path]
    s = triples[0][0]
    if kind == "missing":
        return ([i for i, _ in values], []) if values else None
    if kind == "datatype":
        for i, (_, _, o) in values:
            lit = literal(o)
            if lit and lit[1] == detail:
                return [i], [f'{s} <{path}> "{lit[0]}"^^<{XSD}string> .']
        return None
    if kind == "pattern":
        for i, (_, _, o) in values:
            lit = literal(o)
            if lit and lit[1] in INTEGERS and re.fullmatch(r"[0-9]+", lit[0]):
                bad = "0" + lit[0]
            elif lit and lit[1] == XSD + "string":
                bad = lit[0] + "#"
            else:
                continue
            try:
                if re.search(detail, bad):
                    continue
            except re.error:
                return None
            return [i], [f'{s} <{path}> "{bad}"^^<{lit[1]}> .']
        return None
    if kind == "code-list":
        for i, (_, _, o) in values:
            if o.startswith("<"):
                return [i], [f"{s} <{path}> <{NOT_IN_LIST}> ."]
        return None
    if kind == "duplicate":
        if len(values) != 1:
            return None
        _, (_, _, o) = values[0]
        lit = literal(o)
        if o.startswith("<"):
            second = f"<{o[1:-1]}-tripletrail-bench-second>"
        elif lit and lit[1] in INTEGERS and re.fullmatch(r"[0-9]+", lit[0]):
            second = f'"{int(lit[0]) + 1}"^^<{lit[1]}>'
        elif lit and (lit[2] or lit[1] == XSD + "string"):
            # Strings only: another datatype's lexical space (a WKT literal, a date) may not
            # take an arbitrary second value.
            tail = f"@{lit[2]}" if lit[2] else f"^^<{lit[1]}>"
            second = f'"{lit[0]} (second)"{tail}'
        else:
            return None
        return [], [f"{s} <{path}> {second} ."]
    raise ValueError(kind)


def score(out_dir, clean_keys, mutated_keys):
    """One engine on the injected set, from the expected violations and its result keys (focus
    node, path, constraint component, severity; run_phase0.count_report) on the data before and
    after the mutations. A result is matched by focus node, path and component.

    recall     the expected violations it reports on the mutated data
    precision  of its new results (on the mutated data and not before), those on a node the
               mutations touched (touched.txt: the mutated focus node, an IRI a removed or changed
               triple pointed to, or a node up to 3 links before the focus node, which inverse and
               sequence paths read): a mutation may break more
               than the one constraint it targets, but nothing on another node
    """
    def triples(path):
        with open(path, encoding="utf-8") as f:
            return {tuple(line.rstrip("\n").split("\t")[:3]) for line in f if line.strip()}
    expected = triples(os.path.join(out_dir, "expected.tsv"))
    before, after = triples(clean_keys), triples(mutated_keys)
    found = expected & after
    new = after - before
    with open(os.path.join(out_dir, "touched.txt"), encoding="utf-8") as f:
        touched = {line.rstrip("\n") for line in f}
    on_mutated = {k for k in new if k[0] in touched}
    return {"expected": len(expected), "found": len(found),
            "recall": round(len(found) / len(expected), 4) if expected else None,
            "already_before": len(expected & before), "new_results": len(new),
            "new_on_touched_nodes": len(on_mutated),
            "precision": round(len(on_mutated) / len(new), 4) if new else None,
            "missed_by_component": {c.rsplit("#", 1)[-1]: n for c, n in sorted(
                __import__("collections").Counter(e[2] for e in expected - after).items())}}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("data")
    ap.add_argument("shapes")
    ap.add_argument("out")
    ap.add_argument("--seed", type=int, default=31)
    ap.add_argument("--rate", type=float, default=0.01)
    a = ap.parse_args()
    by_class = rules(a.shapes)
    # Pass 1: the instances of the targeted classes (IRIs only: blank nodes get new labels).
    instances = {}
    with open(a.data, encoding="utf-8") as f:
        for line in f:
            if RDF_TYPE not in line:
                continue
            t = parse(line)
            if t and t[1] == RDF_TYPE and t[2][1:-1] in by_class and t[0].startswith("<"):
                instances.setdefault(t[0], set()).add(t[2][1:-1])
    nodes = sorted(instances)
    rng = random.Random(a.seed)
    drawn = rng.sample(nodes, round(len(nodes) * a.rate)) if nodes else []
    drawn_set = set(drawn)
    # Pass 2: the drawn nodes' own triples.
    own = {n: [] for n in drawn}
    lines = {n: [] for n in drawn}
    with open(a.data, encoding="utf-8") as f:
        for no, line in enumerate(f):
            if not line.startswith("<"):
                continue
            s = line[:line.find(">") + 1]
            if s in drawn_set:
                t = parse(line)
                if t:
                    own[s].append(t)
                    lines[s].append(no)
    # One mutation per drawn node, the kinds in turn (the next kind its class and triples allow).
    drop, add, expected, counts = set(), [], [], {k: 0 for k in KINDS}
    # The nodes a mutation touches: the focus node, the IRIs a removed or changed triple pointed
    # to (an inverse path such as ^era:startsAt fails on those), and the nodes that point to the
    # focus node, up to UPSTREAM hops (a sequence path such as era:netReference/era:startsAt).
    touched = set()
    turn = 0
    for n in drawn:
        options = [r for c in sorted(instances[n]) for r in by_class[c]]
        rng.shuffle(options)
        done = False
        for k in range(len(KINDS)):
            kind = KINDS[(turn + k) % len(KINDS)]
            for _, path, detail in [o for o in options if o[0] == kind]:
                m = mutate(kind, path, detail, own[n], rng)
                if m is None:
                    continue
                drop.update(lines[n][i] for i in m[0])
                add.extend(m[1])
                touched.add(n[1:-1])
                touched.update(own[n][i][2][1:-1] for i in m[0] if own[n][i][2].startswith("<"))
                expected.append((n[1:-1], path, COMPONENT[kind]))
                counts[kind] += 1
                turn = (turn + k + 1) % len(KINDS)
                done = True
                break
            if done:
                break
    os.makedirs(a.out, exist_ok=True)
    with open(a.data, encoding="utf-8") as f, open(os.path.join(a.out, "mutated.nt"), "w", encoding="utf-8") as out:
        for no, line in enumerate(f):
            if no not in drop:
                out.write(line)
        for line in add:
            out.write(line + "\n")
    # Up to UPSTREAM hops back from the mutated nodes: sequence paths such as
    # era:netReference/era:hasLrsCoordinate/era:offsetFromOrigin read a mutated node from there.
    frontier = {f"<{e[0]}>" for e in expected}
    for _ in range(UPSTREAM):
        found = set()
        with open(a.data, encoding="utf-8") as f:
            for line in f:
                if not line.startswith("<") or RDF_TYPE in line:
                    continue
                end = line.rstrip()[:-1].rstrip()
                if end.endswith(">") and end[end.rfind(" <") + 1:] in frontier:
                    found.add(line[:line.find(">") + 1])
        touched.update(n[1:-1] for n in found)
        frontier = found
    with open(os.path.join(a.out, "expected.tsv"), "w", encoding="utf-8") as out:
        for e in sorted(set(expected)):
            out.write("\t".join(e) + "\n")
    with open(os.path.join(a.out, "touched.txt"), "w", encoding="utf-8") as out:
        out.writelines(t + "\n" for t in sorted(touched))
    manifest = {"seed": a.seed, "rate": a.rate, "focus_nodes": len(nodes), "drawn": len(drawn),
                "mutated": len(expected), "touched_nodes": len(touched), "by_kind": counts,
                "lines_removed": len(drop), "lines_added": len(add)}
    json.dump(manifest, open(os.path.join(a.out, "manifest.json"), "w"), indent=1)
    print(json.dumps(manifest))


if __name__ == "__main__":
    sys.exit(main())
