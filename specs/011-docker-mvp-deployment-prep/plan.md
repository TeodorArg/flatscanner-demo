# Implementation Plan: Docker MVP Deployment Prep

## Summary

Prepare the repository for a Docker-first VPS deployment where `flatscanner` runs as a web container plus worker container behind an already-existing nginx ingress container.

## Files And Areas

- `Dockerfile`
- `.dockerignore`
- `.env.example`
- `deploy/`
- `src/jobs/cli.py`
- `tests/test_worker_cli.py`
- `docs/project/backend/`

## Risks

- The target server already owns `80/443` through another nginx container, so `flatscanner` must stay on localhost-only ports.
- Worker startup must stay simple and not require a separate process manager inside the container.
- Docker deployment guidance must not imply PostgreSQL persistence is already wired when it is not.

## Validation

- Run `python -m pytest -q`
- Run `docker compose -f deploy/docker-compose.vps.yml config`
- Run `python -m src.jobs.cli` import-level validation without letting it block indefinitely

