#!/usr/bin/env python3
"""A minimal SPARQL protocol endpoint over an in-memory maplib Model, for benchmark v2.

maplib (https://github.com/DataTreehouse/maplib, Apache-2.0) is a Python library with no server
of its own. The general suites time every engine over HTTP, so this wraps a Model in the same
protocol: it reads the N-Triples file into memory (the "load"), prints one JSON line with the
load time and peak RSS, then serves

  GET|POST /query   query=...   SELECT/ASK -> application/sparql-results+json, or +xml when the
                                Accept header asks for XML and not JSON (the BSBM test driver
                                counts results from the XML form),
                                CONSTRUCT  -> the triples as text (one per line)
  POST     /update  update=...  SPARQL Update; INSERT DATA {...}, which maplib 0.20.26 does not
                                implement, is sent as the equivalent INSERT {...} WHERE {}
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


INSERT_DATA = re.compile(r"^(\s*(?:(?:PREFIX|BASE)\b[^\n]*\n\s*)*)INSERT\s+DATA\s*(\{(?:[^{}]|\{[^{}]*\})*\})\s*;?\s*$", re.S | re.I)


def as_supported_update(u):
    """A lone INSERT DATA as INSERT ... WHERE {} (same triples; maplib 0.20.26 panics on INSERT DATA).
    Only a single operation is rewritten (GRAPH blocks may nest one level); anything else is left as it is."""
    m = INSERT_DATA.match(u)
    return f"{m.group(1)}INSERT {m.group(2)} WHERE {{}}" if m else u


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
                r = model.query(p["query"], return_json=True)
                if r.lstrip().startswith("{"):
                    accept = self.headers.get("Accept", "")
                    if "xml" in accept and "json" not in accept:
                        return self.send(200, json_to_xml(r), "application/sparql-results+xml")
                    return self.send(200, r, "application/sparql-results+json")
                return self.send(200, r, "application/n-triples")
            if path == "/update" and "update" in p:
                model.update(as_supported_update(p["update"]))
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
