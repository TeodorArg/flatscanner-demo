# Tasks: Docker MVP Deployment Prep

## Implementation

- [x] Add a shared Docker image for the application
- [x] Add a container-friendly worker entrypoint
- [x] Add a Docker Compose stack for web, worker, and Redis
- [x] Add a production `.env` template
- [x] Add a deployment runbook for the first VPS rollout

## Validation

- [x] Validate the Compose configuration
- [x] Validate the Python test suite
- [x] Record any remaining VPS-specific prerequisites before live rollout

## VPS Prerequisites

- [x] Confirm the existing ingress Docker network name on the target VPS (`app_app_network`)
- [x] Confirm ports `80/443` are already owned by the existing nginx container
- [x] Confirm `flatscanner.godmodetools.com` DNS is not created yet
- [x] Confirm the current TLS certificate does not yet cover `flatscanner.godmodetools.com`
- [x] Validate that the Docker image builds successfully on the target ARM VPS
