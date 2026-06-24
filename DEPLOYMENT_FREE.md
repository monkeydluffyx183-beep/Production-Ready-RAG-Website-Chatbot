# 🚀 Free Deployment Guide for RAG Chatbot

This guide covers **100% free deployment** with no credit card required for hosting your RAG chatbot.

## ⚡ Quick Start: Deploy in 5 Minutes

### Step 1: Get Your Free Gemini API Key
```bash
# Visit https://aistudio.google.com/app/apikey
# Create a free API key (60 requests/minute, 1M tokens/day free)
```

### Step 2: Deploy Backend to Render (Free Tier)

#### 2.1 Prepare Your Repository
The backend is already configured with the following files:
- `backend/render.yaml` - Render configuration
- `backend/start.sh` - Startup script  
- `backend/requirements.txt` - Updated with gunicorn and spacy

#### 2.2 Deploy on Render
1. Go to [render.com](https://render.com) and sign up (free)
2. Click **"New +"** → **"Web Service"**
3. Connect your GitHub repository
4. Configure:
   - **Name**: `rag-chatbot-backend`
   - **Environment**: `Python 3`
   - **Build Command**: 
     ```bash
     pip install -r requirements.txt && python -m spacy download en_core_web_sm
     ```
   - **Start Command**: `./start.sh`
5. Add Environment Variables:
   ```
   GEMINI_API_KEY=your_actual_gemini_key
   JWT_SECRET=$(openssl rand -hex 32)
   CORS_ORIGINS=https://your-frontend.vercel.app
   DATABASE_URL=sqlite:///./data/chatbot.db
   CHROMA_PERSIST_DIR=./data/chroma_db
   ```
6. Add Persistent Disk:
   - Click **"Add Disk"**
   - Name: `chatbot-data`
   - Mount Path: `/app/data`
   - Size: `1 GB` (free tier limit)
7. Click **"Create Web Service"**

⏱️ Wait 5-10 minutes for the first deployment

### Step 3: Deploy Frontend to Vercel (Free Forever)

#### 3.1 Update Frontend Environment
Create `.env.production` in the frontend folder:
```env
NEXT_PUBLIC_API_URL=https://rag-chatbot-backend.onrender.com/api/v1
NEXT_PUBLIC_GEMINI_ENABLED=true
```

#### 3.2 Deploy to Vercel
1. Go to [vercel.com](https://vercel.com) and sign up (free)
2. Click **"Add New Project"**
3. Import your GitHub repository
4. Set **Root Directory** to `frontend`
5. Add environment variable:
   ```
   NEXT_PUBLIC_API_URL=https://rag-chatbot-backend.onrender.com/api/v1
   ```
6. Click **"Deploy"**

⏱️ Wait 2-3 minutes for deployment

### Step 4: Update CORS Settings
Once both are deployed, update the backend CORS environment variable on Render:
```
CORS_ORIGINS=https://your-frontend.vercel.app,http://localhost:3000
```

Redeploy the backend (Render auto-redeploys when env vars change).

### Step 5: Test Your Deployment
1. Visit your Vercel frontend URL
2. Enter a website URL (e.g., `https://example.com`)
3. Ask questions about the website!

---

## 🎯 Alternative Free Hosting Options

### Option A: Hugging Face Spaces (Completely Free)

**Best for**: Demos and prototypes

#### Setup Steps:
1. Go to [huggingface.co/spaces](https://huggingface.co/spaces)
2. Click **"Create new Space"**
3. Configure:
   - Space name: `rag-chatbot`
   - SDK: `Docker`
   - Visibility: `Public`
4. Create a `Dockerfile` in backend root:
   ```dockerfile
   FROM python:3.11-slim
   
   WORKDIR /app
   
   RUN apt-get update && apt-get install -y git curl \
       && rm -rf /var/lib/apt/lists/*
   
   COPY requirements.txt .
   RUN pip install --no-cache-dir -r requirements.txt
   RUN python -m spacy download en_core_web_sm
   
   COPY app/ ./app/
   COPY data/ ./data/ 2>/dev/null || true
   
   RUN mkdir -p ./data/chroma_db
   
   EXPOSE 7860
   
   CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860"]
   ```
5. Push to Hugging Face:
   ```bash
   pip install huggingface_hub
   huggingface-cli login
   
   # Clone your space
   git clone https://huggingface.co/spaces/YOUR_USERNAME/rag-chatbot
   cd rag-chatbot
   
   # Copy backend files
   cp -r ../backend/* ./
   
   git add .
   git commit -m "Initial deployment"
   git push
   ```

**Limitations**: 
- CPU only, 16GB RAM
- Sleeps after 48 hours of inactivity
- Public by default

### Option B: Fly.io (Always-Free VMs)

**Best for**: Always-on backend with more control

#### Setup Steps:
1. Install Fly CLI:
   ```bash
   curl -L https://fly.io/install.sh | sh
   fly auth login
   ```

2. Create and configure:
   ```bash
   cd backend
   fly launch --name rag-chatbot-backend
   ```

3. Update `fly.toml`:
   ```toml
   app = "rag-chatbot-backend"
   primary_region = "sjc"
   
   [build]
     dockerfile = "Dockerfile"
   
   [env]
     PORT = "8080"
     DATABASE_URL = "sqlite:///./data/chatbot.db"
     CHROMA_PERSIST_DIR = "./data/chroma_db"
   
   [mounts]
     source = "chatbot_data"
     destination = "/app/data"
   
   [[vm]]
     cpu_kind = "shared"
     cpus = 1
     memory_mb = 256
   
   [[services]]
     protocol = "tcp"
     internal_port = 8080
     
     [[services.ports]]
       port = 80
       handlers = ["http"]
     
     [[services.ports]]
       port = 443
       handlers = ["tls", "http"]
     
     [[services.http_checks]]
       interval = 10000
       grace_period = "5s"
       method = "get"
       path = "/health"
   ```

4. Deploy:
   ```bash
   fly secrets set GEMINI_API_KEY=your_key
   fly secrets set JWT_SECRET=$(openssl rand -hex 32)
   fly deploy
   ```

**Free Tier**: 3 shared-cpu-1x 256mb VMs (always-on)

### Option C: Railway (Free Credit)

**Best for**: Easy deployment with $5/month free credit

#### Setup Steps:
1. Go to [railway.app](https://railway.app)
2. Click **"New Project"** → **"Deploy from GitHub"**
3. Select your backend repo
4. Add variables:
   ```
   GEMINI_API_KEY=your_key
   JWT_SECRET=your_secret
   PORT=3000
   ```
5. Add Volume:
   - Click service → **"Volumes"** → **"New Volume"**
   - Mount Path: `/app/data`
   - Size: `1 GB`
6. Deploy!

**Free Tier**: $5 credit/month (~500 hours)

---

## 🔧 Optimization for Free Tiers

### 1. Reduce Memory Usage
Update `backend/app/config.py`:
```python
# Use smaller embedding model (80MB vs 400MB+)
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

# Limit concurrent workers
MAX_WORKERS = 2

# Reduce chunk size
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
```

### 2. Enable Caching
Add simple in-memory cache in `backend/app/cache.py`:
```python
from functools import lru_cache
import time

class SimpleCache:
    def __init__(self, ttl=300):
        self.cache = {}
        self.ttl = ttl
    
    @lru_cache(maxsize=100)
    def get(self, key):
        if key in self.cache:
            value, timestamp = self.cache[key]
            if time.time() - timestamp < self.ttl:
                return value
            del self.cache[key]
        return None
    
    def set(self, key, value):
        self.cache[key] = (value, time.time())

cache = SimpleCache(ttl=600)
```

### 3. Optimize Embedding Generation
Use batch processing in embeddings service:
```python
def generate_embeddings_batch(texts, batch_size=32):
    embeddings = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i+batch_size]
        batch_embeddings = embedding_model.encode(batch)
        embeddings.extend(batch_embeddings)
        # Free memory
        del batch
        del batch_embeddings
    return embeddings
```

### 4. Compress Context
Reduce chunk sizes for free tier:
```python
from langchain.text_splitter import RecursiveCharacterTextSplitter

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=300,  # Reduced from 500
    chunk_overlap=30,  # Reduced from 50
    length_function=len,
)
```

---

## 📊 Preventing Sleep on Free Tiers

### Render Free Tier (Sleeps after 15min inactivity)

#### Method 1: UptimeRobot (Recommended)
1. Go to [uptimerobot.com](https://uptimerobot.com)
2. Create free account
3. Add Monitor:
   - Type: HTTP(s)
   - URL: `https://your-app.onrender.com/health`
   - Interval: 5 minutes

#### Method 2: GitHub Actions Ping
Create `.github/workflows/keep-alive.yml`:
```yaml
name: Keep Render Alive

on:
  schedule:
    - cron: '*/4 * * * *'  # Every 4 minutes
  workflow_dispatch:

jobs:
  ping:
    runs-on: ubuntu-latest
    steps:
      - name: Ping Render
        run: curl https://your-app.onrender.com/health
```

#### Method 3: Cron-job.org
1. Go to [cron-job.org](https://cron-job.org)
2. Create free account
3. Add job:
   - URL: `https://your-app.onrender.com/health`
   - Interval: 4 minutes

---

## 🐛 Troubleshooting

### Issue: "Out of Memory" Error
**Solution**:
```bash
# Reduce worker count
export MAX_WORKERS=1

# Use smaller model
export EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
```

### Issue: "Timeout Error"
**Solution**:
Increase timeout in FastAPI routes or process in background tasks.

### Issue: "Disk Full"
**Solution**:
```bash
# Clean old chroma data (via SSH or redeploy)
rm -rf ./data/chroma_db/*
```

### Issue: "Cold Start Too Slow" (Render)
**Solutions**:
- Use uptime monitor to keep alive
- Pre-warm endpoints
- Reduce model size
- Upgrade to Render Standard ($7/mo) for always-on

### Issue: CORS Errors
**Solution**:
Ensure `CORS_ORIGINS` includes your frontend URL:
```
CORS_ORIGINS=https://your-frontend.vercel.app,http://localhost:3000
```

---

## 💰 Cost Breakdown (100% Free)

| Service | Cost | Limits |
|---------|------|--------|
| **Vercel** | $0 | 100GB/mo bandwidth, 100k requests/day |
| **Render** | $0 | 750 hrs/mo, 512MB RAM, sleeps after 15min |
| **Gemini API** | $0 | 60 req/min, 1M tokens/day |
| **Hugging Face** | $0 | CPU, 16GB RAM, public spaces |
| **Fly.io** | $0 | 3x 256MB VMs always-on |
| **SQLite + ChromaDB** | $0 | File-based, no limits |
| **Total** | **$0/month** | ✅ |

---

## 📈 Scaling Beyond Free Tier

When you outgrow free tiers:

| Upgrade | Cost | Benefit |
|---------|------|---------|
| Render Standard | $7/mo | Always-on, more RAM |
| Vercel Pro | $20/mo | More bandwidth, analytics |
| Pinecone Starter | $25/mo | Managed vector DB |
| Railway Pro | $5/mo | More compute hours |
| Fly.io Paid | $5+/mo | More VMs, resources |

---

## ✅ Deployment Checklist

- [ ] Get Gemini API Key: [aistudio.google.com](https://aistudio.google.com/app/apikey)
- [ ] Deploy backend on Render/HuggingFace/Fly.io
- [ ] Add persistent disk for database
- [ ] Set all environment variables
- [ ] Deploy frontend on Vercel
- [ ] Update frontend API URL
- [ ] Update backend CORS settings
- [ ] Test endpoint: `https://your-backend.com/health`
- [ ] Test full flow: ingest → chat
- [ ] Setup uptime monitor (prevent sleep)
- [ ] Test with small website first
- [ ] Monitor resource usage

---

## 🎉 Success!

Your RAG chatbot is now deployed **100% free**! 

Test it by:
1. Visiting your Vercel frontend URL
2. Entering a website URL (e.g., `https://example.com`)
3. Asking questions about the content
4. Checking citations and sources

**Remember**: Free tiers have limitations. For production use with heavy traffic, consider upgrading to paid plans.

---

## 📚 Additional Resources

- [Render Documentation](https://render.com/docs)
- [Vercel Documentation](https://vercel.com/docs)
- [Google Gemini API](https://ai.google.dev/docs)
- [LangChain Documentation](https://python.langchain.com/docs)
- [ChromaDB Documentation](https://docs.trychroma.com/)
