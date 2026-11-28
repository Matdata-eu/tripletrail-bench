#!/usr/bin/env python3
"""Print the machine and software versions of a benchmark run as JSON."""
import json
import os
import platform
import subprocess


def out(*cmd):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        return (r.stdout.strip() or r.stderr.strip())[-400:]
    except Exception as e:  # noqa: BLE001
        return f"n/a ({e})"


def budget(here):
    try:
        r = subprocess.run(["bash", os.path.join(here, "engines", "budget.sh"), "json"],
                           capture_output=True, text=True, timeout=60)
        return json.loads(r.stdout)
    except Exception as e:  # noqa: BLE001
        return f"n/a ({e})"


def main():
    cpu = ""
    try:
        for line in open("/proc/cpuinfo"):
            if line.startswith("model name"):
                cpu = line.split(":", 1)[1].strip()
                break
    except OSError:
        pass
    mem = ""
    try:
        mem = open("/proc/meminfo").readline().split(":", 1)[1].strip()
    except OSError:
        pass
    here = os.path.dirname(os.path.abspath(__file__))
    env = {
        "cpu": cpu, "cpus": os.cpu_count(), "memory": mem, "kernel": platform.release(),
        "disk_free": out("df", "-h", here),
        "tripletrail_commit": out("git", "-C", os.environ.get("TRIPLETRAIL_SRC", os.path.join(here, "../../core")), "rev-parse", "HEAD"),
        "bench_commit": out("git", "-C", here, "rev-parse", "HEAD"),
        "postgres": out("psql", "--version"),
        # from the packages, so the server need not run
        "postgis": out("dpkg-query", "-W", "-f", "${Package} ${Version}\\n", "postgresql-16-postgis-3",
                       "postgresql-16-pgrouting"),
        "docker": out("docker", "version", "--format", "{{.Server.Version}}"),
        "graphdb_image": out("docker", "image", "inspect", "--format", "{{.Id}} {{index .RepoTags 0}}",
                             os.environ.get("GRAPHDB_IMAGE", "mirror.gcr.io/ontotext/graphdb:10.8.0")),
        "qlever_image": out("docker", "image", "inspect", "--format",
                            "{{.Id}} {{index .Config.Labels \"org.opencontainers.image.version\"}}",
                            os.environ.get("QLEVER_IMAGE", "mirror.gcr.io/adfreiburg/qlever:latest")),
        "oxigraph_image": out("docker", "image", "inspect", "--format", "{{.Id}} {{index .RepoTags 0}}",
                              os.environ.get("OXIGRAPH_IMAGE", "ghcr.io/oxigraph/oxigraph:0.5.13")),
        # the last lines only: JAVA_TOOL_OPTIONS (proxy settings) is echoed first
        "java": "\n".join(out("java", "-version").splitlines()[-3:]),
        "jena_jar": "jena-fuseki-geosparql-6.2.0.jar",
        # The memory and cores every engine was given (engines/budget.sh, #94).
        "budget": budget(here),
    }
    print(json.dumps(env, indent=1))


if __name__ == "__main__":
    main()
