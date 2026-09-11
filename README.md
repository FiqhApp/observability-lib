# observability-lib

Shared OpenTelemetry init/shutdown helpers, extracted out of
`orchestrator-service`, `fiqh-service`, and `hadith-service` — all three
carried a verbatim copy of the same `observability.py`, which had crossed
from "duplicated within one repo" to "duplicated across three repos" once
the backend split into separate repos. This package is that file, made
installable.

```python
from observability import init_observability, shutdown_otel
```

Deliberately kept the import name `observability` (the distribution name
is `observability-lib`, but the importable package is `observability`) so
consuming services didn't need any code changes — only their
`pyproject.toml` and Dockerfile changed, not `main.py`/`server.py`.

## What it does

- `init_observability(service_name, collector_endpoint="http://otel-collector:4317")`
  — sets up an OTLP gRPC exporter for traces, metrics, and logs (via a
  `logging.Handler` attached to the root logger), tagged with
  `service.name=<service_name>`.
- `shutdown_otel(trace, metrics)` — flushes/shuts down the trace and meter
  providers. Called via `atexit.register(shutdown_otel, trace, metrics)`
  in each service.

This is instrumentation setup (the "observability" side: getting telemetry
out of the services), not monitoring/alerting (dashboards, alert rules,
SLOs) — that's a separate concern that belongs in the `deployment` repo's
infra later (e.g. Grafana/alerting config), not in this package.

## Consuming this package

Each service's `pyproject.toml`:

```toml
dependencies = [
    # ...,
    "observability-lib",
]

[tool.uv.sources]
observability-lib = { git = "https://github.com/<your-org-or-user>/observability-lib.git", tag = "v0.1.0" }
```

Replace `<your-org-or-user>` with the actual GitHub org/username once this
repo is pushed. `uv sync` / `uv lock` will then clone this repo at the
pinned tag — so it needs to be reachable (network + auth) from wherever
`uv sync`/`uv lock` runs, including inside each service's Docker build.
**Recommendation: keep this repo public.** It holds no secrets or business
logic, and a private repo would need a credential (deploy key / PAT)
wired into every consumer's CI and Dockerfile builder stage just to clone
it — not worth the complexity for a ~40-line shared helper.

Each consuming service's Dockerfile builder stage also needs `git`
installed (the `uv:python3.12-bookworm-slim` base image doesn't include it
by default), since `uv sync --frozen` has to clone this repo during the
Docker build.

## Versioning

Tag releases (`git tag v0.1.0 && git push --tags`) and have consumers pin
to a tag, not a branch — so a change here doesn't silently change behavior
in three services at once. Bump the tag and update each consumer's
`pyproject.toml` deliberately when you want them to pick up a change.

## Local development

```bash
uv sync
uv build   # sanity-check the package builds
```
