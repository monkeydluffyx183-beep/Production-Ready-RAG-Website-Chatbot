# RAG Website Chatbot - Deployment Guide

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Local Development Setup](#local-development-setup)
3. [Docker Deployment](#docker-deployment)
4. [Render Deployment](#render-deployment)
5. [Vercel Deployment (Frontend)](#vercel-deployment-frontend)
6. [Railway Deployment (Backend)](#railway-deployment-backend)
7. [Environment Variables](#environment-variables)
8. [Production Checklist](#production-checklist)
9. [Troubleshooting](#troubleshooting)

---

## Prerequisites

Before deploying, ensure you have:

- **Node.js** v18+ and npm/yarn
- **Python** v3.11+
- **Docker** and Docker Compose (for local/containerized deployment)
- **Git** account (GitHub/GitLab)
- API Keys:
  - Google Gemini API Key OR OpenAI API Key
  - (Optional) Render/Vercel/Railway accounts

### Get Your API Keys

1. **Google Gemini API**: https://makersuite.google.com/app/apikey
2. **OpenAI API**: https://platform.openai.com/api-keys

---

## Local Development Setup

### Quick Start

```bash
# Clone the repository
cd /workspace/rag-chatbot

# Setup Backend
cd backend
cp .env.example .env
# Edit .env and add your API keys
nano .env

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run backend server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# In a new terminal, setup Frontend
cd ../frontend
npm install

# Create .env.local
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local

# Run frontend dev server
npm run dev
```

Access the application at:
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

---

## Docker Deployment

### Using Docker Compose (Recommended for Local/Testing)

The project includes a complete Docker setup for running all services.

#### 1. Create docker-compose.yml

```yaml
version: '3.8'

services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: rag-backend
    env_file: ./backend/.env
    volumes:
      - chroma_data:/app/chroma_data
      - ./backend:/app
    ports:
      - "8000:8000"
    networks:
      - rag-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
      args:
        - NEXT_PUBLIC_API_URL=http://backend:8000
    container_name: rag-frontend
    ports:
      - "3000:3000"
    depends_on:
      backend:
        condition: service_healthy
    networks:
      - rag-network
    restart: unless-stopped

volumes:
  chroma_data:
    driver: local

networks:
  rag-network:
    driver: bridge
```

#### 2. Create Backend Dockerfile

```dockerfile
# backend/Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### 3. Create Frontend Dockerfile

```dockerfile
# frontend/Dockerfile
FROM node:18-alpine AS base

# Dependencies stage
FROM base AS deps
RUN apk add --no-cache libc6-compat
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm ci

# Builder stage
FROM base AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
ENV NEXT_TELEMETRY_DISABLED 1
RUN npm run build

# Runner stage
FROM base AS runner
WORKDIR /app
ENV NODE_ENV production
ENV NEXT_TELEMETRY_DISABLED 1

RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs
EXPOSE 3000
ENV PORT 3000
ENV HOSTNAME "0.0.0.0"

CMD ["node", "server.js"]
```

#### 4. Update next.config.js for Docker

```javascript
// frontend/next.config.js
/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
  experimental: {
    outputFileTracingRoot: undefined,
  },
}

module.exports = nextConfig
```

#### 5. Build and Run

```bash
# Build images
docker-compose build

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Stop and remove volumes (clears data)
docker-compose down -v
```

---

## Render Deployment

### Backend Deployment on Render

1. **Push to GitHub**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin <your-repo-url>
   git push -u origin main
   ```

2. **Create Web Service on Render**
   - Go to https://render.com
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Select the `backend` folder as root directory

3. **Configure Build & Start**
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Port**: 8000 (or use `$PORT` environment variable)

4. **Set Environment Variables**
   
   In Render Dashboard → Environment:
   ```
   LLM_PROVIDER=gemini
   GEMINI_API_KEY=your_actual_gemini_key
   LLM_MODEL=gemini-2.5-flash
   EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
   MAX_PAGES=50
   REQUEST_TIMEOUT=15
   CHROMA_PERSIST_DIR=/data/chroma_data
   DATABASE_URL=postgresql://user:pass@host:5432/dbname
   JWT_SECRET_KEY=your_super_secret_jwt_key_min_32_chars
   ACCESS_TOKEN_EXPIRE_MINUTES=30
   ```

5. **Add Persistent Disk** (for ChromaDB)
   - Go to your service → Disks
   - Add Disk: `/data`, Size: 1GB minimum

6. **Deploy**
   - Click "Create Web Service"
   - Wait for deployment (5-10 minutes)
   - Note your backend URL: `https://your-app-name.onrender.com`

### Frontend Deployment on Vercel

1. **Go to Vercel**
   - Visit https://vercel.com
   - Click "Add New Project"
   - Import your GitHub repository

2. **Configure Project**
   - **Framework Preset**: Next.js
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `.next`

3. **Set Environment Variables**
   ```
   NEXT_PUBLIC_API_URL=https://your-backend-url.onrender.com
   ```

4. **Deploy**
   - Click "Deploy"
   - Wait for build completion
   - Your app is live at: `https://your-app-name.vercel.app`

---

## Railway Deployment (Alternative Backend)

Railway offers easier PostgreSQL integration and often better performance than Render.

### Steps:

1. **Install Railway CLI**
   ```bash
   npm i -g @railway/cli
   railway login
   ```

2. **Initialize Project**
   ```bash
   cd backend
   railway init
   railway up
   ```

3. **Add PostgreSQL (for user data)**
   ```bash
   railway add postgresql
   railway link
   ```

4. **Set Environment Variables**
   ```bash
   railway variables set \
     LLM_PROVIDER=gemini \
     GEMINI_API_KEY=your_key \
     DATABASE_URL=$DATABASE_URL
   ```

5. **Deploy**
   ```bash
   railway up
   ```

---

## Environment Variables

### Backend (.env)

```bash
# LLM Configuration
LLM_PROVIDER=gemini              # gemini | openai
GEMINI_API_KEY=your_gemini_key   # Required if using Gemini
OPENAI_API_KEY=your_openai_key   # Required if using OpenAI
LLM_MODEL=gemini-2.5-flash       # Model name

# Embeddings
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2

# Crawler Settings
MAX_PAGES=50
REQUEST_TIMEOUT=15
USER_AGENT=Mozilla/5.0 (compatible; RAGBot/1.0)

# Vector Storage
CHROMA_PERSIST_DIR=./chroma_data

# Database (PostgreSQL for production)
DATABASE_URL=postgresql://user:password@localhost:5432/ragchatdb

# Authentication
JWT_SECRET_KEY=your-super-secret-key-at-least-32-characters-long
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# CORS (comma-separated origins)
ALLOWED_ORIGINS=http://localhost:3000,https://yourdomain.com

# Rate Limiting
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=3600

# Logging
LOG_LEVEL=INFO
```

### Frontend (.env.local)

```bash
# API Configuration
NEXT_PUBLIC_API_URL=http://localhost:8000

# Optional: Analytics
NEXT_PUBLIC_GA_ID=G-XXXXXXXXXX
```

---

## Production Checklist

### Security
- [ ] Change all default passwords and secrets
- [ ] Enable HTTPS (automatic on Vercel/Render)
- [ ] Configure CORS properly for production domain
- [ ] Set secure cookie flags
- [ ] Implement rate limiting
- [ ] Add input validation and sanitization
- [ ] Enable SQL injection protection (using ORM)

### Performance
- [ ] Enable response compression
- [ ] Configure CDN for static assets
- [ ] Optimize database queries with indexes
- [ ] Implement caching (Redis recommended)
- [ ] Use connection pooling for database
- [ ] Enable HTTP/2

### Monitoring
- [ ] Set up error tracking (Sentry)
- [ ] Configure logging aggregation
- [ ] Add uptime monitoring (UptimeRobot)
- [ ] Set up alerts for critical errors
- [ ] Monitor API response times
- [ ] Track vector search latency

### Scalability
- [ ] Use managed database (Supabase/Neon)
- [ ] Consider managed vector DB (Pinecone/Weaviate)
- [ ] Implement horizontal scaling
- [ ] Add load balancer for multiple instances
- [ ] Use object storage for files (S3)

### Backup & Recovery
- [ ] Schedule daily database backups
- [ ] Backup ChromaDB data regularly
- [ ] Test restore procedures
- [ ] Document disaster recovery plan

---

## Troubleshooting

### Common Issues

#### 1. Backend Won't Start
```bash
# Check logs
docker-compose logs backend

# Verify environment variables
docker-compose exec backend env | grep -E "API_KEY|SECRET"

# Test database connection
docker-compose exec backend python -c "from app.core.database import engine; print(engine.url)"
```

#### 2. ChromaDB Errors
```bash
# Clear ChromaDB data (development only!)
docker-compose down -v
docker-compose up -d

# Check disk space
df -h

# Verify permissions
ls -la /app/chroma_data
```

#### 3. Frontend Can't Connect to Backend
```bash
# Check API URL
echo $NEXT_PUBLIC_API_URL

# Test backend from browser
curl https://your-backend-url.com/health

# Check CORS settings in backend
# Ensure ALLOWED_ORIGINS includes your frontend URL
```

#### 4. Slow Response Times
- Reduce `MAX_PAGES` during indexing
- Decrease `top_k` retrieval parameter
- Use smaller embedding models
- Implement caching for frequent queries
- Consider upgrading hosting plan

#### 5. Memory Issues
```bash
# Reduce batch size in embeddings
# Limit concurrent workers in crawler
# Use CPU instead of GPU for embeddings (cheaper)
```

### Performance Optimization Tips

1. **Embedding Caching**
   ```python
   from functools import lru_cache
   
   @lru_cache(maxsize=1000)
   def get_embedding(text: str):
       # ...
   ```

2. **Database Indexes**
   ```sql
   CREATE INDEX idx_documents_user_id ON documents(user_id);
   CREATE INDEX idx_conversations_user_id ON conversations(user_id);
   CREATE INDEX idx_messages_conversation_id ON messages(conversation_id);
   ```

3. **Response Compression**
   ```python
   from fastapi.middleware.gzip import GZipMiddleware
   app.add_middleware(GZipMiddleware, minimum_size=1000)
   ```

---

## Cost Estimates

### Free Tier Options
- **Vercel**: Free for hobby projects (100GB bandwidth/month)
- **Render**: Free tier available (web services sleep after 15 min)
- **Railway**: $5 credit/month free trial
- **Supabase**: Free PostgreSQL (500MB)
- **ChromaDB**: Self-hosted (free, pay for storage)

### Production Setup (~$30-50/month)
- **Vercel Pro**: $20/month (or keep free tier)
- **Render Standard**: $7/month
- **Supabase Pro**: $25/month (or use free tier)
- **Domain**: $10-15/year

### Scaling (~$100-200/month)
- **Vercel Pro**: $20/month
- **Render/Heroku**: $25-50/month
- **Managed Vector DB**: $25-75/month
- **PostgreSQL**: $15-25/month
- **Monitoring**: $10-20/month

---

## Support & Resources

- **Documentation**: https://your-docs-site.com
- **GitHub Issues**: https://github.com/yourusername/rag-chatbot/issues
- **Discord Community**: [Join Link]
- **Email Support**: support@yourdomain.com

---

## License

MIT License - See LICENSE file for details.
