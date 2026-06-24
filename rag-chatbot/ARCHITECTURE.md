# RAG Website Chatbot - Production Architecture

## Project Structure

```
rag-chatbot/
├── backend/
│   ├── app/
│   │   ├── api/              # API endpoints
│   │   │   ├── __init__.py
│   │   │   ├── auth.py       # Authentication endpoints
│   │   │   ├── chat.py       # Chat endpoints
│   │   │   ├── documents.py  # Document ingestion endpoints
│   │   │   └── analytics.py  # Analytics endpoints
│   │   ├── core/             # Core configuration
│   │   │   ├── __init__.py
│   │   │   ├── config.py     # Environment config
│   │   │   ├── security.py   # JWT & password hashing
│   │   │   └── database.py   # Database connection
│   │   ├── models/           # SQLAlchemy models
│   │   │   ├── __init__.py
│   │   │   ├── user.py
│   │   │   ├── document.py
│   │   │   ├── conversation.py
│   │   │   └── message.py
│   │   ├── services/         # Business logic
│   │   │   ├── __init__.py
│   │   │   ├── rag_service.py      # RAG pipeline
│   │   │   ├── web_scraper.py      # Web crawling
│   │   │   ├── embedding_service.py # Embedding generation
│   │   │   ├── llm_service.py      # LLM integration
│   │   │   ├── vector_store.py     # ChromaDB operations
│   │   │   └── pdf_processor.py    # PDF handling
│   │   └── utils/            # Utilities
│   │       ├── __init__.py
│   │       ├── text_cleaner.py
│   │       ├── chunking.py
│   │       └── rate_limiter.py
│   ├── tests/
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── app/              # Next.js pages
│   │   ├── components/       # React components
│   │   ├── hooks/            # Custom hooks
│   │   ├── lib/              # Utilities
│   │   ├── store/            # State management
│   │   └── types/            # TypeScript types
│   ├── public/
│   ├── package.json
│   ├── tailwind.config.js
│   ├── next.config.js
│   └── Dockerfile
├── docker/
│   ├── docker-compose.yml
│   └── chromadb/
├── README.md
└── deployment-guide.md
```

## Database Schema

### Users Table
- id (UUID, Primary Key)
- email (String, Unique, Indexed)
- hashed_password (String)
- full_name (String)
- is_active (Boolean)
- created_at (DateTime)
- updated_at (DateTime)

### Documents Table
- id (UUID, Primary Key)
- user_id (UUID, Foreign Key -> Users)
- url (String, Nullable)
- filename (String, Nullable)
- document_type (Enum: 'website', 'pdf')
- status (Enum: 'pending', 'processing', 'completed', 'failed')
- total_chunks (Integer)
- created_at (DateTime)
- updated_at (DateTime)

### Conversations Table
- id (UUID, Primary Key)
- user_id (UUID, Foreign Key -> Users)
- title (String)
- document_ids (Array of UUIDs)
- created_at (DateTime)
- updated_at (DateTime)

### Messages Table
- id (UUID, Primary Key)
- conversation_id (UUID, Foreign Key -> Conversations)
- role (Enum: 'user', 'assistant')
- content (Text)
- sources (JSON)
- created_at (DateTime)

## API Endpoints

### Authentication
- POST /api/v1/auth/register - Register new user
- POST /api/v1/auth/login - Login user
- POST /api/v1/auth/logout - Logout user
- GET /api/v1/auth/me - Get current user
- POST /api/v1/auth/refresh - Refresh token

### Documents
- POST /api/v1/documents/ingest - Ingest website URL
- POST /api/v1/documents/upload - Upload PDF file
- GET /api/v1/documents - List all documents
- GET /api/v1/documents/{id} - Get document details
- DELETE /api/v1/documents/{id} - Delete document
- GET /api/v1/documents/{id}/status - Get indexing status

### Chat
- POST /api/v1/chat/conversations - Create conversation
- GET /api/v1/chat/conversations - List conversations
- GET /api/v1/chat/conversations/{id} - Get conversation
- DELETE /api/v1/chat/conversations/{id} - Delete conversation
- POST /api/v1/chat/messages - Send message (streaming)
- GET /api/v1/chat/conversations/{id}/export - Export as PDF

### Analytics
- GET /api/v1/analytics/overview - Dashboard overview
- GET /api/v1/analytics/usage - Usage statistics
- GET /api/v1/analytics/documents - Document metrics

## Vector Database Setup

ChromaDB will be used with:
- Persistent storage mounted to docker volume
- Collection per user or per document
- HNSW index for approximate nearest neighbor search
- Metadata filtering for multi-tenant support

## LangChain Pipeline

1. **Document Loaders**: 
   - WebScraper for websites
   - PyPDFLoader for PDFs

2. **Text Splitters**:
   - RecursiveCharacterTextSplitter with semantic awareness
   - Chunk size: 500 tokens, overlap: 50 tokens

3. **Embeddings**:
   - sentence-transformers/all-MiniLM-L6-v2
   - Dimension: 384

4. **Vector Store**:
   - ChromaDB with persistence
   - Similarity search with k=4

5. **Retrieval**:
   - Hybrid search (BM25 + Vector)
   - Maximal Marginal Relevance (MMR)

6. **LLM**:
   - Gemini 2.5 Flash or GPT-4o-mini
   - Streaming enabled
   - Temperature: 0.7

7. **Memory**:
   - ConversationBufferWindowMemory
   - Last 10 messages context

## Deployment Instructions

### Local Development
```bash
# Start all services
docker-compose up -d

# Access services
Frontend: http://localhost:3000
Backend: http://localhost:8000
ChromaDB: http://localhost:8001
```

### Render Deployment
1. Push code to GitHub
2. Create Web Service on Render
3. Set environment variables
4. Deploy

### Vercel Deployment
1. Frontend: Deploy to Vercel
2. Backend: Deploy to Render/Railway
3. Configure CORS and API URLs
