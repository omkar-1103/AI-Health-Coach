# Git & Streamlit Deployment Guide

## Git Commands (Start to End)

```bash
cd C:\AI_Health_Coach
```

```bash
git init
```

```bash
git add .
```

```bash
git commit -m "Initial commit"
```

```bash
git branch -M main
```

```bash
git remote add origin https://github.com/YOUR_USERNAME/ai-health-coach.git
```

```bash
git push -u origin main
```

---

## Streamlit Cloud Deployment

1. Open:
```
https://share.streamlit.io
```

2. Login with GitHub

3. Click **New App** → **Deploy from GitHub**

4. Fill details:
```
Repository: YOUR_USERNAME/ai-health-coach
Branch: main
Main file path: app.py
```

5. Click **Deploy**

---

## Add Secrets (API Key)

Go to:
```
Settings → Secrets
```

Add:
```toml
MISTRAL_API_KEY = "your_api_key_here"
```

Save changes and wait for restart.

---

## App URL

```
https://ai-health-coach.streamlit.app
```

---

## Interview One-Line

"I pushed my project to GitHub and deployed it on Streamlit Cloud using GitHub integration and secure secrets management."
