# 🚀 Free Deployment Guide for RAG Chatbot

This guide covers **100% free deployment** options with no credit card required.

## ⚠️ Important Limitations of Free Tiers

| Platform | Limitations |
|----------|-------------|
| **Render** | Web services sleep after 15min inactivity, 750 hours/month limit |
| **Vercel** | 100GB bandwidth/month, serverless function timeout 10s |
| **Railway** | $5 free credit/month (≈500 hours), then pauses |
| **Hugging Face Spaces** | CPU only, 16GB RAM limit, sleeps after inactivity |
| **Fly.io** | 3 shared-cpu-1x 256mb VMs free (always-on) |

## 🎯 Recommended Free Stack

```
Frontend: Vercel (Free Forever)
Backend: Render Free Tier or Hugging Face Spaces
Database: SQLite (built-in) + ChromaDB (file-based)
LLM: Google Gemini Free Tier (60 requests/minute)
Embeddings: sentence-transformers (local, free)
```

---

## Option 1: Vercel + Render (Recommended)

### Step 1: Prepare Backend for Render

#### 1.1 Create `render.yaml`

```yaml
services:
  - type: web
    name: rag-chatbot-backend
    env: python
    buildCommand: |
      pip install -r requirements.txt
      python -m spacy download en_core_web_sm
    startCommand: uvicorn app.main:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: PYTHON_VERSION
        value: 3.11.0
      - key: DATABASE_URL
        value: sqlite:///./data/chatbot.db
      - key: CHROMA_PERSIST_DIR
        value: ./data/chroma_db
      - key: GEMINI_API_KEY
        sync: false
      - key: JWT_SECRET
        generateValue: true
      - key: CORS_ORIGINS
        value: https://your-frontend.vercel.app
    disk:
      name: chatbot-data
      mountPath: /data
      sizeGB: 1
```

#### 1.2 Update `requirements.txt` for Render

Add these lines to your existing `requirements.txt`:

```txt
gunicorn==21.2.0
uvicorn[standard]==0.27.0
```

#### 1.3 Create `start.sh` for Render

```bash
#!/bin/bash
mkdir -p ./data/chroma_db
python -m spacy download en_core_web_sm
exec gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT
```

Make it executable:
```bash
chmod +x start.sh
```

### Step 2: Deploy Backend on Render

1. **Sign up**: Go to [render.com](https://render.com) and create a free account
2. **New Web Service**: Click "New +" → "Web Service"
3. **Connect Repository**: Connect your GitHub repo
4. **Configure**:
   - Name: `rag-chatbot-backend`
   - Environment: `Python 3`
   - Build Command: `pip install -r requirements.txt && python -m spacy download en_core_web_sm`
   - Start Command: `./start.sh`
5. **Add Environment Variables**:
   ```
   GEMINI_API_KEY=your_actual_key
   JWT_SECRET=your_secret_key_here
   CORS_ORIGINS=https://your-frontend.vercel.app
   DATABASE_URL=sqlite:///./data/chatbot.db
   CHROMA_PERSIST_DIR=./data/chroma_db
   ```
6. **Add Disk**: 
   - Click "Add Disk"
   - Name: `chatbot-data`
   - Mount Path: `/data`
   - Size: `1 GB` (free tier)
7. **Deploy**: Click "Create Web Service"

⏱️ **Wait 5-10 minutes** for first deployment

### Step 3: Deploy Frontend on Vercel

#### 3.1 Update Frontend Environment

Create `.env.production` in frontend folder:

```env
NEXT_PUBLIC_API_URL=https://rag-chatbot-backend.onrender.com/api/v1
NEXT_PUBLIC_GEMINI_ENABLED=true
```

#### 3.2 Deploy to Vercel

1. **Install Vercel CLI** (optional):
   ```bash
   npm i -g vercel
   ```

2. **Deploy via CLI**:
   ```bash
   cd frontend
   vercel login
   vercel --prod
   ```

3. **Or Deploy via Web**:
   - Go to [vercel.com](https://vercel.com)
   - Click "Add New Project"
   - Import your GitHub repository
   - Set root directory to `frontend`
   - Add environment variables:
     ```
     NEXT_PUBLIC_API_URL=https://rag-chatbot-backend.onrender.com/api/v1
     ```
   - Click "Deploy"

### Step 4: Update CORS Settings

In your backend code, update CORS origins:

```python
# In app/main.py
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## Option 2: Hugging Face Spaces (Completely Free)

### Step 1: Create Space

1. Go to [huggingface.co/spaces](https://huggingface.co/spaces)
2. Click "Create new Space"
3. Configure:
   - Space name: `rag-chatbot`
   - License: `MIT`
   - SDK: `Docker`
   - Visibility: `Public`

### Step 2: Create Dockerfile for HF Spaces

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN python -m spacy download en_core_web_sm

# Copy application
COPY app/ ./app/
COPY data/ ./data/

# Create data directories
RUN mkdir -p ./data/chroma_db

# Expose port
EXPOSE 7860

# Run with Gradio proxy compatibility
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860"]
```

### Step 3: Update Backend for HF Spaces

Create `app/hf_config.py`:

```python
import os

# Hugging Face Spaces specific config
HF_SPACE = os.getenv("SYSTEM", "") == "spaces"
PORT = int(os.getenv("PORT", 7860))
HOST = "0.0.0.0" if HF_SPACE else "127.0.0.1"

# Disable auth for demo mode (optional)
DEMO_MODE = os.getenv("DEMO_MODE", "false").lower() == "true"
```

Update `app/main.py`:

```python
from app.hf_config import HF_SPACE, PORT, HOST, DEMO_MODE

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=HOST,
        port=PORT,
        reload=False if HF_SPACE else True
    )
```

### Step 4: Push to Hugging Face

```bash
# Install huggingface-cli
pip install huggingface_hub

# Login
huggingface-cli login

# Clone your space
git clone https://huggingface.co/spaces/YOUR_USERNAME/rag-chatbot
cd rag-chatbot

# Copy your files
cp -r ../your-project/app ./
cp -r ../your-project/data ./
cp Dockerfile ./
cp requirements.txt ./

# Commit and push
git add .
git commit -m "Initial deployment"
git push
```

---

## Option 3: Fly.io (Always-Free VMs)

### Step 1: Install Fly CLI

```bash
curl -L https://fly.io/install.sh | sh
fly auth login
```

### Step 2: Create Fly App

```bash
cd backend
fly launch --name rag-chatbot-backend
```

### Step 3: Configure `fly.toml`

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

### Step 4: Create Dockerfile for Fly

```dockerfile
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y git curl
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN python -m spacy download en_core_web_sm

COPY . .
RUN mkdir -p ./data/chroma_db

EXPOSE 8080

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
```

### Step 5: Deploy

```bash
fly secrets set GEMINI_API_KEY=your_key
fly secrets set JWT_SECRET=your_secret
fly deploy
```

---

## Option 4: Railway (Free Credit)

### Quick Deploy

1. Go to [railway.app](https://railway.app)
2. Click "New Project" → "Deploy from GitHub"
3. Select your backend repo
4. Add variables:
   ```
   GEMINI_API_KEY=your_key
   JWT_SECRET=your_secret
   PORT=3000
   ```
5. Add Volume:
   - Click your service → "Volumes" → "New Volume"
   - Mount Path: `/app/data`
   - Size: `1 GB`
6. Deploy!

---

## 🔧 Optimization for Free Tiers

### 1. Reduce Memory Usage

Update `app/config.py`:

```python
# Use smaller embedding model
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"  # 80MB vs 400MB+

# Limit concurrent workers
MAX_WORKERS = 2

# Reduce chunk size
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
```

### 2. Enable Caching

Add Redis alternative (in-memory cache):

```python
# app/cache.py
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

```python
# Use batch processing
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

```python
from langchain.text_splitter import RecursiveCharacterTextSplitter

# Smaller chunks for free tier
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=300,  # Reduced from 500
    chunk_overlap=30,  # Reduced from 50
    length_function=len,
)
```

---

## 📊 Monitoring & Keeping Alive

### Prevent Sleep (Render Free Tier)

Create a simple uptime monitor:

#### Using UptimeRobot (Free)

1. Go to [uptimerobot.com](https://uptimerobot.com)
2. Create account
3. Add Monitor:
   - Type: HTTP(s)
   - URL: `https://your-app.onrender.com/health`
   - Interval: 5 minutes

#### Custom Ping Script

```python
# scripts/keep_alive.py
import requests
import time
import os

URL = os.getenv("BACKEND_URL", "https://your-app.onrender.com")

while True:
    try:
        requests.get(f"{URL}/health", timeout=5)
        print(f"Pinged {URL} at {time.strftime('%X')}")
    except Exception as e:
        print(f"Error: {e}")
    time.sleep(240)  # Every 4 minutes
```

Run on free scheduler:
- GitHub Actions (free 2000 min/month)
- Cron-job.org (free 10 minute intervals)

---

## 🎯 Complete Free Deployment Checklist

- [ ] Get Gemini API Key (free): [aistudio.google.com](https://aistudio.google.com/app/apikey)
- [ ] Deploy backend on Render/HuggingFace
- [ ] Add persistent disk for database
- [ ] Set all environment variables
- [ ] Deploy frontend on Vercel
- [ ] Update frontend API URL
- [ ] Test endpoint: `https://your-backend.com/health`
- [ ] Test full flow: ingest → chat
- [ ] Setup uptime monitor (prevent sleep)
- [ ] Test with small website first
- [ ] Monitor resource usage

---

## 🐛 Troubleshooting Free Deployments

### Issue: "Out of Memory"

**Solution:**
```bash
# Reduce worker count
export MAX_WORKERS=1

# Use smaller model
export EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
```

### Issue: "Timeout Error"

**Solution:**
```python
# Increase timeout in FastAPI
@app.post("/ingest", timeout=300)
async def ingest_website(...):
    # Process in background
    pass
```

### Issue: "Disk Full"

**Solution:**
```bash
# Clean old data
rm -rf ./data/chroma_db/*
# Or implement rotation
```

### Issue: "Cold Start Too Slow"

**Solution:**
- Use uptime monitor to keep alive
- Pre-warm endpoints
- Reduce model size

---

## 💰 Cost Breakdown (100% Free)

| Service | Cost | Limits |
|---------|------|--------|
| **Vercel** | $0 | 100GB/mo, 100k requests/day |
| **Render** | $0 | 750 hrs/mo, 512MB RAM |
| **Gemini API** | $0 | 60 req/min, 1M tokens/day |
| **Hugging Face** | $0 | CPU, 16GB RAM |
| **SQLite + ChromaDB** | $0 | File-based, no limits |
| **Total** | **$0/month** | ✅ |

---

## 🚀 Quick Start Commands

```bash
# 1. Clone and setup
git clone https://github.com/yourusername/rag-chatbot.git
cd rag-chatbot

# 2. Backend (Render)
cd backend
echo "GEMINI_API_KEY=your_key" >> .env
echo "JWT_SECRET=$(openssl rand -hex 32)" >> .env
git add . && git commit -m "Ready for Render"
git push

# 3. Frontend (Vercel)
cd ../frontend
echo "NEXT_PUBLIC_API_URL=https://your-app.onrender.com/api/v1" >> .env.production
npm run build
vercel --prod

# 4. Test
curl https://your-app.onrender.com/health
```

---

## 📈 Scaling Beyond Free Tier

When you outgrow free tiers:

| Upgrade | Cost | Benefit |
|---------|------|---------|
| Render Standard | $7/mo | Always-on, more RAM |
| Vercel Pro | $20/mo | More bandwidth, analytics |
| Pinecone Starter | $25/mo | Managed vector DB |
| Railway Pro | $5/mo | More compute hours |

---

## 🎉 Success!

Your RAG chatbot is now deployed **100% free**! 

Test it by:
1. Visiting your Vercel frontend URL
2. Entering a website URL
3. Asking questions
4. Checking citations

**Remember**: Free tiers have limitations. For production use with heavy traffic, consider upgrading to paid plans.
