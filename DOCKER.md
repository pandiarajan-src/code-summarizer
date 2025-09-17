# Docker Deployment Guide

This guide covers Docker deployment options for the Code Summarizer application, supporting both single-container and multi-container architectures.

## 🏗️ Architecture Overview

### Single Container Deployment
- **Ports**: Frontend (80) + API (8000) in one container
- **Technology**: Python + Nginx + Supervisor
- **Use Case**: Simple deployment, development, small-scale production

### Multi Container Deployment
- **API Container**: FastAPI service (port 8000)
- **Frontend Container**: Nginx static server (port 80)
- **Use Case**: Scalable production, microservices architecture

## 🚀 Quick Start

### Prerequisites
```bash
# Required
docker --version
docker-compose --version

# Create environment file
cp .env.example .env
# Edit .env with your OpenAI API key
```

### Single Container (Recommended for Development)
```bash
# Build and run
docker-compose -f docker-compose.single.yml up -d

# Access
# Frontend: http://localhost
# API: http://localhost:8000 (direct access)
```

### Multi Container (Recommended for Production)
```bash
# Build and run
docker-compose -f docker-compose.multi.yml up -d

# Access
# Frontend: http://localhost
# API: http://localhost:8000
```

## 📋 Environment Configuration

### Required Variables
```bash
# .env file
OPENAI_API_KEY=your_actual_api_key_here
```

### Optional Variables
```bash
# API Configuration
OPENAI_BASE_URL=https://api.openai.com/v1
MODEL_NAME=gpt-4o
DEBUG=false

# Docker Settings
CONTAINER_MODE=single  # or 'multi'
API_HOST=127.0.0.1     # or '0.0.0.0' for multi-container
API_PORT=8000
FRONTEND_PORT=80

# Performance
WORKERS=1
MAX_FILE_SIZE=50MB
REQUEST_TIMEOUT=300
```

## 🔧 Detailed Configuration

### Single Container Setup

#### docker-compose.single.yml
```yaml
services:
  code-summarizer:
    build: .
    ports:
      - "80:80"      # Frontend
      - "8000:8000"  # API (optional direct access)
    env_file: .env
```

#### Architecture
```
┌─────────────────────────────────────┐
│         Docker Container            │
│  ┌─────────────┐  ┌──────────────┐ │
│  │   Nginx     │  │   FastAPI    │ │
│  │   (Port 80) │  │  (Port 8000) │ │
│  │             │  │              │ │
│  │  Frontend   │←→│     API      │ │
│  │  + Proxy    │  │              │ │
│  └─────────────┘  └──────────────┘ │
│         ↑                          │
│    Supervisor                      │
└─────────────────────────────────────┘
```

### Multi Container Setup

#### docker-compose.multi.yml
```yaml
services:
  api:
    build:
      dockerfile: docker/api/Dockerfile
    ports: ["8000:8000"]

  frontend:
    build:
      dockerfile: docker/frontend/Dockerfile
    ports: ["80:80"]
    depends_on: [api]
```

#### Architecture
```
┌──────────────────┐    ┌──────────────────┐
│  Frontend        │    │      API         │
│  Container       │    │   Container      │
│                  │    │                  │
│  ┌─────────────┐ │    │ ┌──────────────┐ │
│  │   Nginx     │ │    │ │   FastAPI    │ │
│  │  (Port 80)  │ │    │ │ (Port 8000)  │ │
│  │             │ │    │ │              │ │
│  │  Frontend   │←┼────┼→│     API      │ │
│  └─────────────┘ │    │ └──────────────┘ │
└──────────────────┘    └──────────────────┘
```

## 🛠️ Management Commands

### Basic Operations
```bash
# Start services
docker-compose -f docker-compose.single.yml up -d

# View logs
docker-compose -f docker-compose.single.yml logs -f

# Stop services
docker-compose -f docker-compose.single.yml down

# Rebuild and restart
docker-compose -f docker-compose.single.yml up -d --build
```

### Health Checks
```bash
# Manual health check
docker exec <container_name> /app/docker/scripts/healthcheck.sh

# Check specific service
docker exec <container_name> /app/docker/scripts/healthcheck.sh api
docker exec <container_name> /app/docker/scripts/healthcheck.sh frontend

# View health status
docker-compose -f docker-compose.single.yml ps
```

### Troubleshooting
```bash
# Enter container
docker exec -it <container_name> /bin/bash

# View supervisor status (single container)
docker exec <container_name> supervisorctl status

# Restart specific service
docker exec <container_name> supervisorctl restart api
docker exec <container_name> supervisorctl restart nginx

# View application logs
docker exec <container_name> tail -f /var/log/supervisor/api.log
docker exec <container_name> tail -f /var/log/supervisor/nginx.log
```

## 🔒 Security Best Practices

### Production Configuration
```bash
# .env for production
DEBUG=false
CONTAINER_MODE=single
ALLOWED_HOSTS=your-domain.com
CORS_ORIGINS=https://your-domain.com

# Use secrets management
OPENAI_API_KEY_FILE=/run/secrets/openai_api_key
```

### Nginx Security Headers
The configuration includes:
- X-Frame-Options: SAMEORIGIN
- X-XSS-Protection: 1; mode=block
- X-Content-Type-Options: nosniff
- Content-Security-Policy: Restrictive CSP
- Rate limiting for API endpoints

### Container Security
- Non-root user execution
- Minimal base images
- Security scanning with `docker scan`
- Regular updates

## 📊 Performance Optimization

### Single Container Tuning
```bash
# Increase worker processes for production
WORKERS=4

# Optimize nginx
worker_processes auto;
worker_connections 1024;

# Enable gzip compression (already configured)
```

### Multi Container Scaling
```bash
# Scale API containers
docker-compose -f docker-compose.multi.yml up -d --scale api=3

# Use load balancer
# Add nginx load balancer or cloud load balancer
```

### Monitoring
```bash
# Resource usage
docker stats

# Container health
docker-compose -f docker-compose.single.yml ps

# Application metrics
curl http://localhost/health
curl http://localhost:8000/api/health
```

## 🚀 Production Deployment

### 1. Prepare Environment
```bash
# Create production environment
cp .env.example .env.production

# Update with production values
vim .env.production
```

### 2. Build Production Images
```bash
# Build optimized images
docker-compose -f docker-compose.single.yml build --no-cache

# Tag for registry
docker tag code-summarizer_code-summarizer:latest your-registry/code-summarizer:v1.0.0
```

### 3. Deploy with SSL (Recommended)
```yaml
# docker-compose.prod.yml
services:
  app:
    # ... existing config

  ssl-proxy:
    image: nginx:alpine
    ports:
      - "443:443"
      - "80:80"
    volumes:
      - ./ssl:/etc/nginx/ssl
      - ./nginx.ssl.conf:/etc/nginx/nginx.conf
```

### 4. Backup Strategy
```bash
# Backup logs
docker cp <container>:/var/log/supervisor ./backups/logs/

# Backup configuration
cp .env ./backups/config/
```

## 🧪 Development Workflow

### Local Development
```bash
# Development with live reload
docker-compose -f docker-compose.single.yml up -d

# Mount source code for live editing
# Add to docker-compose.yml:
volumes:
  - ./app:/app/app
  - ./frontend:/usr/share/nginx/html
```

### Testing
```bash
# Run tests in container
docker exec <container> uv run pytest

# API testing
docker exec <container> python test_api.py

# Load testing
hey -n 1000 -c 10 http://localhost/api/health
```

## 📚 Troubleshooting Guide

### Common Issues

#### 1. Container Won't Start
```bash
# Check logs
docker-compose logs

# Common causes:
# - Missing .env file
# - Invalid OPENAI_API_KEY
# - Port conflicts
```

#### 2. API Not Responding
```bash
# Check API health
curl http://localhost:8000/api/health

# Check supervisor status
docker exec <container> supervisorctl status api

# Restart API service
docker exec <container> supervisorctl restart api
```

#### 3. Frontend Not Loading
```bash
# Check nginx status
docker exec <container> supervisorctl status nginx

# Check nginx logs
docker exec <container> tail -f /var/log/nginx/error.log

# Verify frontend files
docker exec <container> ls -la /usr/share/nginx/html/
```

#### 4. Permission Issues
```bash
# Fix permissions
docker exec -u root <container> chown -R appuser:appuser /app
docker exec -u root <container> chown -R appuser:appuser /var/log/supervisor
```

#### 5. Memory Issues
```bash
# Monitor resource usage
docker stats

# Increase memory limits in docker-compose.yml:
deploy:
  resources:
    limits:
      memory: 2G
```

### Performance Issues
```bash
# Monitor container resources
docker stats

# Check API response times
curl -w "@curl-format.txt" -o /dev/null -s http://localhost:8000/api/health

# Optimize images
docker system prune -a
```

## 🔄 Switching Between Modes

### From Single to Multi Container
```bash
# Stop single container
docker-compose -f docker-compose.single.yml down

# Update .env
sed -i 's/CONTAINER_MODE=single/CONTAINER_MODE=multi/' .env
sed -i 's/API_HOST=127.0.0.1/API_HOST=0.0.0.0/' .env

# Start multi container
docker-compose -f docker-compose.multi.yml up -d
```

### From Multi to Single Container
```bash
# Stop multi container
docker-compose -f docker-compose.multi.yml down

# Update .env
sed -i 's/CONTAINER_MODE=multi/CONTAINER_MODE=single/' .env
sed -i 's/API_HOST=0.0.0.0/API_HOST=127.0.0.1/' .env

# Start single container
docker-compose -f docker-compose.single.yml up -d
```

## 📝 Maintenance

### Regular Tasks
```bash
# Update base images
docker-compose pull

# Clean up unused resources
docker system prune

# Backup important data
./scripts/backup.sh

# Update application
git pull
docker-compose up -d --build
```

### Log Rotation
```bash
# Configure log rotation in docker-compose.yml
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
```

This comprehensive Docker setup provides a robust, scalable, and secure deployment solution for the Code Summarizer application.