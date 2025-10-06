# DALS v1.0.0 Deployment Guide

This guide provides complete deployment instructions for the Digital Asset Logistics System (DALS) v1.0.0 with DALS-001 governance compliance and canonical stardate implementation.

## 🚀 Quick Deployment

### Prerequisites
- Python 3.8+
- Docker & Docker Desktop (for containerized deployment)
- Git

### Method 1: Direct Python Installation

```bash
# Clone the repository
git clone <repository-url>
cd dals

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# or
.venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Start the service
python -m iss_module.api.api
```

Access the service at `http://localhost:8003`

### Method 2: Docker Deployment

```bash
# Build the image
docker build -t dals-iss-module:v1.0.0 .

# Run the container
docker run -p 8003:8003 dals-iss-module:v1.0.0
```

### Method 3: Docker Compose (Recommended)

```bash
# Deploy full stack with monitoring
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs dals-iss
```

## 🛡️ Governance Verification

After deployment, verify DALS-001 compliance:

### API Endpoint Tests

```bash
# Test canonical stardate
curl http://localhost:8003/api/v1/iss/now

# Expected response:
{
  "stardate": 9410.0906,
  "iso_timestamp": "2025-10-05T...",
  "system_status": "operational",
  "governance": "DALS-001 compliant"
}

# Test module status (should return zeros when inactive)
curl http://localhost:8003/api/v1/caleon/status

# Expected response:
{
  "active": false,
  "cognitive_load": 0,
  "reasoning_patterns": 0,
  "status": "offline"
}
```

### Web Interface Verification

1. Visit `http://localhost:8003/docs` for interactive API documentation
2. Check for "🛡️ LIVE DATA ONLY" governance badge in UI
3. Verify no mock data in any responses

## 🔧 Configuration

### Environment Variables

Create `.env` file from `.env.example`:

```bash
# Service Configuration
ISS_SERVICE_NAME=dals-iss-module
ENVIRONMENT=production
ISS_HOST=0.0.0.0
ISS_PORT=8003

# Governance
DALS_001_ENABLED=true
MOCK_DATA_DISABLED=true

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json

# Feature Flags (Phase 1)
PHASE_1_TELEMETRY=true
WEBSOCKET_ENABLED=true
```

### Docker Configuration

Update `docker-compose.yml` for your environment:

```yaml
version: '3.8'
services:
  dals-iss:
    build: .
    ports:
      - "8003:8003"
    environment:
      - ENVIRONMENT=production
      - DALS_001_ENABLED=true
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8003/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

## 📊 Monitoring & Health Checks

### Health Check Endpoint

```bash
curl http://localhost:8003/health
```

### Service Status

```bash
curl http://localhost:8003/api/v1/status
```

### Docker Health Monitoring

```bash
# Check container health
docker ps --filter "name=dals"

# View container logs
docker logs <container-id>
```

## 🛠️ Troubleshooting

### Common Issues

1. **Port 8003 already in use**
   ```bash
   # Find process using port
   netstat -tulpn | grep 8003
   # Or change port in configuration
   ISS_PORT=8004 python -m iss_module.api.api
   ```

2. **Module import errors**
   ```bash
   # Ensure virtual environment is activated
   source .venv/bin/activate
   # Reinstall dependencies
   pip install -r requirements.txt
   ```

3. **Docker build failures**
   ```bash
   # Clean Docker cache
   docker system prune -a
   # Rebuild image
   docker build --no-cache -t dals-iss-module:v1.0.0 .
   ```

4. **Stardate calculation errors**
   ```bash
   # Test stardate function
   python -c "from iss_module.core.utils import get_stardate; print(get_stardate())"
   # Should return positive decimal (e.g., 9410.0906)
   ```

### Logs and Debugging

```bash
# Enable debug logging
LOG_LEVEL=DEBUG python -m iss_module.api.api

# Check log files
tail -f logs/captain_log.json

# Docker logs
docker-compose logs -f dals-iss
```

## 🔒 Security Considerations

### Production Deployment

1. **Environment Variables**: Use secure environment variable management
2. **Network Security**: Configure firewall rules for port 8003
3. **HTTPS**: Use reverse proxy (nginx/traefik) for SSL termination
4. **Authentication**: Implement authentication if required

### Docker Security

```yaml
# docker-compose.yml security additions
services:
  dals-iss:
    user: "1000:1000"  # Non-root user
    read_only: true
    tmpfs:
      - /tmp
    security_opt:
      - no-new-privileges:true
```

## 📈 Performance Tuning

### Docker Resources

```yaml
services:
  dals-iss:
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 512M
        reservations:
          cpus: '0.5'
          memory: 256M
```

### Application Settings

```bash
# Increase worker processes for high load
WORKERS=4 python -m iss_module.api.api

# Optimize logging for production
LOG_LEVEL=WARNING
```

## 🔄 Updates and Maintenance

### Version Updates

```bash
# Pull latest changes
git pull origin main

# Update dependencies
pip install -r requirements.txt

# Restart service
docker-compose restart dals-iss
```

### Database Maintenance

```bash
# Backup captain logs
cp logs/captain_log.json logs/captain_log.json.backup.$(date +%Y%m%d)

# Clean old logs (older than 30 days)
find logs/ -name "*.log" -mtime +30 -delete
```

## 📋 Deployment Checklist

- [ ] Repository cloned/downloaded
- [ ] Dependencies installed
- [ ] Environment variables configured
- [ ] Service starts successfully
- [ ] Health check endpoint responds
- [ ] Canonical stardate returns positive values
- [ ] DALS-001 governance verified (no mock data)
- [ ] API documentation accessible
- [ ] Docker containers healthy (if using Docker)
- [ ] Logs being written correctly
- [ ] Monitoring configured

## 🆘 Support

For deployment issues:

1. Check logs: `logs/captain_log.json`
2. Verify configuration: `.env` file
3. Test components individually:
   ```bash
   python -c "from iss_module.core.utils import get_stardate; print('Stardate OK')"
   python -c "from iss_module.api.api import app; print('API OK')"
   ```

## 📚 Additional Resources

- [Main Documentation](docs/README.md)
- [API Reference](docs/api/API_REFERENCE.md)
- [DALS-001 Governance](docs/governance/DALS-001-governance-enforcement.md)
- [Architecture Guide](docs/architecture/FOLDER_TREE.md)

---

**DALS v1.0.0** - Digital Asset Logistics System with DALS-001 Governance Compliance