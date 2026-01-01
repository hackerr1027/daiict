# 🚀 Complete Deployment Guide - Render + Vercel

This guide will walk you through deploying your TechSprint application to production using **free** hosting services.

## Prerequisites

- GitHub account
- Render account (sign up at [render.com](https://render.com))
- Vercel account (sign up at [vercel.com](https://vercel.com))

---

## Step 1: Clean Up Repository

Your repository has some virtual environment files that shouldn't be in version control. Let's remove them:

```bash
cd c:\Users\admin\Desktop\DAIICT-25dec\TechSprint-main

# Remove virtual environment files from Git tracking
git rm --cached Activate.ps1 activate activate.bat deactivate.bat
git rm --cached -r _distutils_hack annotated* anyio extras
git rm --cached *.exe

# Commit the cleanup
git add .gitignore
git commit -m "Clean up virtual environment files and fix deployment config"
```

---

## Step 2: Push to GitHub

If you haven't already pushed to GitHub:

```bash
# If repository already exists on GitHub
git push

# If this is a new repository
git remote add origin https://github.com/hackerr1027/TechSprint.git
git branch -M main
git push -u origin main
```

---

## Step 3: Deploy Backend to Render

### 3.1 Create Web Service

1. Go to [render.com](https://render.com) and sign in
2. Click **"New +"** → **"Web Service"**
3. Connect your GitHub repository: `hackerr1027/TechSprint`
4. Render will auto-detect the `render.yaml` configuration

### 3.2 Configure Environment Variables

In the Render dashboard, add this environment variable:

- **Key**: `FRONTEND_URL`
- **Value**: `https://*.vercel.app` (we'll update this after Vercel deployment)

Optional (if using Google Gemini API):
- **Key**: `GOOGLE_API_KEY`
- **Value**: Your API key from [Google AI Studio](https://makersuite.google.com/app/apikey)

### 3.3 Deploy

1. Click **"Create Web Service"**
2. Wait 3-5 minutes for deployment
3. **Copy your backend URL**: `https://techsprint-backend-XXXX.onrender.com`

### 3.4 Test Backend

Visit: `https://techsprint-backend-XXXX.onrender.com/health`

You should see:
```json
{
  "status": "healthy",
  "components": { ... }
}
```

---

## Step 4: Deploy Frontend to Vercel

### 4.1 Create New Project

1. Go to [vercel.com](https://vercel.com) and sign in
2. Click **"Add New..."** → **"Project"**
3. Import your GitHub repository: `hackerr1027/TechSprint`

### 4.2 Configure Build Settings

Vercel will auto-detect Vite. Verify these settings:

- **Framework Preset**: Vite
- **Root Directory**: `./`
- **Build Command**: `npm run build` (auto-detected)
- **Output Directory**: `dist` (auto-detected)

### 4.3 Add Environment Variable

Click **"Environment Variables"** and add:

- **Key**: `VITE_API_URL`
- **Value**: `https://techsprint-backend-XXXX.onrender.com` (your Render URL from Step 3)

### 4.4 Deploy

1. Click **"Deploy"**
2. Wait 1-3 minutes
3. **Copy your frontend URL**: `https://techsprint-XXXX.vercel.app`

---

## Step 5: Update Backend CORS (Optional)

For better security, update the Render environment variable:

1. Go to your Render dashboard
2. Navigate to your web service
3. Go to **"Environment"**
4. Update `FRONTEND_URL` to your exact Vercel URL: `https://techsprint-XXXX.vercel.app`
5. Save changes (Render will auto-redeploy)

---

## Step 6: Test Your Deployment

### 6.1 Visit Your App

Open your Vercel URL: `https://techsprint-XXXX.vercel.app`

### 6.2 Wait for Backend Wake-Up

⚠️ **Important**: Render free tier sleeps after 15 minutes of inactivity. The first request takes ~30 seconds to wake up.

### 6.3 Check Connection Status

Look for the **"Backend Connected"** indicator in the top-right corner. It should turn green after ~30 seconds.

### 6.4 Test Infrastructure Generation

1. Enter a prompt like: `"Create a VPC with EC2 and RDS database"`
2. Click **"Generate Infrastructure"**
3. Verify:
   - Mermaid diagram appears
   - Terraform code is generated
   - Security warnings are displayed

---

## Troubleshooting

### Backend Not Connected

**Symptom**: Red "Backend Disconnected" indicator

**Solutions**:
- Wait 30 seconds for Render to wake up
- Check backend health: `https://your-backend.onrender.com/health`
- Verify `VITE_API_URL` environment variable in Vercel

### CORS Errors in Browser Console

**Symptom**: `Access-Control-Allow-Origin` errors

**Solutions**:
- Verify `FRONTEND_URL` is set correctly in Render
- Use wildcard `https://*.vercel.app` to allow all Vercel deployments
- Check browser console for exact error message

### Build Fails on Vercel

**Symptom**: Deployment fails during build

**Solutions**:
- Check build logs in Vercel dashboard
- Verify `VITE_API_URL` environment variable is set
- Try rebuilding: Deployments → ⋯ → Redeploy

### 404 on Page Refresh

**Symptom**: Refreshing any page shows 404

**Solution**: Already fixed in `vercel.json` with SPA rewrites

---

## Your Deployment URLs

Fill these in after deployment:

- **Frontend**: `https://________________.vercel.app`
- **Backend**: `https://________________.onrender.com`
- **API Docs**: `https://________________.onrender.com/docs`

---

## Free Tier Limits

### Render
- 750 hours/month (enough for 1 service)
- Sleeps after 15 minutes of inactivity
- 30-second cold start

### Vercel
- Unlimited deployments
- 100GB bandwidth/month
- Automatic HTTPS

**Total Cost**: $0/month 🎉

---

## Keeping Backend Awake (Optional)

Use [UptimeRobot](https://uptimerobot.com) (free) to ping your backend every 5 minutes:

1. Sign up at uptimerobot.com
2. Add new monitor
3. URL: `https://your-backend.onrender.com/health`
4. Interval: 5 minutes

This prevents the backend from sleeping.

---

## Auto-Deployment

Both platforms auto-deploy when you push to GitHub:

```bash
# Make changes
git add .
git commit -m "Update feature"
git push

# Render and Vercel will automatically deploy the changes
```

---

## Next Steps

1. ✅ Deploy backend to Render
2. ✅ Deploy frontend to Vercel
3. ✅ Test the application
4. 🎯 Share your live URL!

---

## Support

If you encounter issues:

1. Check the troubleshooting section above
2. Review deployment logs in Render/Vercel dashboards
3. Verify environment variables are set correctly
4. Test backend health endpoint directly

**Your application is now live!** 🚀
