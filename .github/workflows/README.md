# Deployment Workflows

Automated deployment pipeline: **Checks → Build & Push → Deploy to Pi**.

## Workflow Structure

### 1. `checks.yml`

**Triggers:** Pull requests to `master`, called by other workflows.

- Sets up Python 3.12 + Poetry
- Runs full pytest suite

### 2. `deploy.yml`

**Triggers:** Push to `master`.

- Runs checks first
- Builds Docker image for `linux/arm64` (Raspberry Pi)
- Pushes to GitHub Container Registry (GHCR) with tags:
  - `ghcr.io/marcinparda/cockpit-api:latest`
  - `ghcr.io/marcinparda/cockpit-api:master`
  - `ghcr.io/marcinparda/cockpit-api:sha-<commit>`
- Uses GHA layer cache for faster builds

### 3. `deploy-to-production.yml`

**Triggers:** Successful `deploy.yml` on `master`, or manual `workflow_dispatch`.

**Process:**

1. Install cloudflared via `AnimMouse/setup-cloudflared@v2`
2. Configure SSH to Pi through Cloudflare Tunnel
3. Write secrets to `/tmp/deploy.env` on Pi via SCP (never inline in commands)
4. Launch `deploy-api.sh` on Pi via `nohup` — detached from SSH connection
5. Poll `/tmp/deploy.exit` every 10s via short-lived SSH connections — avoids cloudflared idle timeout
6. On failure: fetch last 50 lines of `/tmp/deploy.log` for debugging

## Deployment Script (`deploy-api.sh`)

Runs on the Raspberry Pi. Uses `docker run` directly — no compose file.

**Process flow:**

```
1.  Validate all required environment variables
2.  Login to GHCR
3.  Tag cockpit_api:latest → cockpit_api:previous  (rollback safety)
4.  Pull ALL images (cockpit_api, hermes-agent, open-webui, actual-http-api)
    ↑ done BEFORE stopping containers to minimize downtime
5.  Stop and remove old containers
6.  Create network + volumes (idempotent)
7.  Start: cockpit_redis_prod, cockpit_db_prod (wait for ready)
8.  Start: cockpit_api_prod
9.  Start: hermes, actual-http-api
10. Connect cockpit_api_prod to vikunja_default network
11. Start: open-webui
12. Poll GET /health until ready (30 retries × 3s)
13. Verify all core containers are in running state
14. docker image prune (cleanup only after successful deploy)
```

**Running containers after deploy:**

| Container | Port | Image |
|---|---|---|
| `cockpit_api_prod` | 8000 | `ghcr.io/marcinparda/cockpit-api:latest` |
| `cockpit_db_prod` | — | `postgres:15-alpine` |
| `cockpit_redis_prod` | — | `redis/redis-stack-server:latest` |
| `hermes` | 8642 | `nousresearch/hermes-agent:latest` |
| `actual-http-api` | 5007 | `jhonderson/actual-http-api:latest` |
| `open-webui` | 4206 | `ghcr.io/open-webui/open-webui:main` |

## Required GitHub Secrets

### SSH / Infrastructure

| Secret | Description |
|---|---|
| `RASPBERRY_PI_SSH_KEY` | Private SSH key for Pi |
| `SSH_KNOWN_HOSTS` | Known hosts for SSH verification |
| `CLOUDFLARE_TUNNEL_DOMAIN` | Cloudflare tunnel hostname |
| `RASPBERRY_PI_USERNAME` | SSH username |

### Database

| Secret | Description |
|---|---|
| `DB_USER` | PostgreSQL username |
| `DB_PASSWORD` | PostgreSQL password |
| `DB_HOST` | Database host |
| `DB_NAME` | Database name |
| `DB_PORT` | Database port |

### Application

| Secret | Description |
|---|---|
| `CORS_ORIGINS` | Allowed CORS origins |
| `JWT_SECRET_KEY` | JWT signing key |
| `JWT_ALGORITHM` | JWT algorithm |
| `JWT_EXPIRE_HOURS` | Token expiry |
| `BCRYPT_ROUNDS` | Password hashing rounds |
| `COOKIE_DOMAIN` | Session cookie domain |
| `REDIS_PASSWORD` | Redis auth password |
| `OAUTH_SERVER_URL` | OAuth server base URL |

### External Services

| Secret | Description |
|---|---|
| `VIKUNJA_USERNAME` | Vikunja login |
| `VIKUNJA_PASSWORD` | Vikunja password |
| `ACTUAL_HTTP_API_KEY` | Actual Budget HTTP API key |
| `ACTUAL_BUDGET_SYNC_ID` | Actual Budget sync ID |
| `ACTUAL_SERVER_URL` | Actual Budget server URL |
| `ACTUAL_SERVER_PASSWORD` | Actual Budget server password |
| `OPEN_ROUTER_KEY` | OpenRouter API key |
| `SERPER_API_KEY` | Serper search API key |
| `BRAIN_NOTES_PATH` | Path to brain notes on Pi |
| `BRAIN_GIT_REMOTE` | Git remote for brain notes |
| `MCP_API_KEY` | MCP server auth key |
| `HERMES_API_KEY` | Hermes Agent API key |

`GITHUB_TOKEN` is provided automatically by GitHub Actions.

## Manual Deployment

SSH to Pi through cloudflared, set env vars, run the script:

```bash
# From local machine
cloudflared access ssh --hostname your-tunnel-domain

# On Pi — set required vars then run
export GITHUB_TOKEN="..." GITHUB_ACTOR="..." DB_USER="..." # etc.
cd ~
./deploy-api.sh
```

## Rollback

The deploy script tags the previous image before pulling. To roll back:

```bash
# SSH to Pi
docker rm -f cockpit_api_prod
docker run -d --name cockpit_api_prod \
  --network cockpit_network_prod \
  --restart always \
  -p 8000:8000 \
  # ... same env flags as in deploy-api.sh ...
  ghcr.io/marcinparda/cockpit-api:previous
```

Or pull a specific SHA tag:

```bash
docker pull ghcr.io/marcinparda/cockpit-api:sha-<commit>
```

## Monitoring and Troubleshooting

**Health endpoint:** `http://localhost:8000/health`

**View container logs:**

```bash
docker logs cockpit_api_prod
docker logs --tail=50 cockpit_api_prod
docker logs -f cockpit_api_prod          # follow
```

**Check deploy log (during/after CI run):**

```bash
cat /tmp/deploy.log
cat /tmp/deploy.exit   # exit code
```

**Common issues:**

| Issue | Check |
|---|---|
| SSH timeout in CI | Cloudflare tunnel status; polling loop handles transient drops |
| Image pull fails | `docker login ghcr.io` manually; verify `GITHUB_TOKEN` |
| API not healthy | `docker logs cockpit_api_prod`; check DB container is up |
| Container won't start | `docker ps -a`; inspect logs for the failed container |
