# 🐳 Docker Setup Guide

This guide explains the unified Docker setup for Qubic Risk Radar.

## Architecture

The application runs in **3 containers**:

1. **qrr-app** - Combined frontend + backend in ONE container
   - Frontend: React app served by Nginx on port 80
   - Backend: FastAPI app running on port 8000
   - Both managed by Supervisor

2. **qrr-postgres** - PostgreSQL 15 database

3. **qrr-redis** - Redis cache

## Quick Start

### Windows
```bash
start.bat
```

### Linux/Mac
```bash
chmod +x start.sh
./start.sh
```

## What the Script Does

1. **Environment Check**: Creates `.env` from `.env.example` if it doesn't exist
2. **Build**: Builds the unified Docker image
3. **Start**: Starts all three containers
4. **Migrate**: Runs database migrations automatically
5. **Ready**: All services are up and running!

## Manual Commands

### Start Services
```bash
docker-compose up --build
```

### Start in Background
```bash
docker-compose up --build -d
```

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f app
docker-compose logs -f postgres
docker-compose logs -f redis
```

### Stop Services
```bash
docker-compose down
```

### Stop and Remove Volumes (Clean Slate)
```bash
docker-compose down -v
```

### Rebuild from Scratch
```bash
docker-compose down -v
docker-compose build --no-cache
docker-compose up
```

## Access Points

After starting, access the application at:

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Container Details

### App Container (qrr-app)

**Ports:**
- 8000 → Backend API
- 80 → Frontend (mapped to host 3000)

**Processes (managed by Supervisor):**
1. Backend: `uvicorn app.main:app --host 0.0.0.0 --port 8000`
2. Frontend: `nginx -g "daemon off;"`

**Logs:**
```bash
docker exec qrr-app tail -f /var/log/supervisor/backend.out.log
docker exec qrr-app tail -f /var/log/supervisor/nginx.out.log
```

### Database Container (qrr-postgres)

**Port:** 5432

**Connect:**
```bash
docker exec -it qrr-postgres psql -U qubic_radar -d qubic_radar_db
```

**Backup:**
```bash
docker exec qrr-postgres pg_dump -U qubic_radar qubic_radar_db > backup.sql
```

**Restore:**
```bash
docker exec -i qrr-postgres psql -U qubic_radar -d qubic_radar_db < backup.sql
```

### Redis Container (qrr-redis)

**Port:** 6379

**Connect:**
```bash
docker exec -it qrr-redis redis-cli
```

## Environment Variables

Required variables in `.env`:

```env
# Database
POSTGRES_PASSWORD=your_secure_password

# JWT Authentication
JWT_SECRET=your_jwt_secret_key_minimum_32_characters_long_please

# AI (Optional)
GEMINI_API_KEY=your_google_ai_api_key
GEMINI_MODEL=gemini-1.5-pro
AI_DETECTION_ENABLED=true

# Email (Optional)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your_app_password

# Notifications (Optional)
DISCORD_WEBHOOK_URL_CRITICAL=https://discord.com/api/webhooks/...
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
```

## Troubleshooting

### Port Already in Use

If ports 3000, 8000, 5432, or 6379 are already in use:

**Option 1: Stop conflicting services**
```bash
# Windows
netstat -ano | findstr :3000
taskkill /PID <PID> /F

# Linux/Mac
lsof -ti:3000 | xargs kill -9
```

**Option 2: Change ports in docker-compose.yml**
```yaml
app:
  ports:
    - "8001:8000"  # Change 8000 to 8001
    - "3001:80"    # Change 3000 to 3001
```

### Container Won't Start

**Check logs:**
```bash
docker-compose logs app
```

**Common issues:**
- Missing environment variables → Check `.env` file
- Database not ready → Wait for health check (automatic)
- Build errors → Run `docker-compose build --no-cache`

### Database Connection Error

**Verify database is healthy:**
```bash
docker-compose ps
```

Should show `healthy` for postgres.

**Test connection:**
```bash
docker exec -it qrr-postgres pg_isready -U qubic_radar
```

### Frontend Not Loading

**Check nginx:**
```bash
docker exec qrr-app nginx -t
docker exec qrr-app cat /var/log/supervisor/nginx.err.log
```

### Backend API Errors

**Check backend logs:**
```bash
docker exec qrr-app cat /var/log/supervisor/backend.out.log
docker exec qrr-app cat /var/log/supervisor/backend.err.log
```

**Common issues:**
- Database migration failed → Check migrations
- Environment variables missing → Verify `.env`

### Reset Everything

```bash
# Stop and remove all containers, networks, and volumes
docker-compose down -v

# Remove images
docker rmi qubic-ec-c-app postgres:15-alpine redis:7-alpine

# Start fresh
docker-compose up --build
```

## Development Mode

For development with hot-reload:

**Backend:**
```bash
# Mount backend as volume (add to docker-compose.yml)
volumes:
  - ./backend:/app/backend
```

**Frontend:**
```bash
# Run frontend locally instead of in container
cd frontend
npm run dev
```

## Production Considerations

For production deployment:

1. **Environment Variables:**
   - Use strong passwords
   - Set proper CORS origins
   - Configure all notification channels

2. **Volumes:**
   - Use named volumes for data persistence
   - Regular backups of postgres_data

3. **Security:**
   - Use secrets management (Docker secrets, Vault)
   - Enable HTTPS with reverse proxy (Nginx, Caddy)
   - Restrict network access

4. **Monitoring:**
   - Add health check endpoints
   - Use logging aggregation (ELK, Loki)
   - Set up alerts

5. **Scaling:**
   - Use container orchestration (Docker Swarm, Kubernetes)
   - Load balance multiple app instances
   - Separate database to managed service

## Benefits of Unified Container

✅ **Simplicity:** One container for the entire application
✅ **Performance:** No network overhead between frontend/backend
✅ **Deployment:** Single image to deploy
✅ **Development:** Faster startup times
✅ **Resource Usage:** Less memory overhead

## Architecture Diagram

```
┌─────────────────────────────────────┐
│         qrr-app Container           │
│                                     │
│  ┌─────────────┐  ┌──────────────┐ │
│  │   Nginx     │  │   FastAPI    │ │
│  │  (Port 80)  │  │  (Port 8000) │ │
│  │  Frontend   │  │   Backend    │ │
│  └─────────────┘  └──────────────┘ │
│         │                │          │
│         └────── Supervisor ────┘    │
└─────────────────────────────────────┘
            │           │
            │           │
      ┌─────┴────┐  ┌──┴──────┐
      │ postgres │  │  redis  │
      │   :5432  │  │  :6379  │
      └──────────┘  └─────────┘
```

## Next Steps

1. ✅ Start the application with `start.bat` or `start.sh`
2. ✅ Configure `.env` with your API keys
3. ✅ Access http://localhost:3000
4. ✅ Create your first user account
5. ✅ Configure webhooks and notifications

For more information, see the main [README.md](README.md).
