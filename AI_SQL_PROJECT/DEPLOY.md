# 🚀 Permanent Hosting Guide — AI SQL Assistant

Your app is now configured for **single-server deployment**: FastAPI serves
both the API and the frontend on **one port**. No separate frontend server needed.

---

## Option 1: Vercel (Easiest — Free Tier Available)

Your project is already configured with a `vercel.json` file designed specifically for Vercel deployment (serverless backend and static frontend).

1. Push your code to a **GitHub** repository:
   ```bash
   cd F:\AI_SQL_PROJECT
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/YOUR_USERNAME/ai-sql-assistant.git
   git push -u origin main
   ```

2. Go to [vercel.com](https://vercel.com) → Sign up (free) and log in.

3. Click **"Add New..."** → **"Project"** → Connect your GitHub repo.
   - Vercel will automatically read the `vercel.json` and configure the Python Serverless function and static hosting.
   - Leave the **Framework Preset** as "Other".

4. In the Vercel **Environment Variables** setup (before clicking Deploy), add:
   - `GROQ_API_KEY` set to your real API key.

5. Click **Deploy**. Vercel will provide you with a permanent URL for your AI SQL Assistant!

---

## Option 2: Render.com (Simple Alternative)

1. Push your code to a **GitHub** repository:
   ```bash
   cd F:\AI_SQL_PROJECT
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/YOUR_USERNAME/ai-sql-assistant.git
   git push -u origin main
   ```

2. Go to [render.com](https://render.com) → Sign up (free).

3. Click **"New +"** → **"Blueprint"** → Connect your GitHub repo.
   - Render will auto-detect the `render.yaml` file and set everything up.

4. In the Render dashboard, go to your service → **Environment** tab →
   Set `GROQ_API_KEY` to your real API key.

5. That's it! Render gives you a permanent URL like:
   `https://ai-sql-assistant.onrender.com`

---

## Option 2: Railway.app (Simple — $5/month after trial)

1. Push your code to GitHub (same steps as above).

2. Go to [railway.app](https://railway.app) → Sign up.

3. Click **"New Project"** → **"Deploy from GitHub Repo"** → Select your repo.
   - Railway auto-detects the `railway.toml` and `Dockerfile`.

4. In the Railway dashboard → **Variables** tab →
   Add `GROQ_API_KEY` with your real key.

5. Railway gives you a permanent URL like:
   `https://ai-sql-assistant.up.railway.app`

---

## Option 3: Docker (Self-Hosted on Any VPS — Full Control)

If you have a VPS (DigitalOcean, AWS EC2, Linode, etc.):

1. Install Docker on the server.

2. Copy or clone your project to the server.

3. Build and run:
   ```bash
   cd AI_SQL_PROJECT
   docker build -t ai-sql-assistant .
   docker run -d -p 80:8000 -e GROQ_API_KEY=sk-ant-your-key ai-sql-assistant
   ```

4. Your app is now live on `http://YOUR_SERVER_IP`!

5. (Optional) Point a domain name to your server IP and add HTTPS with
   [Caddy](https://caddyserver.com) or Nginx + Let's Encrypt.

---

## Option 4: Run 24/7 on Your Own Windows PC

If you want to keep it running permanently on your local machine:

### A. Using Task Scheduler (Simplest)
1. Open **Task Scheduler** (search in Start Menu).
2. Click **"Create Basic Task"**.
3. Name it: `AI SQL Assistant`
4. Trigger: **"When the computer starts"**
5. Action: **"Start a program"**
   - Program: `python`
   - Arguments: `-m uvicorn main:app --host 0.0.0.0 --port 8000`
   - Start in: `F:\AI_SQL_PROJECT\backend`
6. Finish. The app will now auto-start whenever your PC boots.

### B. Using NSSM (Run as a Windows Service)
1. Download [NSSM](https://nssm.cc/download) (the Non-Sucking Service Manager).
2. Open an **Admin Command Prompt** and run:
   ```cmd
   nssm install AISQLAssistant
   ```
3. In the GUI that pops up:
   - **Path**: `C:\Users\USER\AppData\Local\Programs\Python\Python313\python.exe`
   - **Arguments**: `-m uvicorn main:app --host 0.0.0.0 --port 8000`
   - **Startup Directory**: `F:\AI_SQL_PROJECT\backend`
4. Click **"Install Service"**, then start it:
   ```cmd
   nssm start AISQLAssistant
   ```
5. Your app is now a permanent Windows service! It auto-starts, auto-restarts
   on crash, and runs even when you're not logged in.

---

## Important Notes

- **API Key**: For all options, set the `GROQ_API_KEY` environment
  variable to your real Groq API key. Without it, the app runs in
  "Mock Mode" (works but returns hardcoded SQL).

- **Database**: The current setup uses SQLite (a local file). For production
  with multiple users, consider swapping to PostgreSQL — the `db.py` layer
  was designed to make this easy.

- **Security**: Before exposing publicly, update the CORS `allow_origins`
  in `main.py` from `["*"]` to your specific domain.
