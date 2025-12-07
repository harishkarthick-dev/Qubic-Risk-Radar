# Qubic Risk Radar Next-Gen 🚀

AI-powered blockchain security monitoring system for the Qubic network.

## 🎯 Features

- **AI Detection Engine**: Google Gemini-powered threat analysis
- **Smart Routing**: Multi-channel notifications (Discord, Telegram, Email, Webhooks)
- **Multi-Webhook Support**: Unlimited webhook configurations with tagging
- **Analytics Dashboard**: Comprehensive reporting and insights
- **Real-time Monitoring**: Event normalization and classification

## 📊 System Overview

**Backend**: FastAPI + PostgreSQL + Google Gemini AI  
**Frontend**: React + TypeScript + Vite  
**Database**: PostgreSQL with 9 tables  
**APIs**: 50+ endpoints  
**Services**: 6 backend services

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose
- Google Gemini API key (optional, for AI features)

### One-Command Setup ⚡

**For Windows:**
```bash
start.bat
```

**For Linux/Mac:**
```bash
chmod +x start.sh
./start.sh
```

That's it! The script will:
1. Create `.env` from `.env.example` if needed
2. Build all containers (frontend + backend + databases)
3. Run database migrations
4. Start all services

**Access the application:**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

### Manual Docker Setup (Alternative)

```bash
# Copy environment file
cp .env.example .env
# Edit .env with your configuration (JWT_SECRET, GEMINI_API_KEY, etc.)

# Start everything
docker-compose up --build

# In another terminal, view logs
docker-compose logs -f

# Stop all services
docker-compose down
```

### Development Setup (Without Docker)

<details>
<summary>Click to expand traditional setup instructions</summary>

#### Backend Setup

```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Set environment variables
cp .env.example .env
# Edit .env with your configuration

# Run database migrations
alembic upgrade head

# Start server
python -m app.main
```

#### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Set environment variables
echo "VITE_API_URL=http://localhost:8000" > .env

# Start development server
npm run dev
```

</details>

## ☁️ Deploy to Render (Free Hosting)

Deploy to the cloud with one click:

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy)

**What you get:**
- ✅ Free hosting for 90 days
- ✅ PostgreSQL database (1GB)
- ✅ Redis cache (25MB)
- ✅ Automatic deployments on git push
- ✅ HTTPS enabled by default

**After deployment:**
1. Set environment variables in Render Dashboard
2. Your app is live at `https://your-app.onrender.com`

See [RENDER_DEPLOYMENT.md](RENDER_DEPLOYMENT.md) for detailed deployment guide.


## 📝 Environment Variables

### Backend (.env)

```env
DATABASE_URL=postgresql+asyncpg://user:pass@localhost/qubic_radar
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=43200

# Gemini AI
GEMINI_API_KEY=your-gemini-api-key
GEMINI_MODEL=gemini-1.5-pro
AI_DETECTION_ENABLED=true

# URLs
BACKEND_URL=http://localhost:8000
FRONTEND_URL=http://localhost:5173

# Notifications (optional)
DISCORD_WEBHOOK_URL_CRITICAL=
TELEGRAM_BOT_TOKEN=
SMTP_HOST=
SMTP_PORT=587
```

### Frontend (.env)

```env
VITE_API_URL=http://localhost:8000
```

## 📦 Project Structure

```
Qubic-EC-C/
├── backend/
│   ├── app/
│   │   ├── api/              # API endpoints
│   │   ├── models/           # Database models
│   │   ├── services/         # Business logic
│   │   ├── config.py         # Configuration
│   │   └── main.py           # FastAPI app
│   ├── alembic/              # Database migrations
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── api/              # API client
│   │   ├── pages/            # Page components
│   │   ├── types/            # TypeScript types
│   │   └── App.tsx           # Main app
│   └── package.json
│
└── README.md
```

## 🛠️ Development

### Database Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

### Running Tests

```bash
# Backend
pytest

# Frontend
npm test
```

## 📚 API Documentation

Once the backend is running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## 🔐 Security Features

- JWT authentication
- Password hashing (bcrypt)
- Webhook signature verification
- SQL injection prevention
- Input validation
- User data isolation

## 📈 Monitoring & Analytics

- Real-time detection statistics
- Severity distribution charts
- Category breakdown
- Timeline trends
- Custom report generation

## 🎨 Frontend Pages

1. **Dashboard** (`/dashboard`) - Overview and quick stats
2. **Detections** (`/detections`) - Browse AI detections
3. **Webhooks** (`/webhooks`) - Manage webhook configurations
4. **Analytics** (`/analytics`) - Reports and insights

## 🔧 Troubleshooting

### Database Connection Failed
```bash
# Check PostgreSQL is running
sudo service postgresql start

# Verify connection
psql -U your_user -d qubic_radar
```

### Frontend Build Errors
```bash
# Clean install
rm -rf node_modules package-lock.json
npm install
```

### Import Errors
```bash
# Activate virtual environment
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Reinstall dependencies
pip install -r requirements.txt
```

## 📊 Database Schema

9 main tables:
- `users` - User accounts
- `events` - Raw blockchain events
- `normalized_events` - Processed events
- `ai_detections` - AI analysis results
- `incidents` - Security incidents
- `notification_routing_rules` - Routing configuration
- `notification_logs` - Delivery tracking
- `multi_scope_reports` - Analytics reports
- `easyconnect_configs` - Webhook configurations

## 🚢 Deployment

### Backend (Docker)

```bash
docker build -t qubic-radar-backend .
docker run -p 8000:8000 qubic-radar-backend
```

### Frontend (Netlify/Vercel)

```bash
npm run build
# Deploy dist/ folder
```

## 📄 Documentation

See the `docs/` folder:
- `DEPLOYMENT_GUIDE.md` - Detailed deployment instructions
- `PHASE1_COMPLETE.md` - AI Detection implementation
- `PHASE2_COMPLETE.md` - Smart Routing implementation
- `PHASE3_COMPLETE.md` - Multi-Webhook implementation
- `PHASES_4_5_COMPLETE.md` - Analytics & Polish
- `FRONTEND_COMPLETE.md` - Frontend implementation
- `BUGS_AND_FIXES.md` - Known issues and fixes

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Open a Pull Request

## 📝 License

MIT License - see LICENSE file for details

## 👥 Authors

Qubic Risk Radar Development Team

## 🙏 Acknowledgments

- Google Gemini AI for detection engine
- FastAPI framework
- React ecosystem
- PostgreSQL database

---

**Status**: Production Ready ✅  
**Version**: 1.0.0  
**Last Updated**: December 2025

For support, open an issue on GitHub.
