# Production Deployment Guide

## Pre-Deployment Security Checklist

### 1. Secrets Management
```bash
# Generate strong JWT secret
openssl rand -base64 32

# Create .env file (NEVER commit to git)
cp .env.example .env

# Populate with production values:
# - JWT_SECRET=<generated-key>
# - CORS_ORIGIN=https://yourdomain.com
# - Database credentials
# - Redis credentials
```

### 2. Environment Setup
```bash
# Ensure Node.js 18+ is installed
node --version  # v18.0.0 or higher

# Install dependencies
npm ci  # Use ci instead of install for reproducible builds

# Install production server (PM2, systemd, etc.)
npm install -g pm2
```

### 3. Database Migration
**From JSON Files → PostgreSQL:**

```sql
-- Create users table with encryption
CREATE TABLE users (
  id SERIAL PRIMARY KEY,
  email VARCHAR(255) UNIQUE NOT NULL,
  name VARCHAR(255) NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  role VARCHAR(50) NOT NULL,
  mfa_enabled BOOLEAN DEFAULT false,
  mfa_secret VARCHAR(255) ENCRYPTED,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create audit_logs table
CREATE TABLE audit_logs (
  id SERIAL PRIMARY KEY,
  user_email VARCHAR(255),
  action VARCHAR(255) NOT NULL,
  resource VARCHAR(255),
  ip_address INET,
  user_agent TEXT,
  status VARCHAR(50),
  timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  details JSONB
);

-- Create sessions table (refresh tokens)
CREATE TABLE sessions (
  id SERIAL PRIMARY KEY,
  user_email VARCHAR(255) NOT NULL,
  refresh_token VARCHAR(255) UNIQUE NOT NULL,
  token_family VARCHAR(255),  -- For refresh token rotation detection
  expires_at TIMESTAMP NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  revoked BOOLEAN DEFAULT false
);

-- Indexes for performance
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_sessions_user ON sessions(user_email);
CREATE INDEX idx_sessions_token ON sessions(refresh_token);
CREATE INDEX idx_audit_logs_timestamp ON audit_logs(timestamp);
```

### 4. SSL/TLS Configuration

**Using Let's Encrypt with Nginx:**
```bash
# Install Certbot
sudo apt-get install certbot python3-certbot-nginx

# Generate certificate
sudo certbot certonly --nginx -d yourdomain.com -d www.yourdomain.com

# Certificate location: /etc/letsencrypt/live/yourdomain.com/
```

**Nginx Configuration:**
```nginx
server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Security Headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Reverse Proxy to Node.js
    location / {
        proxy_pass http://localhost:4000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Rate limiting at Nginx level
    location /api/login {
        limit_req zone=login burst=5 nodelay;
        proxy_pass http://localhost:4000;
    }
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

# Rate limiting zones
limit_req_zone $binary_remote_addr zone=login:10m rate=5r/15m;
limit_req_zone $binary_remote_addr zone=general:10m rate=100r/15m;
```

### 5. Process Manager (PM2)

**Install and Configure:**
```bash
npm install -g pm2

# Create ecosystem.config.js
cat > ecosystem.config.js << 'EOF'
module.exports = {
  apps: [{
    name: 'hospital-portal-backend',
    script: './server/index.js',
    instances: 'max',
    exec_mode: 'cluster',
    env: {
      NODE_ENV: 'production',
      JWT_SECRET: process.env.JWT_SECRET,
      CORS_ORIGIN: process.env.CORS_ORIGIN
    },
    error_file: '/var/log/hospital-portal/error.log',
    out_file: '/var/log/hospital-portal/out.log',
    log_file: '/var/log/hospital-portal/combined.log',
    time_format: 'YYYY-MM-DD HH:mm:ss Z',
    watch: false,
    ignore_watch: ['node_modules', 'logs'],
    max_memory_restart: '500M',
    autorestart: true,
    max_restarts: 10,
    min_uptime: '10s',
    listen_timeout: 10000
  }]
};
EOF

# Start application
pm2 start ecosystem.config.js

# Make PM2 start on boot
pm2 startup systemd -u www-data --hp /home/www-data
pm2 save

# Monitor
pm2 monit
pm2 logs
```

### 6. Firewall Rules

```bash
# UFW (Ubuntu Firewall)
sudo ufw enable
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp      # SSH
sudo ufw allow 80/tcp      # HTTP
sudo ufw allow 443/tcp     # HTTPS
sudo ufw allow 5432/tcp    # PostgreSQL (internal only)
```

### 7. Logging & Monitoring

**Install ELK Stack or Alternative:**

```bash
# Example: Sentry for error tracking
npm install @sentry/node

# In server code:
const Sentry = require("@sentry/node");
Sentry.init({ 
  dsn: process.env.SENTRY_DSN,
  environment: process.env.NODE_ENV
});
app.use(Sentry.Handlers.errorHandler());
```

**System Logs:**
```bash
# Create log directory
sudo mkdir -p /var/log/hospital-portal
sudo chown www-data:www-data /var/log/hospital-portal

# Set up log rotation
cat > /etc/logrotate.d/hospital-portal << 'EOF'
/var/log/hospital-portal/*.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    create 0644 www-data www-data
}
EOF
```

### 8. Database Backups

```bash
# Daily backup script
cat > /usr/local/bin/backup-hospital-db.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/var/backups/hospital-portal"
DATE=$(date +%Y-%m-%d_%H-%M-%S)
mkdir -p $BACKUP_DIR

pg_dump -U postgres hospital_db | \
  gzip > $BACKUP_DIR/hospital_db_$DATE.sql.gz

# Keep only last 30 days
find $BACKUP_DIR -name "*.sql.gz" -mtime +30 -delete
EOF

chmod +x /usr/local/bin/backup-hospital-db.sh

# Schedule with cron (daily at 2 AM)
(crontab -l; echo "0 2 * * * /usr/local/bin/backup-hospital-db.sh") | crontab -
```

### 9. Health Checks

**Add health endpoint to backend:**
```javascript
app.get('/health', (req, res) => {
  res.json({ 
    status: 'ok',
    timestamp: new Date(),
    environment: process.env.NODE_ENV
  })
})
```

**Configure monitoring:**
```bash
# PM2 Plus / Datadog / New Relic integration
pm2 install pm2-auto-pull
pm2 save
```

### 10. Pre-Launch Verification

```bash
# 1. Test environment variables
env | grep -E "JWT_SECRET|CORS_ORIGIN|NODE_ENV"

# 2. Verify database connectivity
npm run test:db

# 3. Test rate limiting
for i in {1..6}; do
  curl -X POST https://yourdomain.com/api/login \
    -H "Content-Type: application/json" \
    -d '{"email":"test@test.com","password":"test"}'
done

# 4. Test SSL certificate
curl -vI https://yourdomain.com

# 5. Verify HTTPS headers
curl -I https://yourdomain.com | grep -E "Strict-Transport|X-Frame-Options|X-Content-Type"

# 6. Load test
npm run test:load  # Using Apache Bench or k6

# 7. Security scan
npm audit
npm audit fix --audit-level=moderate
```

### 11. Deployment Steps

```bash
# 1. Pull latest code
cd /var/www/hospital-portal
git pull origin main

# 2. Install dependencies
npm ci

# 3. Run database migrations
npm run migrate

# 4. Build frontend (if applicable)
npm run build

# 5. Start/restart application
pm2 restart ecosystem.config.js

# 6. Verify it's running
pm2 status
curl -s https://yourdomain.com/health | jq
```

### 12. Monitoring & Alerts

**Key Metrics to Monitor:**
- Server CPU/Memory usage
- Response times (p50, p95, p99)
- Error rates
- Failed login attempts (rate limiting triggers)
- MFA attempt failures
- Database connection pool usage
- Disk space

**Alert Thresholds:**
- CPU > 80% for 5 minutes
- Memory > 90%
- Error rate > 5%
- Response time p95 > 2s
- Failed login attempts > 20/minute

---

## Rollback Procedure

```bash
# If deployment fails
git rollback <previous-commit>
npm ci
pm2 restart ecosystem.config.js
pm2 logs  # Check for errors
```

---

## Post-Deployment

1. ✅ Verify all endpoints responding
2. ✅ Check logs for errors
3. ✅ Monitor system resources
4. ✅ Test with actual users (small group first)
5. ✅ Monitor error rates and performance
6. ✅ Document any issues

---

## Support

For deployment issues, check:
- `/var/log/hospital-portal/` (application logs)
- `journalctl -u pm2-www-data` (process manager logs)
- `sudo nginx -t` (Nginx configuration)
- `sudo systemctl status postgresql` (database status)

---

**Last Updated:** November 25, 2025
**Version:** 1.0
