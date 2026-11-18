// OLTP load generator for SPARQL endpoints: many small concurrent reads and writes, as an
// editing application on top of a triple store sends them. Standard library only.
//
//	oltp gen  -assets 200000 -docs 10000 -out data.nq
//	oltp run  -engine tripletrail -query URL -update URL -gsp URL -workloads point,edit
//	          -clients 1,4,16,64 -duration 10s -warmup 2s -out results.json
//
// Each client is a closed loop (send, wait for the answer, send the next), on its own
// keep-alive connection. Latency is wall-clock at the client, HTTP included.
package main

import (
	"bufio"
	"bytes"
	"encoding/json"
	"flag"
	"fmt"
	"io"
	"math/rand"
	"net/http"
	"net/url"
	"os"
	"sort"
	"strconv"
	"strings"
	"sync"
	"sync/atomic"
	"time"
)

const (
	ns    = "http://example.org/oltp/"
	teams = 16
	agent = "urn:sparql-guard:user:team"
	xsd   = "http://www.w3.org/2001/XMLSchema#"
	geo   = "http://www.opengis.net/ont/geosparql#"
)

func asset(i int) string   { return fmt.Sprintf("<%sasset/%d>", ns, i) }
func doc(i int) string     { return fmt.Sprintf("<%sdoc/%d>", ns, i) }
func p(name string) string { return "<" + ns + name + ">" }

var classes = []string{"Signal", "Switch", "Balise", "Sign"}

func status(i int) string {
	switch i % 20 {
	case 0:
		return "retired"
	case 1:
		return "planned"
	}
	return "active"
}

func gen(args []string) {
	fs := flag.NewFlagSet("gen", flag.ExitOnError)
	n := fs.Int("assets", 200000, "assets (about 11 triples each)")
	docs := fs.Int("docs", 10000, "named graphs of 10 triples each")
	out := fs.String("out", "oltp.nq", "N-Quads output")
	fs.Parse(args)
	f, err := os.Create(*out)
	if err != nil {
		panic(err)
	}
	w := bufio.NewWriterSize(f, 1<<20)
	rng := rand.New(rand.NewSource(42))
	for i := 0; i < *n; i++ {
		a := asset(i)
		g := fmt.Sprintf("<%sgeom/%d>", ns, i)
		km := fmt.Sprintf("%.3f", rng.Float64()*500)
		fmt.Fprintf(w, "%s <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> %s .\n", a, p(classes[i%len(classes)]))
		fmt.Fprintf(w, "%s %s \"Asset %d\" .\n", a, p("label"), i)
		fmt.Fprintf(w, "%s %s \"%s\" .\n", a, p("status"), status(i))
		fmt.Fprintf(w, "%s %s <%s%d> .\n", a, p("owner"), agent, i%teams)
		fmt.Fprintf(w, "%s %s \"%s\"^^<%sdecimal> .\n", a, p("km"), km, xsd)
		fmt.Fprintf(w, "%s %s %s .\n", a, p("next"), asset((i+1)%*n))
		fmt.Fprintf(w, "%s %s \"2026-01-01T00:00:00Z\"^^<%sdateTime> .\n", a, p("modified"), xsd)
		fmt.Fprintf(w, "%s %s \"1\"^^<%sinteger> .\n", a, p("version"), xsd)
		fmt.Fprintf(w, "%s <%shasGeometry> %s .\n", a, geo, g)
		fmt.Fprintf(w, "%s <%sasWKT> \"POINT(%.6f %.6f)\"^^<%swktLiteral> .\n", g, geo, 5+rng.Float64()*25, 58+rng.Float64()*12, geo)
	}
	for j := 0; j < *docs; j++ {
		for k := 0; k < 10; k++ {
			fmt.Fprintf(w, "%s %s \"note %d of document %d\" %s .\n", doc(j), p(fmt.Sprintf("field%d", k)), k, j, doc(j))
		}
	}
	w.Flush()
	f.Close()
}

// ---- requests

type kind int

const (
	query kind = iota
	update
	gspPut
)

type request struct {
	op   string
	kind kind
	body string
	gsp  string // graph IRI for gspPut
}

type client struct {
	id     int
	rng    *rand.Rand
	seq    int
	assets int
	docs   int
}

// pick an asset the client's team owns and may see (not retired).
func (c *client) ownAsset() int {
	team := c.id % teams
	for {
		i := c.rng.Intn(c.assets/teams)*teams + team
		if i < c.assets && status(i) != "retired" {
			return i
		}
	}
}

func (c *client) anyAsset() int { return c.ownAsset() } // visible to every rule set we test

func (c *client) make(op string) request {
	switch op {
	case "point":
		return request{op, query, fmt.Sprintf("SELECT ?p ?o WHERE { %s ?p ?o }", asset(c.anyAsset())), ""}
	case "lookup":
		return request{op, query, fmt.Sprintf("SELECT ?a ?km WHERE { ?a %s \"Asset %d\" ; %s ?km }", p("label"), c.anyAsset(), p("km")), ""}
	case "hop":
		return request{op, query, fmt.Sprintf("SELECT ?n ?l ?s WHERE { %s %s ?n . ?n %s ?l ; %s ?s }", asset(c.anyAsset()), p("next"), p("label"), p("status")), ""}
	case "insert":
		c.seq++
		s := fmt.Sprintf("<%snew/%d-%d-%d>", ns, c.id, c.seq, time.Now().UnixNano())
		return request{op, update, fmt.Sprintf(
			"INSERT DATA { %s a %s ; %s \"New %d\" ; %s \"planned\" ; %s <%s%d> ; %s \"1.5\"^^<%sdecimal> ; %s 1 }",
			s, p("Signal"), p("label"), c.seq, p("status"), p("owner"), agent, c.id%teams, p("km"), xsd, p("version")), ""}
	case "edit":
		a := asset(c.ownAsset())
		return request{op, update, fmt.Sprintf(
			"DELETE { %[1]s %[2]s ?m ; %[3]s ?v } INSERT { %[1]s %[2]s ?now ; %[3]s ?v2 } WHERE { %[1]s %[2]s ?m ; %[3]s ?v . BIND(NOW() AS ?now) BIND(?v + 1 AS ?v2) }",
			a, p("modified"), p("version")), ""}
	case "gsp":
		j := c.rng.Intn(c.docs)
		var b strings.Builder
		for k := 0; k < 10; k++ {
			fmt.Fprintf(&b, "%s %s \"edit %d of document %d\" .\n", doc(j), p(fmt.Sprintf("field%d", k)), c.rng.Intn(1000000), j)
		}
		return request{op, gspPut, b.String(), strings.Trim(doc(j), "<>")}
	}
	panic("unknown op " + op)
}

var mixes = map[string][]struct {
	op string
	w  int
}{
	"read90": {{"point", 30}, {"lookup", 30}, {"hop", 30}, {"edit", 10}},
	"rw50":   {{"point", 25}, {"hop", 25}, {"edit", 25}, {"insert", 25}},
}

func (c *client) next(workload string) request {
	if m, ok := mixes[workload]; ok {
		r := c.rng.Intn(100)
		for _, e := range m {
			if r < e.w {
				return c.make(e.op)
			}
			r -= e.w
		}
	}
	return c.make(workload)
}

// ---- running

type endpoints struct {
	query, update, gsp string
	headers            map[string]string // per client: %d replaced by the team
	form               bool
}

func send(h *http.Client, ep *endpoints, c *client, r request) (int, error) {
	var req *http.Request
	var err error
	switch r.kind {
	case query:
		req, err = http.NewRequest("POST", ep.query, strings.NewReader(r.body))
		req.Header.Set("Content-Type", "application/sparql-query")
		req.Header.Set("Accept", "application/sparql-results+json")
	case update:
		if ep.form {
			req, err = http.NewRequest("POST", ep.update, strings.NewReader("update="+url.QueryEscape(r.body)))
			req.Header.Set("Content-Type", "application/x-www-form-urlencoded")
		} else {
			req, err = http.NewRequest("POST", ep.update, strings.NewReader(r.body))
			req.Header.Set("Content-Type", "application/sparql-update")
		}
	case gspPut:
		req, err = http.NewRequest("PUT", ep.gsp+"?graph="+url.QueryEscape(r.gsp), strings.NewReader(r.body))
		req.Header.Set("Content-Type", "application/n-triples")
	}
	if err != nil {
		return 0, err
	}
	for k, v := range ep.headers {
		req.Header.Set(k, strings.ReplaceAll(v, "%d", strconv.Itoa(c.id%teams)))
	}
	resp, err := h.Do(req)
	if err != nil {
		return 0, err
	}
	io.Copy(io.Discard, resp.Body)
	resp.Body.Close()
	return resp.StatusCode, nil
}

type opStats struct {
	N    int     `json:"n"`
	P50  float64 `json:"p50_ms"`
	P90  float64 `json:"p90_ms"`
	P99  float64 `json:"p99_ms"`
	Max  float64 `json:"max_ms"`
	Mean float64 `json:"mean_ms"`
	Errs int     `json:"errors"`
}

type result struct {
	Engine   string              `json:"engine"`
	Scenario string              `json:"scenario"`
	Workload string              `json:"workload"`
	Clients  int                 `json:"clients"`
	Seconds  float64             `json:"seconds"`
	OpsPerS  float64             `json:"ops_per_s"`
	All      opStats             `json:"all"`
	Ops      map[string]*opStats `json:"ops"`
	FirstErr string              `json:"first_error,omitempty"`
}

func stats(lat []float64, errs int) *opStats {
	s := &opStats{N: len(lat), Errs: errs}
	if len(lat) == 0 {
		return s
	}
	sort.Float64s(lat)
	q := func(f float64) float64 { return lat[int(f*float64(len(lat)-1))] }
	sum := 0.0
	for _, v := range lat {
		sum += v
	}
	s.P50, s.P90, s.P99, s.Max, s.Mean = q(0.5), q(0.9), q(0.99), lat[len(lat)-1], sum/float64(len(lat))
	return s
}

func runOne(ep *endpoints, workload string, nclients int, warmup, dur time.Duration, assets, docs int, seed int64) result {
	tr := &http.Transport{MaxIdleConnsPerHost: 1024, MaxConnsPerHost: 0, DisableCompression: true}
	h := &http.Client{Transport: tr, Timeout: 120 * time.Second}
	defer tr.CloseIdleConnections()
	type sample struct {
		op  string
		ms  float64
		err bool
	}
	var measuring atomic.Bool
	var stop atomic.Bool
	var firstErr atomic.Value
	per := make([][]sample, nclients)
	var wg sync.WaitGroup
	for k := 0; k < nclients; k++ {
		wg.Add(1)
		go func(k int) {
			defer wg.Done()
			c := &client{id: k, rng: rand.New(rand.NewSource(seed*1000 + int64(k))), assets: assets, docs: docs}
			for !stop.Load() {
				r := c.next(workload)
				t := time.Now()
				code, err := send(h, ep, c, r)
				ms := float64(time.Since(t).Microseconds()) / 1000
				bad := err != nil || code >= 300
				if bad && firstErr.Load() == nil {
					firstErr.Store(fmt.Sprintf("%s: %d %v", r.op, code, err))
				}
				if measuring.Load() {
					per[k] = append(per[k], sample{r.op, ms, bad})
				}
			}
		}(k)
	}
	time.Sleep(warmup)
	measuring.Store(true)
	t0 := time.Now()
	time.Sleep(dur)
	measuring.Store(false)
	el := time.Since(t0).Seconds()
	stop.Store(true)
	wg.Wait()
	all := []float64{}
	byOp := map[string][]float64{}
	errsOp := map[string]int{}
	errs := 0
	for _, ss := range per {
		for _, s := range ss {
			if s.err {
				errs++
				errsOp[s.op]++
				continue
			}
			all = append(all, s.ms)
			byOp[s.op] = append(byOp[s.op], s.ms)
		}
	}
	res := result{Workload: workload, Clients: nclients, Seconds: el, OpsPerS: float64(len(all)) / el,
		Ops: map[string]*opStats{}}
	res.All = *stats(all, errs)
	for op, l := range byOp {
		res.Ops[op] = stats(l, errsOp[op])
	}
	for op, e := range errsOp {
		if _, ok := res.Ops[op]; !ok {
			res.Ops[op] = &opStats{Errs: e}
		}
	}
	if v := firstErr.Load(); v != nil {
		res.FirstErr = v.(string)
	}
	return res
}

func run(args []string) {
	fs := flag.NewFlagSet("run", flag.ExitOnError)
	engine := fs.String("engine", "", "engine name (for the results)")
	scenario := fs.String("scenario", "open", "scenario name (for the results)")
	q := fs.String("query", "", "query endpoint")
	u := fs.String("update", "", "update endpoint")
	g := fs.String("gsp", "", "graph store endpoint")
	form := fs.Bool("form", false, "send updates as form posts")
	hdr := fs.String("header", "", "extra header Name: value; %d is replaced by the client's team (0..15)")
	wl := fs.String("workloads", "point,lookup,hop,insert,edit,gsp,read90,rw50", "workloads")
	cl := fs.String("clients", "1,2,4,8,16,32,64", "client counts")
	dur := fs.Duration("duration", 10*time.Second, "measured time per point")
	warm := fs.Duration("warmup", 2*time.Second, "unmeasured time before each point")
	assets := fs.Int("assets", 200000, "assets in the data")
	docs := fs.Int("docs", 10000, "documents in the data")
	out := fs.String("out", "", "append JSON lines here")
	fs.Parse(args)
	ep := &endpoints{query: *q, update: *u, gsp: *g, form: *form, headers: map[string]string{}}
	if *hdr != "" {
		k, v, _ := strings.Cut(*hdr, ":")
		ep.headers[strings.TrimSpace(k)] = strings.TrimSpace(v)
	}
	var w io.Writer = io.Discard
	if *out != "" {
		f, err := os.OpenFile(*out, os.O_CREATE|os.O_APPEND|os.O_WRONLY, 0o644)
		if err != nil {
			panic(err)
		}
		defer f.Close()
		w = f
	}
	seed := int64(1)
	for _, workload := range strings.Split(*wl, ",") {
		for _, cs := range strings.Split(*cl, ",") {
			n, _ := strconv.Atoi(cs)
			seed++
			r := runOne(ep, workload, n, *warm, *dur, *assets, *docs, seed)
			r.Engine, r.Scenario = *engine, *scenario
			line, _ := json.Marshal(r)
			w.Write(append(line, '\n'))
			fmt.Printf("%-9s %-8s %-7s c=%-3d %8.1f ops/s  p50 %7.2f  p99 %8.2f ms  errors %d %s\n",
				*engine, *scenario, workload, n, r.OpsPerS, r.All.P50, r.All.P99, r.All.Errs, r.FirstErr)
		}
	}
}

func main() {
	if len(os.Args) < 2 {
		fmt.Fprintln(os.Stderr, "usage: oltp gen|run [flags]")
		os.Exit(2)
	}
	_ = bytes.MinRead
	switch os.Args[1] {
	case "gen":
		gen(os.Args[2:])
	case "run":
		run(os.Args[2:])
	default:
		fmt.Fprintln(os.Stderr, "usage: oltp gen|run [flags]")
		os.Exit(2)
	}
}
