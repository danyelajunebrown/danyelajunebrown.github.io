# Server Deployment Guide

## Overview

This server receives and stores pseudonymized research data from the browser extension. It's a Node.js/Express API with PostgreSQL database.

---

## Prerequisites

- **Node.js** 16+ and npm 8+
- **PostgreSQL** 13+
- **Linux server** (Ubuntu 20.04+ recommended) or equivalent
- **Domain name** with SSL certificate
- **Minimum 2GB RAM**, 20GB storage

---

## Initial Setup

### 1. Clone Repository

```bash
cd /opt
git clone https://github.com/bard-college/gaze-detection-extension.git
cd gaze-detection-extension/server
```

### 2. Install Dependencies

```bash
npm install
```

### 3. Setup PostgreSQL Database

```bash
# Install PostgreSQL
sudo apt update
sudo apt install postgresql postgresql-contrib

# Create database and user
sudo -u postgres psql

# In PostgreSQL shell:
CREATE DATABASE gaze_study;
CREATE USER gaze_admin WITH ENCRYPTED PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE gaze_study TO gaze_admin;
\q

# Load schema
psql -U gaze_admin -d gaze_study -f schema.sql
```

### 4. Configure Environment

```bash
# Copy template
cp .env.example .env

# Edit with your values
nano .env
```

**Required changes:**
- `DB_PASSWORD`: Your PostgreSQL password
- `API_KEY`: Generate with `openssl rand -hex 32`
- `WITHDRAWAL_SECRET`: Generate with `openssl rand -hex 32`
- `ALLOWED_ORIGINS`: Your extension ID (get after publishing to Chrome Web Store)

### 5. Test Server

```bash
# Run in development mode
npm run dev

# Test health endpoint
curl http://localhost:3000/health
```

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "2025-01-15T10:30:00.000Z",
  "database": "connected"
}
```

---

## Production Deployment

### Option 1: Systemd Service (Recommended)

Create service file:

```bash
sudo nano /etc/systemd/system/gaze-study-api.service
```

Content:

```ini
[Unit]
Description=Gaze Study API Server
After=network.target postgresql.service

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/gaze-detection-extension/server
Environment=NODE_ENV=production
EnvironmentFile=/opt/gaze-detection-extension/server/.env
ExecStart=/usr/bin/node server.js
Restart=always
RestartSec=10
StandardOutput=syslog
StandardError=syslog
SyslogIdentifier=gaze-study-api

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable gaze-study-api
sudo systemctl start gaze-study-api

# Check status
sudo systemctl status gaze-study-api

# View logs
sudo journalctl -u gaze-study-api -f
```

### Option 2: PM2 Process Manager

```bash
# Install PM2
sudo npm install -g pm2

# Start server
pm2 start server.js --name gaze-study-api

# Save configuration
pm2 save

# Setup startup script
pm2 startup
```

### Option 3: Docker

```bash
# Build image
docker build -t gaze-study-api .

# Run container
docker run -d \
  --name gaze-study-api \
  --env-file .env \
  -p 3000:3000 \
  --restart unless-stopped \
  gaze-study-api

# View logs
docker logs -f gaze-study-api
```

---

## Nginx Reverse Proxy Setup

### 1. Install Nginx

```bash
sudo apt install nginx
```

### 2. Configure Nginx

```bash
sudo nano /etc/nginx/sites-available/gaze-study-api
```

Content:

```nginx
server {
    listen 80;
    server_name api.gaze-study.bard.edu;

    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.gaze-study.bard.edu;

    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/api.gaze-study.bard.edu/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.gaze-study.bard.edu/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Security headers
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;
    limit_req zone=api_limit burst=20 nodelay;

    # Proxy to Node.js
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Health check endpoint (no rate limit)
    location /health {
        proxy_pass http://localhost:3000/health;
        access_log off;
    }

    # Logging
    access_log /var/log/nginx/gaze-study-api-access.log;
    error_log /var/log/nginx/gaze-study-api-error.log;
}
```

Enable site:

```bash
sudo ln -s /etc/nginx/sites-available/gaze-study-api /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 3. Setup SSL with Let's Encrypt

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d api.gaze-study.bard.edu
```

---

## Database Maintenance

### Backup

**Automated daily backups:**

```bash
sudo nano /usr/local/bin/backup-gaze-db.sh
```

Content:

```bash
#!/bin/bash
BACKUP_DIR="/var/backups/gaze-study"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR

pg_dump -U gaze_admin gaze_study | gzip > $BACKUP_DIR/gaze_study_$DATE.sql.gz

# Keep only last 30 days
find $BACKUP_DIR -name "gaze_study_*.sql.gz" -mtime +30 -delete
```

Make executable and add to cron:

```bash
sudo chmod +x /usr/local/bin/backup-gaze-db.sh

# Add to crontab (daily at 2 AM)
sudo crontab -e
# Add line:
0 2 * * * /usr/local/bin/backup-gaze-db.sh
```

### Restore

```bash
gunzip < /var/backups/gaze-study/gaze_study_20250115_020000.sql.gz | \
  psql -U gaze_admin gaze_study
```

### Monitoring Queries

```sql
-- Check database size
SELECT pg_size_pretty(pg_database_size('gaze_study'));

-- Check table sizes
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- Active participants
SELECT COUNT(*) FROM participants WHERE withdrawn = FALSE;

-- Events in last 24 hours
SELECT COUNT(*) FROM events WHERE stored_at > NOW() - INTERVAL '24 hours';

-- Upload activity
SELECT 
    DATE(uploaded_at) as date,
    COUNT(*) as uploads,
    SUM(event_count) as total_events
FROM upload_batches
WHERE uploaded_at > NOW() - INTERVAL '7 days'
GROUP BY DATE(uploaded_at)
ORDER BY date DESC;
```

---

## Monitoring & Alerts

### Setup Application Monitoring

**Option 1: Simple monitoring script**

```bash
sudo nano /usr/local/bin/monitor-gaze-api.sh
```

Content:

```bash
#!/bin/bash
HEALTH_URL="https://api.gaze-study.bard.edu/health"
ALERT_EMAIL="pi@bard.edu"

# Check health endpoint
STATUS=$(curl -s -o /dev/null -w "%{http_code}" $HEALTH_URL)

if [ $STATUS -ne 200 ]; then
    echo "Gaze Study API is DOWN! Status: $STATUS" | \
      mail -s "ALERT: Gaze Study API Down" $ALERT_EMAIL
fi
```

Add to cron (check every 5 minutes):

```
*/5 * * * * /usr/local/bin/monitor-gaze-api.sh
```

**Option 2: Use external monitoring service**
- Uptime Robot (free tier)
- Pingdom
- DataDog
- New Relic

### Log Monitoring

```bash
# View real-time logs
sudo journalctl -u gaze-study-api -f

# View errors only
sudo journalctl -u gaze-study-api -p err -f

# View logs from last hour
sudo journalctl -u gaze-study-api --since "1 hour ago"
```

---

## Security Checklist

- [x] PostgreSQL uses strong password
- [x] API key is randomly generated (32+ chars)
- [x] Withdrawal secret is randomly generated
- [x] SSL/TLS certificate installed and auto-renewing
- [x] Firewall configured (allow only 80, 443, 22)
- [x] Database not exposed to public internet
- [x] Rate limiting enabled
- [x] Regular automated backups
- [x] Server patched and updated regularly
- [x] Logs monitored for suspicious activity
- [x] Access restricted to authorized personnel only

### Firewall Setup (UFW)

```bash
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP (redirects to HTTPS)
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable
sudo ufw status
```

---

## Testing

### Manual Testing

```bash
# Health check
curl https://api.gaze-study.bard.edu/health

# Register test participant
curl -X POST https://api.gaze-study.bard.edu/api/register \
  -H "Content-Type: application/json" \
  -d '{"participantId":"Ptest123abc","consentTimestamp":1699123456789}'

# Upload test batch (won't work without valid participant)
curl -X POST https://api.gaze-study.bard.edu/api/upload \
  -H "Content-Type: application/json" \
  -d '{
    "participantId":"Ptest123abc",
    "batchId":"batch_test_123",
    "eventCount":1,
    "events":[{
      "eventId":"evt_test_001",
      "timestamp":1699123456789,
      "faceGazeDirection":"toward_camera",
      "gazeOnFace":false,
      "distanceFromFace":12.3,
      "pupilDiameter":3.2,
      "pupilBaseline":3.0,
      "blinkEvent":false,
      "context":"video_call",
      "url":"zoom.us",
      "confidenceScore":0.87
    }]
  }'
```

### Load Testing

```bash
# Install Apache Bench
sudo apt install apache2-utils

# Test health endpoint (100 requests, 10 concurrent)
ab -n 100 -c 10 https://api.gaze-study.bard.edu/health

# Test upload endpoint (requires valid auth)
# Use wrk or siege for more complex scenarios
```

---

## Troubleshooting

### Common Issues

**1. Cannot connect to database**
```bash
# Check PostgreSQL is running
sudo systemctl status postgresql

# Check connection
psql -U gaze_admin -d gaze_study -c "SELECT 1;"

# Check logs
sudo tail -f /var/log/postgresql/postgresql-*.log
```

**2. 502 Bad Gateway from Nginx**
```bash
# Check Node.js server is running
sudo systemctl status gaze-study-api

# Check if port 3000 is listening
sudo netstat -tlnp | grep 3000

# Check Nginx error logs
sudo tail -f /var/log/nginx/gaze-study-api-error.log
```

**3. High memory usage**
```bash
# Check Node.js process
top -p $(pgrep -f "node server.js")

# Restart service
sudo systemctl restart gaze-study-api
```

**4. Database growing too large**
```sql
-- Check largest tables
SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename))
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- Vacuum database
VACUUM ANALYZE;
```

---

## Scaling

As the study grows, you may need to scale:

### Vertical Scaling
- Upgrade server resources (more RAM, CPU)
- Optimize PostgreSQL configuration
- Add database indexes

### Horizontal Scaling
- Add read replicas for PostgreSQL
- Load balance across multiple API servers
- Use Redis for caching

### Performance Tuning

**PostgreSQL:**

```sql
-- Adjust based on available RAM
ALTER SYSTEM SET shared_buffers = '4GB';
ALTER SYSTEM SET effective_cache_size = '12GB';
ALTER SYSTEM SET maintenance_work_mem = '1GB';
ALTER SYSTEM SET checkpoint_completion_target = 0.9;
ALTER SYSTEM SET wal_buffers = '16MB';
ALTER SYSTEM SET default_statistics_target = 100;
ALTER SYSTEM SET random_page_cost = 1.1;
ALTER SYSTEM SET effective_io_concurrency = 200;
ALTER SYSTEM SET work_mem = '64MB';
ALTER SYSTEM SET min_wal_size = '1GB';
ALTER SYSTEM SET max_wal_size = '4GB';

-- Reload configuration
SELECT pg_reload_conf();
```

---

## Support

For deployment issues:
- Email: tech-support@bard.edu
- Documentation: https://docs.gaze-study.bard.edu
- GitHub Issues: https://github.com/bard-college/gaze-detection-extension/issues

---

## Compliance

### Data Retention
- Active data: Duration of study + 2 years
- Archived data: 5 years post-publication
- Automatic deletion: After retention period or on withdrawal

### Access Control
- PI: Full access
- Research assistants: Read-only (with IRB approval)
- Auditing: All access logged

### Incident Response
1. Immediately isolate affected systems
2. Notify IRB within 24 hours
3. Notify affected participants within 72 hours
4. Document incident and remediation
5. Update security measures

---

**Server is now production-ready!** 🚀

Next step: Update `ALLOWED_ORIGINS` in `.env` once you publish the extension to Chrome Web Store and get your extension ID.
