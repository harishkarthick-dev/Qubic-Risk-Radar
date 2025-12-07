# 🚀 Deploying to Render.com

This guide walks you through deploying Qubic Risk Radar to Render.com using their free tier.

## 📋 Prerequisites

1. **GitHub Repository** - Your code must be in a GitHub repo
2. **Render Account** - Sign up at [render.com](https://render.com) (free)
3. **Environment Variables Ready** - Have your API keys ready:
   - JWT_SECRET (auto-generated if not provided)
   - GEMINI_API_KEY (optional, for AI features)
   - SMTP credentials (optional, for email)
   - Discord/Telegram tokens (optional, for notifications)

## 🎯 One-Click Deployment

### Method 1: Using render.yaml (Recommended)

1. **Fork/Clone this repository** to your GitHub account

2. **Connect to Render:**
   - Go to [Render Dashboard](https://dashboard.render.com)
   - Click **New** → **Blueprint**
   - Connect your GitHub repository
   - Select branch: `main`

3. **Render will automatically detect `render.yaml` and create:**
   - ✅ Web Service (Frontend + Backend)
   - ✅ PostgreSQL Database (Free, 90 days)
   - ✅ Redis Cache (Free, 90 days)

4. **Set Required Environment Variables:**
   - In the Render Dashboard, go to your web service
   - Navigate to **Environment** tab
   - Add/update these variables:
     ```
     SMTP_USER=your-email@gmail.com
     SMTP_PASSWORD=your-app-password
     GEMINI_API_KEY=your-gemini-api-key (optional)
     ```

5. **Deploy!**
   - Click **Create New Resources**
   - Wait 5-10 minutes for initial deployment
   - Your app will be live at: `https://qubic-risk-radar.onrender.com`

### Method 2: Manual Setup

If you prefer manual setup or need to customize:

#### Step 1: Create PostgreSQL Database

1. In Render Dashboard, click **New** → **PostgreSQL**
2. Configure:
   - **Name:** `qubic-risk-radar-db`
   - **Database:** `qubic_radar_db`
   - **User:** `qubic_radar`
   - **Plan:** Free
   - **Region:** Oregon (or nearest)
3. Click **Create Database**
4. Copy the **Internal Database URL** (we'll use this later)

#### Step 2: Create Redis Instance

1. Click **New** → **Redis**
2. Configure:
   - **Name:** `qubic-risk-radar-redis`
   - **Plan:** Free
   - **Region:** Oregon (same as database)
   - **Maxmemory Policy:** allkeys-lru
3. Click **Create Redis**
4. Copy the **Internal Redis URL**

#### Step 3: Create Web Service

1. Click **New** → **Web Service**
2. Connect your GitHub repository
3. Configure:
   - **Name:** `qubic-risk-radar`
   - **Environment:** Docker
   - **Branch:** main
   - **Plan:** Free
   - **Region:** Oregon
   - **Dockerfile Path:** `./Dockerfile`
   - **Docker Context:** `.`

4. **Add Environment Variables:**

Click **Advanced** → **Add Environment Variable** and add:

```env
# Database (use Internal URL from Step 1)
DATABASE_URL=postgresql://qubic_radar:xxxxx@xxx/qubic_radar_db

# Redis (use Internal URL from Step 2)
REDIS_URL=redis://xxx:6379

# JWT & Security
JWT_SECRET=your_jwt_secret_minimum_32_characters_long
WEBHOOK_SECRET=your_webhook_secret_here

# URLs (update with your Render URL)
FRONTEND_URL=https://qubic-risk-radar.onrender.com
BACKEND_URL=https://qubic-risk-radar.onrender.com

# Email
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=noreply@qubicradar.io
SMTP_FROM_NAME=Qubic Risk Radar

# Trial & Pricing
PRO_TRIAL_DAYS=30
PRICING_ENABLED=true

# AI (Optional)
GEMINI_API_KEY=your-gemini-api-key
GEMINI_MODEL=gemini-1.5-pro
AI_DETECTION_ENABLED=true

# Qubic
QUBIC_RPC_URL=https://rpc.qubic.org

# CORS
CORS_ORIGINS=["https://qubic-risk-radar.onrender.com"]
```

5. **Configure Health Check:**
   - **Health Check Path:** `/health`

6. Click **Create Web Service**

## 🔧 Post-Deployment Configuration

### 1. Verify Deployment

Once deployed, check:
- ✅ Web service is running (green status)
- ✅ Database is connected
- ✅ Redis is connected

### 2. Access Your Application

Your app will be available at:
- **Frontend:** `https://qubic-risk-radar.onrender.com`
- **Backend API:** `https://qubic-risk-radar.onrender.com/api`
- **API Docs:** `https://qubic-risk-radar.onrender.com/docs`

### 3. Create First User

1. Go to your frontend URL
2. Click **Sign Up**
3. Create your admin account
4. Verify email (if SMTP configured)

### 4. Configure Webhooks (Optional)

If you want Discord/Telegram notifications:
1. Go to Render Dashboard → Your Web Service → Environment
2. Add:
   ```
   DISCORD_WEBHOOK_URL_CRITICAL=https://discord.com/api/webhooks/...
   TELEGRAM_BOT_TOKEN=123456789:ABC...
   TELEGRAM_CHAT_ID=-1001234567890
   ```
3. Save changes (triggers redeployment)

## 📊 Free Tier Limitations

### Important Notes:

**Web Service (Free Plan):**
- ✅ 750 hours/month (enough for 24/7 with one service)
- ⚠️ Spins down after 15 minutes of inactivity
- ⚠️ Cold start takes 30-60 seconds
- ✅ 512 MB RAM
- ✅ Auto-deploys on git push

**PostgreSQL (Free Plan):**
- ⚠️ **Expires after 90 days** (upgrade to paid or migrate data)
- ✅ 1 GB storage
- ✅ 10 concurrent connections
- ⚠️ Deleted if inactive for 90 days

**Redis (Free Plan):**
- ⚠️ **Expires after 90 days** (upgrade to paid or migrate)
- ✅ 25 MB max memory
- ⚠️ Data may be evicted with allkeys-lru policy

**Recommendations:**
1. For production, upgrade to paid plans ($7/month for persistent database)
2. Set up database backups
3. Use external Redis if needed (RedisLabs free tier)

## 🔄 Auto-Deploy on Push

With `render.yaml`, Render automatically deploys when you push to `main`:

```bash
git add .
git commit -m "Update application"
git push origin main
```

Wait 3-5 minutes, and your changes are live!

## 📝 Managing Environment Variables

### Via Dashboard:
1. Go to your web service
2. Click **Environment** tab
3. Add/Edit/Delete variables
4. Click **Save Changes** (triggers redeployment)

### Via render.yaml:
1. Edit `render.yaml` 
2. Commit and push
3. Render updates configuration automatically

## 🔍 Monitoring & Logs

### View Logs:
1. Go to your web service in Render Dashboard
2. Click **Logs** tab
3. See real-time logs from your application

### Useful log commands:
- Filter by service: Use dropdown
- Search logs: Use search bar
- Download logs: Click download icon

### Backend Logs:
```
Supervisor backend logs: /var/log/supervisor/backend.out.log
Supervisor nginx logs: /var/log/supervisor/nginx.out.log
```

Access via SSH (paid plans only) or check in Logs tab.

## 🐛 Troubleshooting

### Deployment Failed

**Check build logs:**
1. Go to web service
2. Click **Events** tab
3. Review build/deployment errors

**Common issues:**
- Missing Dockerfile → Verify Dockerfile exists in repo root
- Build timeout → Free tier builds timeout after 15 min
- Out of memory → Reduce build complexity

### Application Not Starting

**Check logs:**
- Database connection errors → Verify DATABASE_URL
- Redis connection errors → Verify REDIS_URL
- Missing env vars → Check all required variables are set

### Database Connection Error

**Verify DATABASE_URL format:**
```
postgresql://user:password@host:port/database
```

**Check database status:**
- Go to PostgreSQL resource
- Verify it's running (green status)

### Cold Start Issues

Free tier services spin down after 15 min inactivity:
- First request takes 30-60s to wake up
- Subsequent requests are fast
- **Solution:** Use a uptime monitor (e.g., UptimeRobot) to ping every 14 min

### Frontend Not Loading

**Check:**
1. Nginx is running → Check logs
2. Build succeeded → Verify frontend/dist exists
3. Port configuration → Should be 80 internally, mapped by Render

## 🔐 Security Best Practices

1. **Environment Variables:**
   - Never commit secrets to git
   - Use Render's environment variable encryption
   - Rotate secrets regularly

2. **Database:**
   - Use strong passwords
   - Enable SSL (default on Render)
   - Regular backups

3. **CORS:**
   - Update CORS_ORIGINS with your actual domain
   - Don't use wildcards in production

4. **JWT Secret:**
   - Use strong, random 32+ character secret
   - Let Render generate it or use: `openssl rand -hex 32`

## 📈 Upgrading from Free Tier

When ready for production:

### Web Service: $7/month
- No sleep/cold starts
- 512 MB RAM → 2 GB+
- Priority support

### Database: $7/month
- No expiration
- 256 MB RAM → 1 GB+
- Automated backups
- Point-in-time recovery

### Redis: $10/month
- No expiration  
- 25 MB → 256 MB+
- Persistent storage

**Total:** ~$24/month for production-grade hosting

## 🔄 Database Backup & Migration

### Before 90-day Expiration:

**1. Backup Database:**
```bash
# Using Render's shell (paid tier)
pg_dump $DATABASE_URL > backup.sql

# Or locally
pg_dump <DATABASE_URL> > backup.sql
```

**2. Create New Database:**
- Create new free or paid PostgreSQL instance
- Note the new DATABASE_URL

**3. Restore:**
```bash
psql <NEW_DATABASE_URL> < backup.sql
```

**4. Update Environment:**
- Update DATABASE_URL in web service
- Redeploy

## 📚 Additional Resources

- **Render Docs:** https://render.com/docs
- **Blueprint Spec:** https://render.com/docs/blueprint-spec
- **Docker on Render:** https://render.com/docs/docker
- **Environment Variables:** https://render.com/docs/environment-variables

## ✅ Deployment Checklist

Before going live:

- [ ] Repository connected to Render
- [ ] render.yaml configured
- [ ] All required environment variables set
- [ ] Database created and connected
- [ ] Redis created and connected
- [ ] Health check working (`/health` endpoint)
- [ ] Logs show successful startup
- [ ] Frontend accessible
- [ ] Backend API accessible (`/docs`)
- [ ] Can create user account
- [ ] Email verification works (if configured)
- [ ] Set up uptime monitor (prevent cold starts)
- [ ] Configure custom domain (optional)

## 🎉 You're Live!

Your Qubic Risk Radar is now deployed and accessible worldwide!

**Next steps:**
1. Share your app URL
2. Monitor usage and logs
3. Set up backups
4. Consider upgrading for production use

---

**Need help?** Check [Render's Documentation](https://render.com/docs) or open an issue on GitHub.
