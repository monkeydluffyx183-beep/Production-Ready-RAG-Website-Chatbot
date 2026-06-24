"""Analytics API endpoints."""

from typing import Dict, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.document import Document, DocumentStatus
from app.models.conversation import Conversation, Message


router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/overview")
async def get_analytics_overview(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get analytics overview for the current user."""
    # Count documents by status
    document_stats = db.query(
        Document.status,
        func.count(Document.id)
    ).filter(
        Document.user_id == current_user.id
    ).group_by(Document.status).all()
    
    document_counts = {status.value: count for status, count in document_stats}
    
    # Total conversations
    total_conversations = db.query(func.count(Conversation.id)).filter(
        Conversation.user_id == current_user.id
    ).scalar()
    
    # Total messages
    total_messages = db.query(func.count(Message.id)).join(
        Conversation,
        Message.conversation_id == Conversation.id
    ).filter(
        Conversation.user_id == current_user.id
    ).scalar()
    
    return {
        "documents": {
            "total": sum(document_counts.values()),
            "completed": document_counts.get("completed", 0),
            "processing": document_counts.get("processing", 0),
            "failed": document_counts.get("failed", 0),
            "pending": document_counts.get("pending", 0)
        },
        "conversations": {
            "total": total_conversations
        },
        "messages": {
            "total": total_messages
        }
    }


@router.get("/usage")
async def get_usage_statistics(
    days: int = 7,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get usage statistics for the last N days."""
    from datetime import datetime, timedelta
    
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    # Messages per day
    messages_per_day = db.query(
        func.date(Message.created_at),
        func.count(Message.id)
    ).join(
        Conversation,
        Message.conversation_id == Conversation.id
    ).filter(
        Conversation.user_id == current_user.id,
        Message.created_at >= cutoff_date
    ).group_by(func.date(Message.created_at)).all()
    
    # Documents created per day
    documents_per_day = db.query(
        func.date(Document.created_at),
        func.count(Document.id)
    ).filter(
        Document.user_id == current_user.id,
        Document.created_at >= cutoff_date
    ).group_by(func.date(Document.created_at)).all()
    
    return {
        "period_days": days,
        "messages": [
            {"date": str(date), "count": count}
            for date, count in messages_per_day
        ],
        "documents": [
            {"date": str(date), "count": count}
            for date, count in documents_per_day
        ]
    }


@router.get("/documents")
async def get_document_metrics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get detailed document metrics."""
    documents = db.query(Document).filter(
        Document.user_id == current_user.id
    ).all()
    
    metrics = []
    for doc in documents:
        metrics.append({
            "id": doc.id,
            "url": doc.url,
            "filename": doc.filename,
            "type": doc.document_type,
            "status": doc.status,
            "chunks": doc.total_chunks,
            "created_at": doc.created_at.isoformat()
        })
    
    return {
        "total_documents": len(metrics),
        "documents": metrics
    }
