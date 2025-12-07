# Render.com Quick Deploy Button

Deploy Qubic Risk Radar to Render with one click:

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/YOUR_USERNAME/YOUR_REPO_NAME)

## What Gets Deployed

Clicking the button above will automatically create:

1. **Web Service** - Your application (Frontend + Backend)
2. **PostgreSQL Database** - 1GB storage, 90 days free
3. **Redis Instance** - 25MB memory, 90 days free

## After Deployment

1. **Set Environment Variables** in Render Dashboard:
   - `SMTP_USER` - Your email for sending notifications
   - `SMTP_PASSWORD` - Your email app password
   - `GEMINI_API_KEY` - For AI detection (optional)

2. **Access Your App:**
   - Frontend: `https://qubic-risk-radar.onrender.com`
   - API Docs: `https://qubic-risk-radar.onrender.com/docs`

## Free Tier Notes

⚠️ **Important Free Tier Limitations:**

- Web service spins down after 15 min of inactivity (30-60s cold start)
- PostgreSQL expires after 90 days
- Redis expires after 90 days

For production use, upgrade to paid plans ($7/month for web service, $7/month for database).

## Full Documentation

See [RENDER_DEPLOYMENT.md](RENDER_DEPLOYMENT.md) for complete deployment guide.

## Manual Deployment

If you prefer manual deployment:

1. Fork this repository
2. Go to [Render Dashboard](https://dashboard.render.com)
3. Click **New** → **Blueprint**
4. Connect your repository
5. Render will detect `render.yaml` and create all services

---

**Need help?** Check the [deployment guide](RENDER_DEPLOYMENT.md) or open an issue.
