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
TELEGRAM_ADMIN_BOT_TOKEN=your_telegram_bot_token
```

### Step 4: Get Persistent Auth Token (Recommended)
To avoid Railway re-logging in on every deploy (which can trigger Instagram security):

1. **Run the bot locally first:**
   ```bash
   python run.py
   ```

2. **Copy the token from logs:**
   When the bot logs in, it will print:
   ```
   ============================================================
   [AUTH] NEW TOKEN GENERATED - Copy to Railway env vars:
   IG_AUTH_TOKEN=Bearer IGT:2:...
   IG_USER_ID=12345678...
   ============================================================
   ```

3. **Add to Railway environment variables:**
   ```
   IG_AUTH_TOKEN=Bearer IGT:2:...
   IG_USER_ID=12345678...
   ```

> ⚠️ **Note:** Tokens expire eventually. If you see auth errors in Railway logs, run locally again and update the env vars.

### Step 5: Deploy
Railway will automatically:
- Detect Python project
- Install dependencies from `requirements.txt`
- Run `python run.py` (runs both Instagram bot and Telegram admin bot)

### Step 6: Monitor
- Check "Deployments" tab for logs
- Bot should show "[Auth] Using environment variables for authentication"

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
