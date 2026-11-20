#!/usr/bin/env python3
"""A minimal SPARQL protocol endpoint over an in-memory maplib Model, for benchmark v2.

maplib (https://github.com/DataTreehouse/maplib, Apache-2.0) is a Python library with no server
of its own. The general suites time every engine over HTTP, so this wraps a Model in the same
protocol: it reads the N-Triples file into memory (the "load"), prints one JSON line with the
load time and peak RSS, then serves

  GET|POST /query   query=...   SELECT/ASK -> application/sparql-results+json, or +xml when the
                                Accept header asks for XML and not JSON (the BSBM test driver
                                counts results from the XML form),
                                CONSTRUCT  -> the triples as N-Triples (one per line)
  POST     /update  update=...  SPARQL Update
  GET      /health              200 once the data is loaded

one request at a time (the suites use a single client). A failed request answers 500 with the
error and also prints it to stderr (docker logs). Used by engines/maplib.sh.
"""
import json
import re
import resource
import sys
import time
import urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer

from xml.sax.saxutils import escape, quoteattr

from maplib import Model

model = Model()

# The query form: the first keyword after the prologue (PREFIX/BASE lines and comments).
PROLOGUE = re.compile(r"^(?:\s+|#[^\n]*\n|(?:PREFIX|BASE)\b[^\n]*\n)*", re.I)


def is_graph_query(q):
    """CONSTRUCT or DESCRIBE, which maplib answers as tables of triples (SELECT and ASK as JSON)."""
    rest = q[PROLOGUE.match(q).end():].lstrip()
    return rest[:9].upper().startswith(("CONSTRUCT", "DESCRIBE"))


ESCAPES = str.maketrans({"\\": "\\\\", '"': '\\"', "\n": "\\n", "\r": "\\r"})
LANG_STRING = "<http://www.w3.org/1999/02/22-rdf-syntax-ns#langString>"
SINGLE = re.compile(r'^RDFType\.(IRI|BlankNode)\(\)$|^RDFType\.Literal\("([^"]*)"\)$')


def lexical(v):
    if isinstance(v, bool):
        return "true" if v else "false"
    return (v.isoformat() if hasattr(v, "isoformat") else str(v)).translate(ESCAPES)


def nt_single(v, kind, dt):
    """A value of a column of one RDF type: an IRI, a blank node or a literal of datatype dt."""
    if v is None:
        return None
    if kind == "IRI":
        return f"<{v}>"
    if kind == "BlankNode":
        return f"_:{v}"
    return f'"{lexical(v)}"^^<{dt}>'


def nt_multi(v):
    """A value of a column of several RDF types: a struct with one field per type (I = IRI,
    B = blank node, <langString> with l = its language, <datatype> = a literal of it)."""
    if v.get("I") is not None:
        return f"<{v['I']}>"
    if v.get("B") is not None:
        return f"_:{v['B']}"
    if v.get(LANG_STRING) is not None:
        return f'"{lexical(v[LANG_STRING])}"@{v["l"]}'
    for k, x in v.items():
        if k.startswith("<") and x is not None:
            return f'"{lexical(x)}"^^{k}'
    return None


def as_ntriples(tables):
    """CONSTRUCT results as N-Triples, one triple per line. maplib 0.22 writes CONSTRUCT as
    pretty Turtle (several objects on a line), which the suites cannot count triples from by
    lines, so the triple tables are asked for with their RDF types and written out here."""
    out = []
    for sm in tables:
        cols = []
        for c in ("subject", "predicate", "object"):
            m = SINGLE.match(str(sm.rdf_types[c]))
            cols.append((lambda v, k=m.group(1) or "Literal", d=m.group(2): nt_single(v, k, d)) if m else nt_multi)
        for row in sm.mappings.iter_rows():
            terms = [f(v) for f, v in zip(cols, row)]
            if None not in terms:
                out.append(" ".join(terms) + " .\n")
    return "".join(out)


def json_to_xml(doc):
    """SPARQL results JSON -> SPARQL results XML."""
    d = json.loads(doc)
    out = ['<?xml version="1.0"?>\n<sparql xmlns="http://www.w3.org/2005/sparql-results#">', "<head>"]
    out += [f"<variable name={quoteattr(v)}/>" for v in d.get("head", {}).get("vars", [])]
    out.append("</head>")
    if "boolean" in d:
        out.append(f"<boolean>{'true' if d['boolean'] else 'false'}</boolean>")
    else:
        out.append("<results>")
        for b in d.get("results", {}).get("bindings", []):
            out.append("<result>")
            for k, t in b.items():
                v = escape(t.get("value", ""))
                if t.get("type") == "uri":
                    term = f"<uri>{v}</uri>"
                elif t.get("type") == "bnode":
                    term = f"<bnode>{v}</bnode>"
                elif "datatype" in t:
                    term = f"<literal datatype={quoteattr(t['datatype'])}>{v}</literal>"
                elif "xml:lang" in t:
                    term = f"<literal xml:lang={quoteattr(t['xml:lang'])}>{v}</literal>"
                else:
                    term = f"<literal>{v}</literal>"
                out.append(f"<binding name={quoteattr(k)}>{term}</binding>")
            out.append("</result>")
        out.append("</results>")
    out.append("</sparql>")
    return "\n".join(out)


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *_):
        pass

    def params(self):
        q = urllib.parse.urlsplit(self.path).query
        p = urllib.parse.parse_qs(q)
        if self.command == "POST":
            n = int(self.headers.get("Content-Length") or 0)
            body = self.rfile.read(n).decode()
            ctype = self.headers.get("Content-Type", "")
            if ctype.startswith("application/sparql-query"):
                p["query"] = [body]
            elif ctype.startswith("application/sparql-update"):
                p["update"] = [body]
            else:
                p.update(urllib.parse.parse_qs(body))
        return {k: v[0] for k, v in p.items()}

    def send(self, code, body, ctype="text/plain; charset=utf-8"):
        b = body.encode() if isinstance(body, str) else body
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def handle_any(self):
        path = urllib.parse.urlsplit(self.path).path
        try:
            if path == "/health":
                return self.send(200, "ok")
            p = self.params()
            if path == "/query" and "query" in p:
                q = p["query"]
                if is_graph_query(q):
                    return self.send(200, as_ntriples(model.query(q, solution_mappings=True)), "application/n-triples")
                r = model.query(q, return_format="json")
                accept = self.headers.get("Accept", "")
                if "xml" in accept and "json" not in accept:
                    return self.send(200, json_to_xml(r), "application/sparql-results+xml")
                return self.send(200, r, "application/sparql-results+json")
            if path == "/update" and "update" in p:
                model.update(p["update"])
                return self.send(204, b"")
            return self.send(400, "expected /query?query=... or /update with update=...")
        except BaseException as e:  # noqa: BLE001 - also maplib's PanicException; reported and logged
            msg = f"{type(e).__name__}: {e}"
            print(f"ERROR {path}: {msg[:2000]}", file=sys.stderr, flush=True)
            return self.send(500, msg)

    do_GET = handle_any
    do_POST = handle_any


def main():
    path, port = sys.argv[1], int(sys.argv[2])
    t = time.perf_counter()
    model.read(path, parallel=True)
    load_s = time.perf_counter() - t
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024
    print(json.dumps({"load_s": round(load_s, 3), "load_peak_rss_bytes": rss}), flush=True)
    HTTPServer(("0.0.0.0", port), Handler).serve_forever()


if __name__ == "__main__":
    main()
