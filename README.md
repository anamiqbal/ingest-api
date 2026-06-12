# Ingest API

A lightweight FastAPI service that accepts JSON payloads and persists them to SQLite — with a full DevSecOps CI pipeline.

[![CI](https://github.com/YOUR_USERNAME/ingest-api/actions/workflows/ci.yml/badge.svg)](https://github.com/YOUR_USERNAME/ingest-api/actions/workflows/ci.yml)

## Run locally

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --port 8010
```

Interactive docs: http://127.0.0.1:8010/docs

## Run with Docker

```bash
docker build -t ingest-api .
docker run -p 8010:8010 ingest-api
```

## Run the tests

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

## API

| Method | Path           | Purpose                                        |
|--------|----------------|------------------------------------------------|
| POST   | /payloads      | Ingest any JSON body (201 on success)          |
| GET    | /payloads      | List payloads, newest first (`limit`, `offset`)|
| GET    | /health        | Liveness check                                 |

## CI/CD pipeline (DevSecOps)

Every push and pull request to `main` runs six automated gates via GitHub Actions
(`.github/workflows/ci.yml`):

| Stage            | Tool      | What it catches                                      |
|------------------|-----------|------------------------------------------------------|
| Lint             | ruff      | Code-quality issues and common bugs                  |
| Tests            | pytest    | Functional regressions (6 tests, incl. edge cases)   |
| SAST             | bandit    | Security flaws in our own code (e.g. SQL injection)  |
| Dependency audit | pip-audit | Known CVEs in third-party packages                   |
| Secret scan      | gitleaks  | Credentials accidentally committed to git history    |
| Container scan   | Trivy     | CRITICAL/HIGH vulnerabilities in the Docker image    |

Plus **Dependabot** (`.github/dependabot.yml`) opens weekly PRs for dependency
and GitHub Actions updates, so security patches land continuously.

### Security decisions in the code itself

- **Parameterised SQL queries** everywhere — no string interpolation, no SQL injection.
- **Non-root container user** — the app runs as `appuser`, not root, limiting blast radius.
- **Slim base image** — `python:3.12-slim` keeps the attack surface small.
- **Config via environment variables** (`DB_PATH`) — no secrets or paths hardcoded.
- **`.gitignore` blocks `.env` and database files** from ever being committed.
- **Least-privilege workflow token** — the pipeline runs with `contents: read` only.

### Why "shift-left"?

All six gates run *before* code merges, so security problems are caught at the
cheapest possible moment — in a pull request, not in production. The container
scan only runs after lint and tests pass (`needs: [lint, test]`), keeping fast
feedback first and expensive checks later.
