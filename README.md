
📁 Project Structure
# Backend
cd backend
cp .env.example .env        # fill in GEMINI_API_KEY or OPENAI_API_KEY
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Frontend (separate terminal)
cd frontend
npm install
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local
npm run dev
rag-chatbot/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI entry
│   │   ├── config.py            # Settings
│   │   ├── models.py            # Pydantic schemas
│   │   ├── routers/
│   │   │   ├── __init__.py
│   │   │   ├── ingest.py        # URL ingestion endpoints
│   │   │   └── chat.py          # Chat + SSE streaming
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── crawler.py       # Recursive web scraper
│   │   │   ├── chunker.py       # Text splitter
│   │   │   ├── embeddings.py    # Embedding + Chroma
│   │   │   └── rag.py           # LangChain RAG pipeline
│   │   └── utils/
│   │       ├── __init__.py
│   │       └── text.py          # Cleaning helpers
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── layout.tsx
│   │   │   ├── page.tsx
│   │   │   └── globals.css
│   │   └── components/
│   │       ├── ChatWindow.tsx
│   │       ├── IngestForm.tsx
│   │       └── Message.tsx
│   ├── package.json
│   ├── tailwind.config.ts
│   └── Dockerfile
├── docker-compose.yml
└── README.md
