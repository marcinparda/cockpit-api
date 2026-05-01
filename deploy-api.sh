#!/bin/bash

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
REGISTRY="ghcr.io"
OWNER="marcinparda"
REPO="cockpit-api"
IMAGE_NAME="${REGISTRY}/${OWNER}/${REPO}"

echo -e "${GREEN}🚀 Starting Cockpit API deployment...${NC}"

# Check required environment variables
required_vars=(
    "GITHUB_TOKEN"
    "GITHUB_ACTOR"
    "DB_USER"
    "DB_PASSWORD"
    "DB_HOST"
    "DB_NAME"
    "DB_PORT"
    "CORS_ORIGINS"
    "JWT_SECRET_KEY"
    "JWT_ALGORITHM"
    "JWT_EXPIRE_HOURS"
    "BCRYPT_ROUNDS"
    "COOKIE_DOMAIN"
    "REDIS_PASSWORD"
    "VIKUNJA_USERNAME"
    "VIKUNJA_PASSWORD"
    "ACTUAL_HTTP_API_KEY"
    "ACTUAL_BUDGET_SYNC_ID"
    "ACTUAL_SERVER_URL"
    "ACTUAL_SERVER_PASSWORD"
    "OPEN_ROUTER_KEY"
    "SERPER_API_KEY"
    "BRAIN_NOTES_PATH"
    "MCP_API_KEY"
    "HERMES_API_KEY"
    "OAUTH_SERVER_URL"
)

echo -e "${YELLOW}📋 Checking environment variables...${NC}"
for var in "${required_vars[@]}"; do
    if [[ -z "${!var}" ]]; then
        echo -e "${RED}❌ Error: Required environment variable $var is not set${NC}"
        exit 1
    fi
done
echo -e "${GREEN}✅ All environment variables are set${NC}"

# Login to GitHub Container Registry
echo -e "${YELLOW}🔐 Logging into GitHub Container Registry...${NC}"
echo "${GITHUB_TOKEN}" | docker login ${REGISTRY} -u ${GITHUB_ACTOR} --password-stdin
echo -e "${GREEN}✅ Successfully logged in to GHCR${NC}"

# Tag current image as :previous before pulling new one (rollback safety)
echo -e "${YELLOW}🏷️  Tagging current image as :previous...${NC}"
docker tag ${IMAGE_NAME}:latest ${IMAGE_NAME}:previous 2>/dev/null \
    && echo -e "${GREEN}✅ Previous image tagged for rollback${NC}" \
    || echo -e "${YELLOW}⚠️  No existing image to tag (first deploy)${NC}"

# Pull ALL images BEFORE stopping any containers to minimize downtime
echo -e "${YELLOW}📥 Pulling all images (containers still running)...${NC}"
docker pull ${IMAGE_NAME}:latest
docker pull nousresearch/hermes-agent:latest
docker pull ghcr.io/open-webui/open-webui:main
docker pull jhonderson/actual-http-api:latest
echo -e "${GREEN}✅ All images pulled${NC}"

# Stop existing containers
echo -e "${YELLOW}🛑 Stopping existing containers...${NC}"
for container in cockpit_api_prod cockpit_redis_prod cockpit_db_prod hermes actual-http-api open-webui; do
    docker rm -f "$container" 2>/dev/null || true
done

# Create Docker network if it doesn't exist
echo -e "${YELLOW}🌐 Creating Docker network...${NC}"
docker network create cockpit_network_prod 2>/dev/null || echo "Network already exists"

# Ensure volumes exist
echo -e "${YELLOW}💾 Ensuring production volumes exist...${NC}"
docker volume create cockpit-api_cockpit_postgres_data_prod 2>/dev/null || echo "Volume already exists"
docker volume create cockpit-api_cockpit_redis_data_prod 2>/dev/null || echo "Redis volume already exists"

# Start Redis container
echo -e "${YELLOW}🗄️ Starting Redis container...${NC}"
docker run -d \
  --name cockpit_redis_prod \
  --network cockpit_network_prod \
  --restart always \
  -v cockpit-api_cockpit_redis_data_prod:/var/lib/redis-stack \
  redis/redis-stack-server:latest \
  redis-stack-server --appendonly yes --requirepass "${REDIS_PASSWORD}"
echo -e "${GREEN}✅ Redis container started${NC}"

# Start PostgreSQL container
echo -e "${YELLOW}🗄️ Starting PostgreSQL container...${NC}"
docker run -d \
  --name cockpit_db_prod \
  --network cockpit_network_prod \
  --restart always \
  -e POSTGRES_USER="${DB_USER}" \
  -e POSTGRES_PASSWORD="${DB_PASSWORD}" \
  -e POSTGRES_DB="${DB_NAME}" \
  -v cockpit-api_cockpit_postgres_data_prod:/var/lib/postgresql/data \
  --health-cmd="pg_isready -U ${DB_USER} -d ${DB_NAME}" \
  --health-interval=10s \
  --health-timeout=5s \
  --health-retries=5 \
  postgres:15-alpine
echo -e "${GREEN}✅ PostgreSQL container started${NC}"

# Wait for database to be ready
echo -e "${YELLOW}⏳ Waiting for database to be ready...${NC}"
while ! docker exec cockpit_db_prod pg_isready -U "${DB_USER}" -d "${DB_NAME}" >/dev/null 2>&1; do
  echo -e "${YELLOW}⏳ Database not ready yet, waiting...${NC}"
  sleep 2
done
echo -e "${GREEN}✅ Database is ready${NC}"

# Start API container
echo -e "${YELLOW}🚀 Starting API container...${NC}"
docker run -d \
  --name cockpit_api_prod \
  --network cockpit_network_prod \
  --restart always \
  -p 8000:8000 \
  -e DB_USER="${DB_USER}" \
  -e DB_PASSWORD="${DB_PASSWORD}" \
  -e DB_HOST="cockpit_db_prod" \
  -e DB_NAME="${DB_NAME}" \
  -e DB_PORT="${DB_PORT}" \
  -e CORS_ORIGINS="${CORS_ORIGINS}" \
  -e JWT_SECRET_KEY="${JWT_SECRET_KEY}" \
  -e JWT_ALGORITHM="${JWT_ALGORITHM}" \
  -e JWT_EXPIRE_HOURS="${JWT_EXPIRE_HOURS}" \
  -e BCRYPT_ROUNDS="${BCRYPT_ROUNDS}" \
  -e COOKIE_DOMAIN="${COOKIE_DOMAIN}" \
  -e COOKIE_SECURE=True \
  -e ENVIRONMENT=production \
  -e REDIS_STORE_URL="redis://:${REDIS_PASSWORD}@cockpit_redis_prod:6379" \
  -e VIKUNJA_BASE_URL="http://vikunja:3456/api/v1" \
  -e VIKUNJA_USERNAME="${VIKUNJA_USERNAME}" \
  -e VIKUNJA_PASSWORD="${VIKUNJA_PASSWORD}" \
  -e ACTUAL_HTTP_API_URL="http://actual-http-api:5007" \
  -e ACTUAL_HTTP_API_KEY="${ACTUAL_HTTP_API_KEY}" \
  -e ACTUAL_BUDGET_SYNC_ID="${ACTUAL_BUDGET_SYNC_ID}" \
  -e OPEN_ROUTER_KEY="${OPEN_ROUTER_KEY}" \
  -e SERPER_API_KEY="${SERPER_API_KEY}" \
  -e BRAIN_NOTES_PATH="${BRAIN_NOTES_PATH}" \
  -e BRAIN_GIT_REMOTE="${BRAIN_GIT_REMOTE}" \
  -e MCP_API_KEY="${MCP_API_KEY}" \
  -e OAUTH_SERVER_URL="${OAUTH_SERVER_URL}" \
  -e HERMES_CONFIG_PATH="/opt/hermes/cli-config.yaml" \
  -v "${BRAIN_NOTES_PATH}:${BRAIN_NOTES_PATH}" \
  -v "${HOME}/.hermes:/opt/hermes" \
  -v /var/run/docker.sock:/var/run/docker.sock \
  ${IMAGE_NAME}:latest
echo -e "${GREEN}✅ API container started${NC}"

# Deploy Hermes Agent
echo -e "${YELLOW}🤖 Deploying Hermes Agent...${NC}"
mkdir -p "${HOME}/.hermes"
cat > "${HOME}/.hermes/config.yaml" << EOF
model:
  default: "${HERMES_MODEL:-openai/gpt-5-mini}"
  provider: "auto"
  base_url: "https://openrouter.ai/api/v1"
EOF

cat > "${HOME}/.hermes/cli-config.yaml" << EOF
mcp_servers:
  cockpit:
    url: http://cockpit_api_prod:8000/mcp
    headers:
      Authorization: "Bearer ${MCP_API_KEY}"
EOF
docker run -d \
  --name hermes \
  --network cockpit_network_prod \
  --restart always \
  -p 8642:8642 \
  -v "${HOME}/.hermes:/opt/data" \
  -e HERMES_UID=$(id -u) \
  -e HERMES_GID=$(id -g) \
  -e API_SERVER_HOST=0.0.0.0 \
  -e API_SERVER_PORT=8642 \
  -e API_SERVER_KEY="${HERMES_API_KEY}" \
  -e OPENROUTER_API_KEY="${OPEN_ROUTER_KEY}" \
  nousresearch/hermes-agent:latest \
  gateway run
echo -e "${GREEN}✅ Hermes Agent deployed on port 8642${NC}"

# Deploy actual-http-api
echo -e "${YELLOW}🔄 Deploying actual-http-api...${NC}"
docker network create actual_network 2>/dev/null || true
docker network connect actual_network actual 2>/dev/null || true
docker volume create actual_http_api_data 2>/dev/null || true
docker run -d \
  --name actual-http-api \
  --network actual_network \
  --restart always \
  -p 5007:5007 \
  -v actual_http_api_data:/data \
  -e ACTUAL_SERVER_URL="${ACTUAL_SERVER_URL}" \
  -e ACTUAL_SERVER_PASSWORD="${ACTUAL_SERVER_PASSWORD}" \
  -e API_KEY="${ACTUAL_HTTP_API_KEY}" \
  -e ACTUAL_DATA_DIR=/data \
  jhonderson/actual-http-api:latest
echo -e "${GREEN}✅ actual-http-api deployed${NC}"

# Connect to external service networks so container hostnames resolve
echo -e "${YELLOW}🔗 Connecting to external networks...${NC}"
docker network connect vikunja_default cockpit_api_prod
docker network connect cockpit_network_prod actual-http-api 2>/dev/null || true
echo -e "${GREEN}✅ Connected to external networks${NC}"

# Deploy Open WebUI
echo -e "${YELLOW}🤖 Deploying Open WebUI...${NC}"
docker volume create open_webui_data 2>/dev/null || echo "Volume already exists"
docker run -d \
  --name open-webui \
  --network cockpit_network_prod \
  --restart always \
  -p 4206:8080 \
  -v open_webui_data:/app/backend/data \
  -e OPENAI_API_BASE_URLS="https://openrouter.ai/api/v1;http://hermes:8642/v1" \
  -e OPENAI_API_KEYS="${OPEN_ROUTER_KEY};${HERMES_API_KEY}" \
  -e ENABLE_SIGNUP=true \
  ghcr.io/open-webui/open-webui:main
echo -e "${GREEN}✅ Open WebUI deployed on port 4206${NC}"

# Wait for API to be ready (real readiness check)
echo -e "${YELLOW}🏥 Waiting for API to be ready...${NC}"
for i in $(seq 1 30); do
    if curl -sf http://localhost:8000/health >/dev/null 2>&1; then
        echo -e "${GREEN}✅ API health check passed (attempt $i)${NC}"
        break
    fi
    if [ "$i" -eq 30 ]; then
        echo -e "${RED}❌ API failed to become healthy after 90 seconds${NC}"
        echo -e "${YELLOW}📋 Recent API logs:${NC}"
        docker logs --tail=30 cockpit_api_prod 2>/dev/null || true
        exit 1
    fi
    echo -e "${YELLOW}⏳ Waiting for API... attempt $i/30${NC}"
    sleep 3
done

# Verify core containers are running
echo -e "${YELLOW}🔍 Verifying all core containers are up...${NC}"
failed=0
for container in cockpit_api_prod cockpit_db_prod cockpit_redis_prod; do
    if docker ps --filter "name=${container}" --filter "status=running" | grep -q "${container}"; then
        echo -e "${GREEN}✅ ${container} is running${NC}"
    else
        echo -e "${RED}❌ ${container} is not running${NC}"
        docker logs --tail=20 "${container}" 2>/dev/null || true
        failed=1
    fi
done
[ "$failed" -eq 1 ] && exit 1

# Clean up old images now that deploy succeeded
echo -e "${YELLOW}🧹 Cleaning up old images...${NC}"
docker image prune -f || true

echo -e "${GREEN}🎉 Deployment completed successfully!${NC}"
echo -e "${GREEN}📍 API available at: http://localhost:8000${NC}"
echo -e "${GREEN}📍 Health check: http://localhost:8000/health${NC}"
