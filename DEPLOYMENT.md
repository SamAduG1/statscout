# StatScout Deployment Guide

## Quick Start - Get Your App Live in 30 Minutes

### Step 1: Deploy Backend to Render (10 minutes)

1. **Go to [render.com](https://render.com)** and sign up (free)
2. **Click "New +" → "Web Service"**
3. **Connect your GitHub repository**
   - You'll need to push your code to GitHub first (see below)
4. **Configure the service:**
   - Name: `statscout-backend`
   - Root Directory: `backend`
   - Environment: `Python 3`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn app:app`
   - Instance Type: **Free** (this is important!)
5. **Add Environment Variables** (click "Advanced"):
   - `ODDS_API_KEY` = `cbb4a79921b3771989446173daeeb917`
   - `FLASK_ENV` = `production`
   - `PYTHON_VERSION` = `3.11.0`
6. **Click "Create Web Service"**
7. **Copy your backend URL** (will be something like `https://statscout-backend.onrender.com`)

**IMPORTANT**: Render free tier spins down after 15 minutes of inactivity. First request after idle takes ~30 seconds to wake up. This is fine for beta testing!

### Step 2: Deploy Frontend to Vercel (5 minutes)

1. **Go to [vercel.com](https://vercel.com)** and sign up (free)
2. **Click "Add New" → "Project"**
3. **Import your GitHub repository**
4. **Configure the project:**
   - Framework Preset: `Vite`
   - Root Directory: `frontend`
   - Build Command: `npm run build`
   - Output Directory: `dist`
5. **Add Environment Variable:**
   - Name: `VITE_API_BASE_URL`
   - Value: Your Render backend URL (from Step 1)
6. **Click "Deploy"**
7. **Your frontend URL** will be something like `https://statscout.vercel.app`

### Step 3: Update Frontend to Use Backend URL (5 minutes)

1. Open `frontend/src/App.jsx`
2. Find the line that says `const API_BASE_URL`
3. Update it to use environment variable:
   ```javascript
   const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000';
   ```
4. Commit and push the change
5. Vercel will auto-deploy the update

### Step 4: Test It!

1. Open your Vercel URL (e.g., `https://statscout.vercel.app`)
2. Check if data loads (first load may take 30 seconds if Render was asleep)
3. If it works - you're live! Share the URL!

## Pushing to GitHub (Required First Step)

If you haven't pushed to GitHub yet:

```bash
cd c:\Users\sa100\statscout
git add .
git commit -m "Prepare for deployment"
git push origin master
```

If you don't have a GitHub remote:

1. Go to [github.com](https://github.com) and create a new repository called `statscout`
2. Run:
```bash
git remote add origin https://github.com/YOUR_USERNAME/statscout.git
git push -u origin master
```

## Troubleshooting

**Backend not responding:**
- Check Render logs (click on your service → "Logs")
- Verify environment variables are set correctly
- Free tier takes ~30 seconds to wake up from sleep

**Frontend can't connect to backend:**
- Check `VITE_API_BASE_URL` in Vercel environment variables
- Make sure you updated `App.jsx` to use the env variable
- Check browser console for CORS errors

**Build failures:**
- Render: Check Python version is 3.11
- Vercel: Make sure Node version is 18+ (usually auto-detected)

## Costs

- **Render Free Tier**: $0/month
  - 750 hours/month
  - Spins down after 15 min inactivity
  - Perfect for beta testing

- **Vercel Free Tier**: $0/month
  - 100GB bandwidth
  - Unlimited deployments
  - Perfect for small projects

**Total: $0/month for beta testing!**

## Next Steps After Beta

Once you have 10-20 active users:
- Upgrade Render to $7/month (no sleep, better performance)
- Consider custom domain ($12/year)
- Monitor usage and upgrade as needed
