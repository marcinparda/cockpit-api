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
)

echo -e "${YELLOW}📋 Checking environment variables...${NC}"
for var in "${required_vars[@]}"; do
    if [[ -z "${!var}" ]]; then
        echo -e "${RED}❌ Error: Required environment variable $var is not set${NC}"
        exit 1
    fi
done
echo -e "${GREEN}✅ All environment variables are set${NC}"

# All environment variables are passed directly to containers - no .env file needed
echo -e "${YELLOW}📝 Environment variables will be passed directly to containers${NC}"

# Login to GitHub Container Registry
echo -e "${YELLOW}🔐 Logging into GitHub Container Registry...${NC}"
echo "${GITHUB_TOKEN}" | docker login ${REGISTRY} -u ${GITHUB_ACTOR} --password-stdin
echo -e "${GREEN}✅ Successfully logged in to GHCR${NC}"

# Stop existing containers by name (no compose file needed)
echo -e "${YELLOW}🛑 Stopping existing containers...${NC}"
docker stop cockpit_api_prod cockpit_redis_prod cockpit_db_prod 2>/dev/null || echo "No existing containers to stop"
docker rm cockpit_api_prod cockpit_redis_prod cockpit_db_prod 2>/dev/null || echo "No existing containers to remove"

# Remove old images to save space
echo -e "${YELLOW}🧹 Cleaning up old images...${NC}"
docker image prune -f || true

# Create Docker network if it doesn't exist
echo -e "${YELLOW}🌐 Creating Docker network...${NC}"
docker network create cockpit_network_prod 2>/dev/null || echo "Network already exists"

# Use existing volume with old production data
echo -e "${YELLOW}💾 Using existing production volumes...${NC}"
docker volume create cockpit-api_cockpit_postgres_data_prod 2>/dev/null || echo "Volume already exists"
docker volume create cockpit-api_cockpit_redis_data_prod 2>/dev/null || echo "Redis volume already exists"

# Pull the latest image
echo -e "${YELLOW}📥 Pulling latest image from GHCR...${NC}"
docker pull ${IMAGE_NAME}:latest
echo -e "${GREEN}✅ Latest image pulled${NC}"

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
  ${IMAGE_NAME}:latest

echo -e "${GREEN}✅ API container started${NC}"

# Wait a moment for services to start
echo -e "${YELLOW}⏳ Waiting for services to start...${NC}"
sleep 10

# Basic health check
echo -e "${YELLOW}🏥 Performing health check...${NC}"
if docker ps | grep -E "(cockpit_api_prod|cockpit_db_prod|cockpit_redis_prod)" | grep -q "Up"; then
    echo -e "${GREEN}✅ Health check passed - containers are running${NC}"
    
    # Try to connect to the API
    if curl -f http://localhost:8000/health >/dev/null 2>&1; then
        echo -e "${GREEN}✅ API health check passed${NC}"
    else
        echo -e "${YELLOW}⚠️  API health endpoint not responding yet (this is normal for initial startup)${NC}"
    fi
else
    echo -e "${RED}❌ Health check failed - containers may not be running properly${NC}"
    echo -e "${YELLOW}📋 Container status:${NC}"
    docker ps -a | grep -E "(cockpit_api_prod|cockpit_db_prod|cockpit_redis_prod)"
    echo -e "${YELLOW}📋 Recent API logs:${NC}"
    docker logs --tail=20 cockpit_api_prod 2>/dev/null || echo "No API logs available"
    echo -e "${YELLOW}📋 Recent DB logs:${NC}"
    docker logs --tail=20 cockpit_db_prod 2>/dev/null || echo "No DB logs available"
    echo -e "${YELLOW}📋 Recent Redis logs:${NC}"
    docker logs --tail=20 cockpit_redis_prod 2>/dev/null || echo "No Redis logs available"
    exit 1
fi

echo -e "${GREEN}🎉 Deployment completed successfully!${NC}"
echo -e "${GREEN}📍 Application is available at: http://localhost:8000${NC}"
echo -e "${GREEN}📍 Health check endpoint: http://localhost:8000/health${NC}"