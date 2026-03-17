# Feature Spec: Docker MVP Deployment Prep

## Context

The application MVP is close to live testing, but the repository still lacks a reproducible server deployment layer for the existing FastAPI web service and Redis-backed worker.

The target environment is a remote Ubuntu VPS that already runs Docker and an nginx container on ports `80/443`. `flatscanner` should fit into that shape without taking over the public ingress layer.

## Scope

- Add a Docker image for the application
- Add a worker entrypoint suitable for container execution
- Add a Docker Compose stack for web, worker, and Redis
- Add an environment template for production secrets
- Add a deployment runbook for the first VPS rollout

## Out Of Scope

- Full production hardening
- Kubernetes or orchestration beyond Docker Compose
- PostgreSQL persistence wiring
- Automatic webhook provisioning

## Requirements

- Web and worker must run from the same built image
- Redis must be available in the deployment stack
- The web container must bind only to localhost on the VPS
- Deployment guidance must assume an external nginx container owns `80/443`
- The repo must expose an explicit worker runtime command

## Acceptance Criteria

- A Docker image can start the FastAPI app
- A container command can start the Redis worker loop
- `docker compose -f deploy/docker-compose.vps.yml config` is valid
- The deployment docs list required secrets and the first rollout sequence

