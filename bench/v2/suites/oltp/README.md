# OLTP suite

Many small concurrent requests, as an editing application on top of a triple store sends
them: point reads, small updates and Graph Store writes, alone and mixed, from 1 to 64
clients. Each client is a closed loop (send, wait for the answer, send the next) on its own
keep-alive connection; latency is wall-clock at the client, HTTP included. The load generator
is `main.go` (Go, standard library only: `go build -o oltp .`).

## Data

`oltp gen -assets 200000 -docs 10000 -out oltp.nq` writes 2.1M quads: 200,000 assets of 10
triples (type, label, status, owner, km, next asset, modified, version, a WKT point) in the
default graph, and 10,000 named graphs ("documents") of 10 triples. Owners are
`urn:sparql-guard:user:team0..15`; 5% of assets are `retired`.

## Workloads

| name | request |
|---|---|
| point | `SELECT ?p ?o WHERE { <asset> ?p ?o }` |
| lookup | asset by its label literal, with its km |
| hop | asset → next asset → its label and status |
| insert | `INSERT DATA` of a new asset, 6 triples |
| edit | `DELETE/INSERT … WHERE` on one asset (modified := NOW(), version + 1) |
| gsp | Graph Store `PUT ?graph=<doc>` of 10 triples (N-Triples) |
| read90 | 30% point, 30% lookup, 30% hop, 10% edit |
| rw50 | 25% point, 25% hop, 25% edit, 25% insert |

Client k edits assets of team k mod 16 only, so the same run works under row rules.

## Scenarios (TripleTrail)

- `open`: no `--auth-config`.
- `policy`: `policy.json` (trusted header, one policy that lets authenticated agents write).
- `rows`: `rows.json`: also `sg:visibleIf` (hides retired assets) and `sg:editableIf`
  (an agent edits only the assets it owns).

## Running

```bash
go build -o oltp . && ./oltp gen -out /data/oltp.nq
tripletrail load --location work/mg --dataset ds /data/oltp.nq
TRIPLETRAIL_RESULT_CACHE_MB=0 tripletrail serve --location work/mg --dataset ds --bind 127.0.0.1:7070 &
./run.sh tripletrail            # appends to ../../results/oltp/results.jsonl
./report.py                  # writes ../../results/oltp/report.md
```

Oxigraph: `oxigraph load` + `optimize` + `serve` (docker image ghcr.io/oxigraph/oxigraph:0.5.13).
Fuseki: `tdb2.tdbloader` then `jena-fuseki-server-6.2.0.jar --tdb2 --loc DB --update /ds`
(4 GB heap). Restart from a fresh copy of the store between scenarios: the write workloads
add data. Never run this in GitHub-hosted CI.

## Results of 2026-11-13

`../../results/oltp/report.md`, from a 4-core, 16 GB cloud container (load generator on the
same machine), main at 0fc1f4a with the one-line fix of #690 applied locally (without it, runs
with more than 4 clients hang). Durability differs: TripleTrail and Fuseki sync their log on
every commit, Oxigraph (RocksDB) does not.

- Reads: TripleTrail leads (point reads 21,600/s at 16-64 clients, Oxigraph 13,000, Fuseki
  1,700), with the lowest p99.
- Writes: TripleTrail plateaus at ~2,000 inserts/s and ~1,400 edits/s from 4 clients (Fuseki
  ~120/s; Oxigraph 7,000-8,700/s without per-commit fsync). #709.
- Graph Store PUT of a small N-Triples graph: 25/s, 40 ms each, serialized (Oxigraph 2,100/s). #702.
- Row rules: reads 3x slower (#708); writes ~0.5/s, 1.7 s each (#700).
- More than 4 concurrent keep-alive clients hang (#690).
