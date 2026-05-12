# Production Deployment Checklist

## Pre-Deployment

### Code Quality
- [ ] All modules have type hints (100% coverage)
- [ ] All public functions have docstrings
- [ ] No hardcoded secrets or API keys
- [ ] All imports are organized and clean
- [ ] No unused imports or variables
- [ ] Code follows PEP 8 standards

### Testing
- [ ] Unit tests written for all modules
- [ ] Integration tests pass
- [ ] Error handling tested
- [ ] Streaming endpoints tested
- [ ] Tool execution tested
- [ ] Load testing completed

### Documentation
- [ ] README.md updated for production
- [ ] API documentation complete
- [ ] Architecture documented
- [ ] Deployment guide written
- [ ] Troubleshooting guide included

### Security
- [ ] No secrets in environment files
- [ ] CORS configured appropriately
- [ ] Input validation in place
- [ ] Error messages don't leak info
- [ ] Logging doesn't contain secrets
- [ ] API keys rotated
- [ ] SSL/TLS enabled (for HTTPS)

### Performance
- [ ] Load tested with expected traffic
- [ ] Memory usage acceptable
- [ ] Response times acceptable
- [ ] Database queries optimized
- [ ] Caching implemented where needed

## Deployment

### Infrastructure
- [ ] Server provisioned and configured
- [ ] Database setup (if using PostgreSQL)
- [ ] Redis setup (if using for caching)
- [ ] SSL certificate installed
- [ ] Firewall rules configured
- [ ] Backup strategy implemented

### Configuration
- [ ] Production `.env` file created
- [ ] Database connection string set
- [ ] API keys securely stored
- [ ] Logging level appropriate (INFO/WARNING)
- [ ] Debug mode disabled
- [ ] CORS origins restricted

### Docker/Containerization
- [ ] Dockerfile builds successfully
- [ ] Docker image tested locally
- [ ] Docker image pushed to registry
- [ ] docker-compose.yml updated for production
- [ ] Health checks configured
- [ ] Resource limits set

### Monitoring & Logging
- [ ] Centralized logging configured
- [ ] Error tracking setup (Sentry, etc.)
- [ ] Metrics collection setup (Prometheus, etc.)
- [ ] Alerts configured
- [ ] Log rotation configured
- [ ] Performance monitoring enabled

### Database (if applicable)
- [ ] PostgreSQL configured for production
- [ ] Backups automated
- [ ] Connection pooling enabled
- [ ] Migrations tested
- [ ] Indexes optimized
- [ ] Query performance tested

### API Gateway/Load Balancer
- [ ] Nginx/HAProxy configured
- [ ] SSL/TLS termination set up
- [ ] Load balancing rules configured
- [ ] Rate limiting enabled
- [ ] Request/response logging enabled

## Post-Deployment

### Verification
- [ ] API endpoints responding correctly
- [ ] Streaming working without issues
- [ ] Tool execution working
- [ ] Error handling working
- [ ] Logging working
- [ ] Monitoring dashboards populated

### Performance
- [ ] Response times acceptable
- [ ] Memory usage stable
- [ ] CPU usage acceptable
- [ ] Database performance good
- [ ] No memory leaks

### Security
- [ ] No unauthorized access
- [ ] SSL/TLS working
- [ ] CORS working correctly
- [ ] API keys secure
- [ ] No logs exposed

### Backup & Recovery
- [ ] Backups verified
- [ ] Disaster recovery tested
- [ ] Rollback procedure documented
- [ ] Emergency contacts documented

## Ongoing Maintenance

### Regular Tasks
- [ ] Review logs daily
- [ ] Monitor error rates
- [ ] Check performance metrics
- [ ] Review security logs
- [ ] Test backups weekly

### Weekly
- [ ] Update dependencies (security patches)
- [ ] Review performance reports
- [ ] Check disk space
- [ ] Review API usage

### Monthly
- [ ] Full backup verification
- [ ] Security audit
- [ ] Performance optimization review
- [ ] Documentation update

### Quarterly
- [ ] Full security audit
- [ ] Disaster recovery drill
- [ ] Performance benchmarking
- [ ] Capacity planning

## Configuration Checklist

### Environment Variables

```env
# Required
GROQ_API_KEY=production-key-here
LLM_MODEL=meta-llama/llama-4-scout-17b-16e-instruct
LLM_PROVIDER=groq

# Security
HOST=127.0.0.1  # Don't expose to 0.0.0.0
PORT=8000
DEBUG=False
LOG_LEVEL=INFO

# CORS
CORS_ORIGINS=["https://yourdomain.com"]
CORS_METHODS=["GET", "POST", "OPTIONS"]
CORS_HEADERS=["*"]

# Optional
TAVILY_MAX_RESULTS=4

# Database (if using PostgreSQL)
DATABASE_URL=postgresql://user:password@host:5432/dbname

# Redis (if caching)
REDIS_URL=redis://host:6379/0
```

### Docker Compose (Production)

```yaml
version: '3.8'

services:
  backend:
    image: perplexity-backend:v1.0
    ports:
      - "8000:8000"
    environment:
      GROQ_API_KEY: ${GROQ_API_KEY}
      DEBUG: "False"
      LOG_LEVEL: "INFO"
      CORS_ORIGINS: '["https://yourdomain.com"]'
    restart: always
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

## Monitoring Queries

### Check API Health

```bash
curl -v http://your-domain/api/health
```

Expected response:
```json
{"status": "ok", "service": "perplexity-2.0-backend"}
```

### Test Streaming

```bash
curl -N "http://your-domain/api/chat_stream/test%20query"
```

Should see SSE events streaming.

### Check Logs

```bash
# Docker
docker logs container-name

# Docker Compose
docker-compose logs -f backend

# Systemd
journalctl -u perplexity-backend -f
```

## Troubleshooting

### Issue: API not responding
1. Check service status: `systemctl status perplexity-backend`
2. Check logs: `journalctl -u perplexity-backend -n 50`
3. Verify network: `curl http://localhost:8000/api/health`
4. Check firewall: `sudo ufw status`

### Issue: Tool execution fails
1. Verify API key: `echo $GROQ_API_KEY`
2. Check network connectivity
3. Test manually with Groq API
4. Review error logs

### Issue: Performance degradation
1. Check CPU usage: `top`
2. Check memory: `free -h`
3. Check disk: `df -h`
4. Review database query times
5. Scale horizontally if needed

### Issue: High memory usage
1. Check for memory leaks: `ps aux | grep python`
2. Review logs for errors
3. Consider restarting service
4. Optimize database queries
5. Add caching if applicable

## Rollback Procedure

If deployment fails:

```bash
# Check current version
docker ps

# Stop current container
docker-compose down

# Rollback to previous image
docker pull perplexity-backend:v1.0-stable
docker tag perplexity-backend:v1.0-stable perplexity-backend:latest

# Start previous version
docker-compose up -d

# Verify
curl http://localhost:8000/api/health
```

## Documentation References

- [README_ARCHITECTURE.md](README_ARCHITECTURE.md) - Full architecture
- [QUICKSTART.md](QUICKSTART.md) - Quick start guide
- [REFACTORING_SUMMARY.md](REFACTORING_SUMMARY.md) - What changed
- [STREAMING_EVENTS.md](STREAMING_EVENTS.md) - Event documentation

## Contacts & Escalation

- **Backend Team**: [contact info]
- **DevOps Team**: [contact info]
- **On-Call Support**: [contact info]
- **Escalation**: [process]

## Sign-Off

- [ ] Code reviewed and approved by: _____________
- [ ] Infrastructure approved by: _____________
- [ ] Security approved by: _____________
- [ ] Performance approved by: _____________
- [ ] Deployment approved by: _____________

**Deployment Date**: _____________  
**Deployed By**: _____________  
**Approved By**: _____________  

---

Good luck with production deployment! 🚀
