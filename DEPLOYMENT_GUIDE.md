# DEPLOYMENT GUIDE

## Quick Start (5 Minutes)

### Prerequisites
- Python 3.11+ installed
- Node.js 20+ installed
- Gemini API key from https://aistudio.google.com/

### Step 1: Clone/Setup Project
```bash
cd C:\PROJECTS\GenAI-voice-Assistant
```

### Step 2: Backend Setup
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r backend/requirements.txt

# Create .env file
copy .env.example .env  # Windows: copy instead of cp

# Edit .env and add your Gemini API key
# GEMINI_API_KEY=your_key_here
```

### Step 3: Frontend Setup
```bash
cd frontend
npm install
```

### Step 4: Run Both (Open 2 Terminals)

**Terminal 1 - Backend:**
```bash
cd C:\PROJECTS\GenAI-voice-Assistant
venv\Scripts\activate  # Windows
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 - Frontend:**
```bash
cd C:\PROJECTS\GenAI-voice-Assistant\frontend
npm run dev
```

### Step 5: Access
- Frontend: http://localhost:5173
- Backend: http://localhost:8000
- Swagger Docs: http://localhost:8000/docs

---

## Production Deployment

### Option 1: Linux Server (Recommended)

#### Prerequisites
- Ubuntu 22.04 LTS
- Python 3.11+
- Node.js 20+
- Supervisor (for process management)
- Nginx (for reverse proxy)

#### Setup

```bash
# 1. Clone repository
git clone <your-repo> /app
cd /app

# 2. Backend setup
python3.11 -m venv venv
source venv/bin/activate
pip install -r backend/requirements.txt

# 3. Frontend setup
cd frontend
npm install
npm run build  # Production build
cd ..

# 4. Create .env
cp .env.example .env
nano .env  # Edit with your API key
```

#### Systemd Service (Backend)

Create `/etc/systemd/system/voice-assistant-backend.service`:

```ini
[Unit]
Description=GenAI Voice Assistant Backend
After=network.target

[Service]
Type=notify
User=ubuntu
WorkingDirectory=/app
Environment="PATH=/app/venv/bin"
ExecStart=/app/venv/bin/uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Start:
```bash
sudo systemctl daemon-reload
sudo systemctl start voice-assistant-backend
sudo systemctl enable voice-assistant-backend
```

#### Nginx Configuration

Create `/etc/nginx/sites-available/voice-assistant`:

```nginx
server {
    listen 80;
    server_name yourdomain.com;

    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl;
    server_name yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    # Frontend
    location / {
        root /app/frontend/dist;
        try_files $uri $uri/ /index.html;
        expires 1h;
    }

    # Backend API
    location /api/ {
        proxy_pass http://127.0.0.1:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket
    location /ws/ {
        proxy_pass http://127.0.0.1:8000/ws/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable:
```bash
sudo ln -s /etc/nginx/sites-available/voice-assistant /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

---

### Option 2: Docker (Recommended for Consistency)

#### Dockerfile (Backend)

Create `Dockerfile.backend`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy code
COPY . .

# Set environment
ENV PYTHONUNBUFFERED=1
ENV PORT=8000

# Run
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### Dockerfile (Frontend)

Create `Dockerfile.frontend`:

```dockerfile
FROM node:20-alpine as builder

WORKDIR /app

# Install dependencies and build
COPY frontend/package*.json .
RUN npm ci
COPY frontend .
RUN npm run build

# Serve
FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

#### Docker Compose

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  backend:
    build:
      context: .
      dockerfile: Dockerfile.backend
    ports:
      - "8000:8000"
    environment:
      - GEMINI_API_KEY=${GEMINI_API_KEY}
      - MONGODB_URI=mongodb://mongo:27017/genai_assistant
      - ENVIRONMENT=production
    depends_on:
      - mongo
    restart: unless-stopped

  frontend:
    build:
      context: .
      dockerfile: Dockerfile.frontend
    ports:
      - "80:80"
    environment:
      - VITE_API_BASE_URL=http://backend:8000
      - VITE_WS_BASE_URL=ws://backend:8000
    depends_on:
      - backend
    restart: unless-stopped

  mongo:
    image: mongo:6
    ports:
      - "27017:27017"
    volumes:
      - mongo_data:/data/db
    environment:
      - MONGO_INITDB_ROOT_USERNAME=admin
      - MONGO_INITDB_ROOT_PASSWORD=${MONGO_PASSWORD}
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped

volumes:
  mongo_data:
  redis_data:
```

#### Run with Docker Compose

```bash
# Build
docker-compose build

# Run
docker-compose up -d

# Access
# Frontend: http://localhost
# Backend: http://localhost:8000
```

---

### Option 3: Cloud Deployment

#### AWS Elastic Beanstalk

```bash
# Install EB CLI
pip install awsebcli

# Initialize
eb init -p "python-3.11 running on 64bit Amazon Linux 2" voice-assistant

# Create environment
eb create voice-assistant-prod

# Deploy
eb deploy

# Open
eb open
```

#### Google Cloud App Engine

```yaml
# app.yaml
runtime: python311
env: standard
entrypoint: uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT

env_variables:
  GEMINI_API_KEY: "YOUR_KEY"
  ENVIRONMENT: "production"
```

```bash
gcloud app deploy
```

#### Heroku

```bash
# Login
heroku login

# Create app
heroku create voice-assistant

# Add buildpacks
heroku buildpacks:add heroku/python
heroku buildpacks:add heroku/nodejs

# Deploy
git push heroku main

# Set env vars
heroku config:set GEMINI_API_KEY=your_key
```

---

## Environment Variables

### Required
```bash
GEMINI_API_KEY=sk-xxx...        # Google Gemini API key
```

### Optional
```bash
MONGODB_URI=mongodb://...       # MongoDB connection string
MONGODB_DATABASE=genai_assistant
CHROMA_PATH=/app/rag/data/chroma
ENVIRONMENT=production
LOG_LEVEL=INFO
PORT=8000
HOST=0.0.0.0
FRONTEND_URL=https://yourdomain.com
```

---

## Monitoring & Logging

### View Logs

**Local:**
```bash
# Backend
# Logs appear in terminal running uvicorn

# Frontend
# Logs appear in browser console (F12)
```

**Production:**
```bash
# Systemd
sudo journalctl -u voice-assistant-backend -f

# Docker
docker-compose logs -f backend

# File
tail -f /var/log/voice-assistant.log
```

### Health Check

```bash
curl http://localhost:8000/health

# Response:
# {"status": "healthy", "version": "1.0.0", "app": "Multilingual GenAI Voice Assistant"}
```

---

## Troubleshooting

### Backend Won't Start

**Error: "ModuleNotFoundError: No module named 'google.genai'"**
```bash
pip install google-genai chromadb
```

**Error: "GEMINI_API_KEY not found"**
```bash
# Check .env file exists and has value
cat .env | grep GEMINI_API_KEY

# If missing, add it
echo "GEMINI_API_KEY=your_key_here" >> .env
```

**Error: "Address already in use"**
```bash
# Change port
uvicorn backend.app.main:app --port 8001
```

### Frontend Won't Connect

**Error: "WebSocket connection failed"**
- Check backend is running on port 8000
- Check VITE_WS_BASE_URL is correct
- Check firewall allows port 8000

**Error: "Microphone access denied"**
- Use localhost, not IP address
- Use HTTPS, not HTTP (Chrome requirement)
- Check browser permissions

### Gemini API Errors

**Error: "401 Unauthorized"**
- API key is invalid or expired
- Generate new key from https://aistudio.google.com/

**Error: "429 Too Many Requests"**
- Hit rate limit
- Wait or upgrade your plan

**Error: "503 Service Unavailable"**
- Gemini service is down
- Check https://status.cloud.google.com/

---

## Performance Tuning

### Backend

```python
# config.py
WORKERS = 4  # Number of worker processes
THREAD_POOL_SIZE = 10
REQUEST_TIMEOUT = 30
```

### Frontend

```bash
# Build optimization
npm run build

# Gzip compression
# Configure in nginx.conf:
gzip on;
gzip_types text/plain application/json;
gzip_min_length 1000;
```

### Database

```bash
# MongoDB indexing
db.customers.createIndex({ "phone": 1 })
db.bills.createIndex({ "customer_id": 1 })

# Redis eviction
maxmemory-policy allkeys-lru
```

---

## Scaling

### Horizontal Scaling

```bash
# Multiple backend instances
supervisor:
  [program:backend-1]
  command=/app/venv/bin/uvicorn ... --port 8001
  
  [program:backend-2]
  command=/app/venv/bin/uvicorn ... --port 8002

# Load balance with Nginx upstream
upstream backend {
    server 127.0.0.1:8001;
    server 127.0.0.1:8002;
}
```

### Caching Layer

```bash
# Add Redis
# In production, cache:
# - Gemini responses (5 min)
# - RAG results (1 hour)
# - Tool results (15 min)
```

---

## Security Checklist

- [ ] GEMINI_API_KEY not in source code
- [ ] .env file not committed to git
- [ ] HTTPS enabled in production
- [ ] CORS properly configured
- [ ] Input validation enabled
- [ ] Rate limiting configured
- [ ] Logs sanitized (no API keys)
- [ ] Database credentials secured
- [ ] Firewall blocks unnecessary ports
- [ ] Regular backups configured

---

## Maintenance

### Regular Tasks

```bash
# Daily
- Check logs for errors
- Monitor API usage

# Weekly
- Test backup/restore
- Review performance metrics
- Update dependencies (npm/pip)

# Monthly
- Full system test
- Security audit
- Database optimization
- Clean old logs
```

### Backup

```bash
# Backup MongoDB
mongodump --out /backups/mongo_$(date +%Y%m%d)

# Backup frontend
tar -czf /backups/frontend_$(date +%Y%m%d).tar.gz frontend/dist

# Backup .env
cp .env /backups/.env_$(date +%Y%m%d)
```

---

## Rollback Procedure

```bash
# If deployment fails:
git revert HEAD
git push

# Redeploy:
docker-compose up -d --build

# Or
eb abort
```

---

## Support

- **Documentation:** See REQUIRED_VS_OPTIONAL.md
- **Issues:** Check logs in `/var/log/`
- **Performance:** Use monitoring tools (Prometheus, Grafana)
- **Debugging:** Enable DEBUG=true in .env

---

## Summary

| Aspect | Local | Production |
|--------|-------|-----------|
| Setup Time | 10 min | 1-2 hours |
| Database | Optional | Required (MongoDB) |
| Cache | Optional | Required (Redis) |
| SSL | Not needed | Required (HTTPS) |
| Logging | Console | File + external |
| Monitoring | None | Prometheus/Grafana |
| Backups | Manual | Automated |
| High Availability | N/A | Load balanced |
| Recovery | N/A | Automated |
