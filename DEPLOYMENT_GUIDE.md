# 📱 Mobile App & 🌐 100% Free Cloud Deployment Guide

This guide covers step-by-step instructions to:
1. **Deploy your Encatesus AI Chat app online completely for FREE** with a permanent public URL and free SSL (HTTPS).
2. **Install & Run as a Mobile App** on Android and iOS (Zero cost, no developer fee required).

---

## 🌐 Part 1: Deploying to the Internet for FREE

### Option A: Deploy on Render.com (Recommended — 100% Free Tier)

**Render** gives you free web hosting with automated HTTPS and GitHub integration:

1. **Push your code to GitHub**:
   ```powershell
   git init
   git add .
   git commit -m "Deploy Encatesus AI"
   git remote add origin https://github.com/<your-username>/encatesus-chat.git
   git push -u origin main
   ```
2. **Sign up / Log in to [Render.com](https://render.com/)** (Free).
3. Click **"New +"** ➡️ **"Web Service"** ➡️ Select your GitHub repository.
4. Set the configuration:
   - **Name**: `encatesus-ai`
   - **Environment**: `Python`
   - **Build Command**: `pip install -r backend/requirements.txt`
   - **Start Command**: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
   - **Instance Type**: `Free`
5. Under **"Environment Variables"**, add:
   - `GEMINI_API_KEY` = `your_gemini_api_key_here` (Get your free key from https://aistudio.google.com/)
6. Click **"Create Web Service"**!
7. In ~2 minutes, your web app will be live at:
   👉 `https://encatesus-ai.onrender.com`

---

### Option B: Deploy on Hugging Face Spaces (100% Free, Continuous Uptime)

1. Go to **[Hugging Face](https://huggingface.co/)** and create a free account.
2. Click **"New Space"**.
3. Space Name: `encatesus-ai-chat`
4. Space SDK: **Docker** (Blank) or **Gradio/FastAPI**.
5. Set Space Visibility to **Public**.
6. In the Settings tab under **Secrets**, add `GEMINI_API_KEY`.
7. Push the repository or upload your files.
8. Your app is instantly live at `https://<username>-encatesus-ai-chat.hf.space`!

---

### Option C: Instant Free Temporary/Permanent Tunnel (ngrok / Cloudflare Tunnel)

If you want to access your local server immediately from your phone without uploading anywhere:

Using **Cloudflare Tunnel** (100% Free, no signup required):
```powershell
# In PowerShell:
winget install Cloudflare.cloudflared
cloudflared tunnel --url http://localhost:8000
```
*Cloudflare will print a free public HTTPS link (e.g., `https://random-subdomain.trycloudflare.com`) accessible from any smartphone in the world.*

---

## 📱 Part 2: Creating the Mobile App

We have configured **Encatesus** with two mobile packaging solutions:

### Method 1: Instant PWA Mobile App (Android & iOS — Zero Setup Needed)

Once your app is online (or via Cloudflare tunnel / local Wi-Fi):

#### On Android (Google Chrome):
1. Open your live URL (e.g. `https://encatesus-ai.onrender.com`) in Chrome.
2. Tap the **three dots menu (⋮)** in the top right corner.
3. Tap **"Install app"** or **"Add to Home screen"**.
4. The **Encatesus AI** app icon will appear directly in your Android App Drawer and Home Screen.
5. It opens in a standalone, fullscreen window without any browser navigation bar — just like a native app from the Play Store!

#### On iPhone / iPad (Safari):
1. Open the URL in **Safari**.
2. Tap the **Share button (square with arrow up)** at the bottom.
3. Scroll down and tap **"Add to Home Screen"**.
4. Tap **Add**. You now have the Encatesus app on your iOS home screen with custom icon and splash screen.

---

### Method 2: Build a Native Android APK (Using Capacitor / Bubblewrap)

If you want a standalone `.apk` installation file:

1. **Install Node.js & Capacitor CLI** (Free):
   ```powershell
   npm install -g @capacitor/cli @capacitor/core @capacitor/android
   ```
2. **Add Android Platform**:
   ```powershell
   npx cap add android
   ```
3. **Build APK**:
   ```powershell
   npx cap open android
   ```
   *(Opens Android Studio where you can click **Build ➡️ Build Bundle(s) / APK(s) ➡️ Build APK(s)**)*.
   Or use Google's free **Bubblewrap** CLI to generate an APK from your PWA URL in 60 seconds:
   ```powershell
   npx @bubblewrap/cli init --manifest=https://your-deployed-url.com/manifest.json
   npx @bubblewrap/cli build
   ```
