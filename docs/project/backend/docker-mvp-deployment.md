# Docker MVP Deployment

This runbook covers the first VPS deployment path for `flatscanner`.

## Target Shape

- `flatscanner-web` runs in Docker and listens on `127.0.0.1:8010`
- `flatscanner-worker` runs in Docker and consumes Redis jobs
- `flatscanner-redis` runs in Docker for the MVP queue
- the existing public nginx container keeps owning ports `80/443`
- nginx routes `flatscanner.godmodetools.com` to `flatscanner-web:8000` over a shared Docker network
- for first MVP trials, `web` and `worker` bind-mount `src/` so the live containers always use the current checkout on the VPS

## Files

- `Dockerfile`: shared image for web and worker
- `.env.example`: required runtime environment variables
- `deploy/docker-compose.vps.yml`: Docker-first stack for VPS rollout
- `deploy/nginx/flatscanner.godmodetools.com.conf.example`: nginx vhost example

## Required Secrets

- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_WEBHOOK_SECRET`
- `APIFY_API_TOKEN`
- `OPENROUTER_API_KEY`
- `OPENROUTER_MODEL`
- `GEOAPIFY_API_KEY`
- `FLATSCANNER_INGRESS_NETWORK` when the shared nginx network is not `app_app_network`

Optional:

- `APIFY_AIRBNB_ACTOR_ID` when overriding the default actor
- `DATABASE_URL` for future persistence wiring

## First Rollout Sequence

1. Copy `.env.example` to `.env` and fill in the secrets.
2. Start the stack with:
   `docker compose -f deploy/docker-compose.vps.yml up -d --build`
3. Verify health locally:
   `curl http://127.0.0.1:8010/health`
4. Attach `flatscanner-web` to the same Docker network as the public nginx container.
5. Add nginx routing for `flatscanner.godmodetools.com`.
6. Reload nginx.
7. Ensure the certificate covers `flatscanner.godmodetools.com`.
8. Set the Telegram webhook to the public HTTPS URL.
9. Send one live Airbnb link and verify:
   - webhook ingress
   - Redis enqueue
   - worker processing
   - Telegram response

## Notes

- This deployment path does not yet enable PostgreSQL-backed persistence.
- Redis is mandatory for MVP because job orchestration depends on it.
- The server already has an nginx container on `80/443`, so `flatscanner` must not bind those ports directly.
- On the current VPS, the shared ingress network is `app_app_network`.
- The default Airbnb actor is `curious_coder~airbnb-scraper` because it accepts listing detail URLs; actors that only support search-result URLs will fail for the Telegram MVP flow.
- If `flatscanner.godmodetools.com` is proxied through Cloudflare, webhook POST requests may be blocked by Cloudflare WAF/bot rules. For the first live MVP test, prefer DNS-only mode on that subdomain or add an explicit allow rule for Telegram webhook traffic.
