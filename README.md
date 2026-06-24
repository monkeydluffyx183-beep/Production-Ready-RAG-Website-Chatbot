# RAG Chatbot

A Retrieval-Augmented Generation (RAG) chatbot that allows users to ingest web content and chat with it using AI. Built with FastAPI backend and Next.js frontend.

## Features

- 🌐 **Web Content Ingestion**: Recursively crawl and ingest content from URLs
- 💬 **AI-Powered Chat**: Chat with your ingested content using LLMs (Gemini or OpenAI)
- 🔄 **Real-time Streaming**: Server-Sent Events (SSE) for streaming responses
- 🎨 **Modern UI**: Clean, responsive interface built with Next.js and Tailwind CSS
- 📦 **Docker Support**: Easy deployment with Docker Compose
- 💾 **Vector Storage**: ChromaDB for persistent vector embeddings

## Tech Stack

### Backend
- **Framework**: FastAPI
- **LLM Integration**: LangChain with Google Gemini / OpenAI support
- **Vector Database**: ChromaDB
- **Web Scraping**: BeautifulSoup4, lxml
- **Embeddings**: Sentence Transformers

### Frontend
- **Framework**: Next.js 14
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **Components**: React Markdown, Lucide React icons

## Project Structure

```
/workspace/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI entry point
│   │   ├── config.py            # Application settings
│   │   ├── models.py            # Pydantic schemas
│   │   ├── routers/
│   │   │   ├── ingest.py        # URL ingestion endpoints
│   │   │   └── chat.py          # Chat + SSE streaming
│   │   ├── services/
│   │   │   ├── crawler.py       # Recursive web scraper
│   │   │   ├── chunker.py       # Text splitter
│   │   │   ├── embeddings.py    # Embedding + ChromaDB
│   │   │   └── rag.py           # LangChain RAG pipeline
│   │   └── utils/
│   │       └── text.py          # Text cleaning helpers
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
```

## Quick Start

### Prerequisites

- Python 3.9+
- Node.js 18+
- Docker & Docker Compose (optional)
- API Key: Google Gemini or OpenAI

### Option 1: Docker Compose (Recommended)

1. **Configure environment variables**:
   ```bash
   cd backend
   cp .env.example .env
   # Edit .env and add your API key:
   # GEMINI_API_KEY=your_key_here
   # or
   # OPENAI_API_KEY=your_key_here
   ```

2. **Start all services**:
   ```bash
   docker-compose up --build
   ```

3. **Access the application**:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

### Option 2: Manual Setup

#### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your API key

# Start the server
uvicorn app.main:app --reload --port 8000
```

#### Frontend Setup

Open a new terminal:

```bash
cd frontend

# Install dependencies
npm install

# Configure environment
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local

# Start development server
npm run dev
```

Access the application at http://localhost:3000

## Configuration

### Environment Variables

#### Backend (.env)

| Variable | Description | Required |
|----------|-------------|----------|
| `GEMINI_API_KEY` | Google Gemini API key | Yes* |
| `OPENAI_API_KEY` | OpenAI API key | Yes* |
| `CHROMA_PERSIST_DIR` | ChromaDB persistence directory | No (default: ./chroma_data) |

*At least one API key is required

#### Frontend (.env.local)

| Variable | Description | Default |
|----------|-------------|---------|
| `NEXT_PUBLIC_API_URL` | Backend API URL | http://localhost:8000 |

## Usage

1. **Ingest Content**: 
   - Enter a URL in the ingestion form
   - The system will crawl the website and store embeddings in ChromaDB

2. **Chat**:
   - Ask questions about the ingested content
   - Responses are streamed in real-time
   - The RAG system retrieves relevant context before generating answers

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| POST | `/api/ingest` | Ingest content from URL |
| POST | `/api/chat` | Send chat message |
| GET | `/api/chat/stream` | Stream chat response (SSE) |

Visit http://localhost:8000/docs for interactive API documentation.

## Development

### Running Tests

(Add your test commands here)

### Code Style

- Backend: Follow PEP 8 guidelines
- Frontend: ESLint + Prettier configuration

## License

See [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
