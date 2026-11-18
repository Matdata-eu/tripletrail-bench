# Running the benchmarks on a rented machine

GitHub-hosted runners are too small for these benchmarks, so the manual workflow
[`bench.yml`](../../../.github/workflows/bench.yml) (**Benchmarks**) rents a Hetzner Cloud
server for the length of one run:

1. `approve`: waits for a maintainer's approval (the `benchmark` environment). Nothing is
   rented before that.
2. `provision` (GitHub-hosted): asks GitHub for a runner registration token and creates the
   server through the Hetzner API, with [`setup-runner.sh`](setup-runner.sh) as its user data.
   The script installs Docker, Java, Python and Rust and registers the server as an
   **ephemeral** runner with a label unique to the run (`bench-<run id>`): it takes this one
   job only. `await-runner` then waits up to 30 minutes for that runner to come online.
3. `bench` (on the new server): checks out TripleTrail at the input `core_ref` into `core/`,
   builds it, downloads or generates the data, runs every engine in turn (dropping each store
   after its run) and uploads the results as an artifact.
4. `teardown` (GitHub-hosted): deletes the server, always, also when the run failed or was
   cancelled. It looks the server up by the run label, so it also finds a server whose
   creation step failed halfway, and then deletes the run's extra volume, if there is one.
5. `collect` (GitHub-hosted): pushes the results to a `bench-results/<run id>` branch and opens
   a pull request for it. Merging it publishes the results on the dashboard.

Only the server is billed, by the hour (a CCX43, 16 dedicated vCPU / 64 GB / 360 GB, costs
roughly €0.15–0.20 an hour; the `full` profile takes 8 to 12 hours).

## Why this is safe in a public repository

- The workflow runs only by hand (`workflow_dispatch`), which needs write access, and then
  only after approval in the `benchmark` environment. No workflow here runs on pull requests.
- The rented server is an ephemeral runner with a label unique to the run, and it is deleted
  by `teardown`.
- Settings → Actions → General → "Fork pull request workflows from outside collaborators":
  **Require approval for all outside collaborators**, so no outside code runs without a look.

## One-time setup

1. Hetzner: Cloud Console → project → **Security → API tokens → Generate API token**,
   permission **Read & Write**.
2. GitHub: a fine-grained personal access token for this repository only, with the repository
   permission **Administration: Read and write** (to issue runner registration tokens; the
   workflow's own token cannot).
3. Settings → Secrets and variables → Actions → **New repository secret**: `HCLOUD_TOKEN`
   (step 1) and `RUNNER_ADMIN_TOKEN` (step 2).
4. Settings → Environments → **New environment** `benchmark` → Required reviewers: yourself.
5. Settings → Actions → General → Workflow permissions: **Read and write**, and **Allow GitHub
   Actions to create and approve pull requests** (for the results pull request).
6. Settings → Pages → Source: **GitHub Actions** (the dashboard, `pages.yml`).

## Each run

Actions → **Benchmarks** → Run workflow. The defaults (suite `all`, dataset `full`, engines
`default`, machine `ccx43`, core `main`) run every job of
[`../profiles/full.txt`](../profiles/full.txt) (benchmark v2 small / large / OSM Norway,
Geographica 2, BSBM 1M and 10M, Sparqloscope on BSBM and RINF, Trainmarks) on one server, one
after the other, through [`../bench.sh`](../bench.sh). Dataset `dashboard` adds the scale
benchmark (OSM Benelux and Europe, about 4 hours more, with a 600 GB volume). One job on its
own: e.g. suite `sparqloscope`, dataset `dblp`. Set `core_ref` to a release tag (such as
`v0.1.0`) to measure a release.

All results of a run come back in **one commit**: the result folders of every job, a run
manifest `bench/v2/results/runs/<run id>.json` (TripleTrail commit, harness commit, machine,
status and time of each job, link to the run) and the index `bench/v2/results/runs/README.md`.
A job whose inputs or tools are missing is skipped with the reason in the manifest; a failed job
does not stop the others, but the run is marked failed.

### Inputs that cannot be generated

[`../data/fetch_inputs.sh`](../data/fetch_inputs.sh) downloads them once per server:

- `norway-rail-landuse-admin.osm.pbf` (OSM as of 2026-11-05, 96 MB; © OpenStreetMap
  contributors, ODbL): an asset of the release **`bench-data`** of this repository (or of
  `BENCH_DATA_REPO`, a repository variable; set the secret `BENCH_DATA_TOKEN` if that one is
  private). Without it the OSM Norway job is skipped.
- The six Geographica 2 datasets, from https://geographica2.di.uoa.gr/ with pinned SHA-256
  sums. They carry no licence of their own, so they are never copied here. If one changes
  upstream, the Geographica job is skipped with a warning. The query lists are in
  [`../geographica/queries`](../geographica/queries) (Apache-2.0).

To look at a running server, add an SSH key to the Hetzner project (Security → SSH keys) and
`ssh root@<ip>`. If a run ever leaves a server behind, delete it in the Cloud Console: servers
and volumes created by the workflow carry the label `purpose=tripletrail-bench`.

## By hand, without the workflow

Create a CCX43 with Ubuntu 24.04, SSH in, run the apt line of `setup-runner.sh`, clone this
repository and TripleTrail into its `core/` folder, build (`cd core && cargo build --release -p
tripletrail-server`) and run e.g. `bench/v2/bench.sh all full`. Delete the server afterwards: a
stopped server is still billed.
