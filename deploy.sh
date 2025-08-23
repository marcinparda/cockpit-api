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
COMPOSE_FILE="docker-compose.prod.yml"

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
)

echo -e "${YELLOW}📋 Checking environment variables...${NC}"
for var in "${required_vars[@]}"; do
    if [[ -z "${!var}" ]]; then
        echo -e "${RED}❌ Error: Required environment variable $var is not set${NC}"
        exit 1
    fi
done
echo -e "${GREEN}✅ All environment variables are set${NC}"

# Create .env file with all required variables
echo -e "${YELLOW}📝 Creating .env file...${NC}"
cat > .env << EOF
DB_USER='${DB_USER}'
DB_PASSWORD='${DB_PASSWORD}'
DB_HOST='${DB_HOST}'
DB_NAME='${DB_NAME}'
DB_PORT='${DB_PORT}'
CORS_ORIGINS='${CORS_ORIGINS}'
JWT_SECRET_KEY='${JWT_SECRET_KEY}'
JWT_ALGORITHM='${JWT_ALGORITHM}'
JWT_EXPIRE_HOURS='${JWT_EXPIRE_HOURS}'
BCRYPT_ROUNDS='${BCRYPT_ROUNDS}'
COOKIE_DOMAIN='${COOKIE_DOMAIN}'
COOKIE_SECURE=True
ENVIRONMENT=production
EOF
echo -e "${GREEN}✅ .env file created${NC}"

# Login to GitHub Container Registry
echo -e "${YELLOW}🔐 Logging into GitHub Container Registry...${NC}"
echo "${GITHUB_TOKEN}" | docker login ${REGISTRY} -u ${GITHUB_ACTOR} --password-stdin
echo -e "${GREEN}✅ Successfully logged in to GHCR${NC}"

# Stop existing containers
echo -e "${YELLOW}🛑 Stopping existing containers...${NC}"
docker compose -f ${COMPOSE_FILE} down || true
echo -e "${GREEN}✅ Containers stopped${NC}"

# Remove old images to save space
echo -e "${YELLOW}🧹 Cleaning up old images...${NC}"
docker image prune -f || true

# Create updated docker-compose.prod.yml that uses GHCR image
echo -e "${YELLOW}📝 Updating Docker Compose configuration for GHCR...${NC}"
cp ${COMPOSE_FILE} ${COMPOSE_FILE}.backup

# Update the compose file to use the GHCR image instead of building locally
cat > ${COMPOSE_FILE} << 'EOF'
services:
  cockpit_db:
    image: postgres:15-alpine
    container_name: cockpit_db_prod
    env_file:
      - .env
    environment:
      - POSTGRES_USER=${DB_USER}
      - POSTGRES_PASSWORD=${DB_PASSWORD}
      - POSTGRES_DB=${DB_NAME}
    volumes:
      - cockpit_postgres_data_prod:/var/lib/postgresql/data
    networks:
      - cockpit_network_prod
    restart: always
    healthcheck:
      test: ['CMD-SHELL', 'pg_isready -U ${DB_USER} -d ${DB_NAME}']
      interval: 10s
      timeout: 5s
      retries: 5

  cockpit_api:
    image: ghcr.io/marcinparda/cockpit-api:latest
    container_name: cockpit_api_prod
    env_file:
      - .env
    environment:
      - DB_HOST=cockpit_db
    ports:
      - '8000:8000'
    depends_on:
      cockpit_db:
        condition: service_healthy
    networks:
      - cockpit_network_prod
    restart: always

networks:
  cockpit_network_prod:
    driver: bridge

volumes:
  cockpit_postgres_data_prod:
EOF

echo -e "${GREEN}✅ Docker Compose configuration updated${NC}"

# Pull the latest image
echo -e "${YELLOW}📥 Pulling latest image from GHCR...${NC}"
docker pull ${IMAGE_NAME}:latest
echo -e "${GREEN}✅ Latest image pulled${NC}"

# Start the services
echo -e "${YELLOW}🚀 Starting services...${NC}"
docker compose -f ${COMPOSE_FILE} up -d
echo -e "${GREEN}✅ Services started${NC}"

# Wait a moment for services to start
echo -e "${YELLOW}⏳ Waiting for services to start...${NC}"
sleep 10

# Basic health check
echo -e "${YELLOW}🏥 Performing health check...${NC}"
if docker compose -f ${COMPOSE_FILE} ps | grep -q "Up"; then
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
    docker compose -f ${COMPOSE_FILE} ps
    echo -e "${YELLOW}📋 Recent logs:${NC}"
    docker compose -f ${COMPOSE_FILE} logs --tail=20
    exit 1
fi

echo -e "${GREEN}🎉 Deployment completed successfully!${NC}"
echo -e "${GREEN}📍 Application is available at: http://localhost:8000${NC}"
echo -e "${GREEN}📍 Health check endpoint: http://localhost:8000/health${NC}"