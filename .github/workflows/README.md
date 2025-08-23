# Deployment Workflows

This document describes the automated deployment system for the Cockpit API application, which follows a three-stage approach: **Checks** → **Build & Push** → **Deploy**.

## Overview

The deployment system is designed to:
- Ensure code quality through automated testing
- Build and publish Docker images to GitHub Container Registry (GHCR)
- Deploy to Raspberry Pi infrastructure using containerized applications
- Provide rollback capabilities and deployment visibility

## Workflow Structure

### 1. Checks Workflow (`checks.yml`)

**Triggers:**
- Pull requests to `master` branch
- Called by other workflows

**Responsibilities:**
- Sets up Python 3.12 environment
- Installs Poetry and project dependencies
- Runs the complete test suite using pytest
- Validates code quality before deployment

**Key Steps:**
```yaml
- Checkout repository
- Set up Python 3.12
- Install Poetry
- Install dependencies (including dev dependencies)
- Run pytest with verbose output
```

### 2. Deploy Workflow (`deploy.yml`)

**Triggers:**
- Push to `master` branch

**Responsibilities:**
- Runs checks workflow first
- Builds Docker image for `linux/arm64` (Raspberry Pi compatible)
- Pushes image to GitHub Container Registry with multiple tags
- Triggers production deployment

**Image Tagging Strategy:**
- `ghcr.io/marcinparda/cockpit-api:latest` - Latest version from master
- `ghcr.io/marcinparda/cockpit-api:sha-<commit-sha>` - Specific commit version
- `ghcr.io/marcinparda/cockpit-api:master` - Branch-based tag

**Key Features:**
- Multi-platform build support (optimized for ARM64)
- Docker layer caching for faster builds
- Automated metadata extraction
- Build summary generation

### 3. Deploy to Production Workflow (`deploy-to-production.yml`)

**Triggers:**
- Successful completion of Deploy workflow on `master` branch

**Responsibilities:**
- Connects to Raspberry Pi via Cloudflare Tunnel and SSH
- Executes deployment script on target server
- Provides deployment status feedback

**Security Features:**
- Uses Cloudflare Tunnel for secure SSH access
- Environment variables passed securely through GitHub Secrets
- SSH key-based authentication

## Deployment Script (`deploy.sh`)

The deployment script handles the actual application deployment on the Raspberry Pi:

### Key Functions:
1. **Environment Validation** - Checks all required environment variables
2. **GHCR Authentication** - Logs into GitHub Container Registry
3. **Configuration Management** - Creates `.env` file with production settings
4. **Container Orchestration** - Updates and restarts Docker containers
5. **Health Checks** - Verifies successful deployment

### Process Flow:
```bash
1. Validate environment variables
2. Create production .env file
3. Login to GHCR using GitHub token
4. Stop existing containers
5. Update docker-compose.prod.yml to use GHCR image
6. Pull latest image from registry
7. Start services with docker-compose
8. Perform health checks
9. Report deployment status
```

## Required GitHub Secrets

### SSH and Infrastructure:
- `RASPBERRY_PI_SSH_KEY` - Private SSH key for Pi access
- `SSH_KNOWN_HOSTS` - Known hosts for SSH security
- `CLOUDFLARE_TUNNEL_DOMAIN` - Cloudflare tunnel hostname
- `RASPBERRY_PI_USERNAME` - SSH username for Pi

### Database Configuration:
- `DB_USER` - PostgreSQL username
- `DB_PASSWORD` - PostgreSQL password  
- `DB_HOST` - Database host (internal Docker network name)
- `DB_NAME` - Database name
- `DB_PORT` - Database port

### Application Configuration:
- `CORS_ORIGINS` - Allowed CORS origins for API
- `JWT_SECRET_KEY` - Secret key for JWT token signing
- `JWT_ALGORITHM` - JWT signing algorithm
- `JWT_EXPIRE_HOURS` - Token expiration time
- `BCRYPT_ROUNDS` - Password hashing rounds
- `COOKIE_DOMAIN` - Domain for session cookies

### Registry Access:
- `GITHUB_TOKEN` - Automatically provided by GitHub Actions

## Manual Deployment

For manual deployments or troubleshooting:

### Building Image Locally:
```bash
docker build -t cockpit-api:local --target production .
```

### Manual Deployment to Pi:
```bash
# SSH to Raspberry Pi
ssh username@your-pi-hostname

# Navigate to project directory
cd ~/cockpit-api

# Pull latest code
git pull origin master

# Set environment variables and run deployment
export GITHUB_TOKEN="your-token"
export GITHUB_ACTOR="your-username"
# ... set other required variables ...
./deploy.sh
```

### Rollback Procedure:
```bash
# SSH to Pi
ssh username@your-pi-hostname
cd ~/cockpit-api

# Pull specific version
docker pull ghcr.io/marcinparda/cockpit-api:sha-<previous-commit>

# Update compose file to use specific tag
# Edit docker-compose.prod.yml to change image tag

# Restart services
docker compose -f docker-compose.prod.yml up -d
```

## Monitoring and Troubleshooting

### Health Check Endpoints:
- **API Health**: `http://localhost:8000/health`
- **Database**: Automatic health checks in docker-compose

### Common Issues:

1. **Image Pull Failures**: Verify GHCR authentication and network connectivity
2. **Container Start Failures**: Check environment variables and docker logs
3. **Database Connection Issues**: Verify database container health and credentials
4. **SSH Connection Problems**: Check Cloudflare tunnel status and SSH keys

### Viewing Logs:
```bash
# All service logs
docker compose -f docker-compose.prod.yml logs

# Specific service logs
docker compose -f docker-compose.prod.yml logs cockpit_api

# Real-time logs
docker compose -f docker-compose.prod.yml logs -f
```

## Architecture Decisions

### Why GHCR (GitHub Container Registry)?
- Integrated with GitHub ecosystem
- Free for public repositories
- Excellent integration with GitHub Actions
- Supports multi-architecture images

### Why Separate Workflows?
- **Separation of Concerns**: Build vs Deploy responsibilities
- **Reusability**: Checks can be used in PRs and deployments  
- **Visibility**: Clear deployment pipeline stages
- **Rollback**: Can redeploy without rebuilding

### Why Raspberry Pi?
- Cost-effective production hosting
- ARM64 architecture support
- Full container orchestration capabilities
- Suitable for personal/small-scale applications

## Migration from Legacy Workflows

The legacy `test-and-deploy.yml` workflow is now available only via manual trigger for emergency deployments. The new system provides:

- ✅ Better separation of concerns
- ✅ Container registry integration
- ✅ Improved deployment visibility
- ✅ Enhanced security through GHCR
- ✅ Easier rollback capabilities
- ✅ More maintainable deployment scripts

## Future Enhancements

Potential improvements to consider:
- **Blue/Green Deployments**: Zero-downtime deployments
- **Automated Rollback**: On health check failures
- **Multi-Environment**: Staging environment support  
- **Monitoring Integration**: Application performance monitoring
- **Database Migrations**: Automated Alembic migration runs