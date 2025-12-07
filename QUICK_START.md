# Quick Reference Card - Qubic Risk Radar

## 🚀 Start Everything (One Command)

**Windows:**
```bash
start.bat
```

**Linux/Mac:**
```bash
chmod +x start.sh && ./start.sh
```

## 🌐 Access Points

- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8000  
- **API Docs:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

## 🛠️ Common Commands

### View Logs
```bash
docker-compose logs -f           # All services
docker-compose logs -f app       # App only
docker-compose logs -f postgres  # Database only
```

### Stop Services
```bash
docker-compose down              # Stop containers
docker-compose down -v           # Stop + remove data
```

### Restart
```bash
docker-compose restart           # Restart all
docker-compose restart app       # Restart app only
```

### Shell Access
```bash
# App container
docker exec -it qrr-app bash

# Database
docker exec -it qrr-postgres psql -U qubic_radar -d qubic_radar_db

# Redis
docker exec -it qrr-redis redis-cli
```

### Database Operations
```bash
# Backup
docker exec qrr-postgres pg_dump -U qubic_radar qubic_radar_db > backup.sql

# Restore
docker exec -i qrr-postgres psql -U qubic_radar -d qubic_radar_db < backup.sql

# Migrations (inside container)
docker exec -it qrr-app bash
cd backend && alembic upgrade head
```

## 🐛 Troubleshooting

### Port Conflicts
Change ports in `docker-compose.yml`:
```yaml
ports:
  - "8001:8000"  # Backend
  - "3001:80"    # Frontend
```

### Container Issues
```bash
# Rebuild from scratch
docker-compose down -v
docker-compose build --no-cache
docker-compose up
```

### View App Logs
```bash
# Backend
docker exec qrr-app tail -f /var/log/supervisor/backend.out.log

# Frontend (nginx)
docker exec qrr-app tail -f /var/log/supervisor/nginx.out.log
```

## 📁 Important Files

- `.env` - Configuration (create from `.env.example`)
- `docker-compose.yml` - Service definitions
- `Dockerfile` - Unified app container
- `DOCKER_SETUP.md` - Detailed documentation

## 🔐 Required Environment Variables

Minimum `.env` configuration:
```env
POSTGRES_PASSWORD=your_secure_password
JWT_SECRET=your_jwt_secret_key_minimum_32_characters
```

Optional but recommended:
```env
GEMINI_API_KEY=your_google_ai_api_key
SMTP_HOST=smtp.gmail.com
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your_app_password
```

## 🏗️ Architecture

```
qrr-app (Ports: 3000, 8000)
├── Frontend (Nginx on :80)
└── Backend (FastAPI on :8000)

qrr-postgres (Port: 5432)
qrr-redis (Port: 6379)
```

## 📚 Full Documentation

See [DOCKER_SETUP.md](DOCKER_SETUP.md) for complete guide.
