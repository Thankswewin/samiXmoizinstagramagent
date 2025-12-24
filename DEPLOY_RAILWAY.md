# 🚀 Railway Deployment Guide

## Quick Deploy to Railway

### Step 1: Create Railway Account
1. Go to [railway.app](https://railway.app)
2. Sign up with GitHub

### Step 2: Create New Project
1. Click "New Project"
2. Select "Deploy from GitHub repo"
3. Connect your GitHub and select this repository

### Step 3: Set Environment Variables
In Railway dashboard, go to your project → Variables tab:

```
IG_USERNAME=your_instagram_username
IG_PASSWORD=your_instagram_password
LANGUAGE=english
USE_PROXY=false
GROUP_MESSAGES=false
```

### Step 4: Deploy
Railway will automatically:
- Detect Python project
- Install dependencies from `requirements.txt`
- Run `python main.py`

### Step 5: Monitor
- Check "Deployments" tab for logs
- Bot should show "the last dm message that came in: None" when running

---

## Important Notes

⚠️ **Proxy Usage**: Railway IPs may get flagged by Instagram. Consider:
- Setting `USE_PROXY=true`
- Adding residential proxies to `proxies.txt`

⚠️ **Keep Running**: Railway free tier has usage limits. Consider upgrading for 24/7 operation.

---

## Troubleshooting

**Bot stops unexpectedly?**
- Check Railway logs for errors
- Instagram may have rate-limited the IP

**Login issues?**
- Verify credentials in Variables
- Try logging into Instagram manually first to clear any challenges

**Need support?**
Contact [@samiXmoiz_bot](https://t.me/samiXmoiz_bot)
