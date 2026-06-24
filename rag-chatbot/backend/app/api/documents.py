"""Documents API endpoints."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.document import Document, DocumentStatus
from app.services.rag_service import RAGService


router = APIRouter(prefix="/documents", tags=["Documents"])


class DocumentResponse(BaseModel):
    """Document response schema."""
    id: str
    user_id: str
    url: Optional[str] = None
    filename: Optional[str] = None
    document_type: str
    status: str
    total_chunks: int
    created_at: str
    
    class Config:
        from_attributes = True


class IngestURLRequest(BaseModel):
    """Request schema for ingesting a website URL."""
    url: str


@router.post("/ingest", response_model=DocumentResponse)
async def ingest_website(
    request: IngestURLRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Ingest a website URL for RAG."""
    rag_service = RAGService(db)
    
    # Validate URL
    if not request.url.startswith(('http://', 'https://')):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid URL. Must start with http:// or https://"
        )
    
    try:
        # Start ingestion in background
        document = await rag_service.ingest_website(
            url=request.url,
            user_id=current_user.id
        )
        
        return document
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/upload", response_model=DocumentResponse)
async def upload_pdf(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Upload and ingest a PDF file."""
    # Validate file type
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are supported"
        )
    
    # Read file bytes
    file_bytes = await file.read()
    
    if len(file_bytes) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Empty file"
        )
    
    rag_service = RAGService(db)
    
    try:
        document = rag_service.ingest_pdf(
            file_bytes=file_bytes,
            filename=file.filename,
            user_id=current_user.id
        )
        
        return document
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/", response_model=List[DocumentResponse])
async def list_documents(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all documents for the current user."""
    documents = db.query(Document).filter(
        Document.user_id == current_user.id
    ).offset(skip).limit(limit).all()
    
    return documents


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific document by ID."""
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.user_id == current_user.id
    ).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    return document


@router.get("/{document_id}/status")
async def get_document_status(
    document_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get the indexing status of a document."""
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.user_id == current_user.id
    ).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    return {
        "id": document.id,
        "status": document.status,
        "total_chunks": document.total_chunks
    }


@router.delete("/{document_id}")
async def delete_document(
    document_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a document and its vectors."""
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.user_id == current_user.id
    ).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    rag_service = RAGService(db)
    rag_service.delete_document(document_id)
    
    return {"message": "Document deleted successfully"}
