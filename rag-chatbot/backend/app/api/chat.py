"""Chat API endpoints."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
import json

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.document import Document
from app.models.conversation import Conversation, Message


router = APIRouter(prefix="/chat", tags=["Chat"])


class CreateConversationRequest(BaseModel):
    """Request schema for creating a conversation."""
    title: str
    document_ids: List[str]


class SendMessageRequest(BaseModel):
    """Request schema for sending a message."""
    content: str
    stream: bool = True


class MessageResponse(BaseModel):
    """Message response schema."""
    id: str
    conversation_id: str
    role: str
    content: str
    sources: Optional[dict] = None
    created_at: str
    
    class Config:
        from_attributes = True


class ConversationResponse(BaseModel):
    """Conversation response schema."""
    id: str
    user_id: str
    title: str
    document_ids: List[str]
    created_at: str
    updated_at: str
    
    class Config:
        from_attributes = True


@router.post("/conversations", response_model=ConversationResponse)
async def create_conversation(
    request: CreateConversationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new conversation."""
    # Validate document IDs
    documents = db.query(Document).filter(
        Document.id.in_(request.document_ids),
        Document.user_id == current_user.id
    ).all()
    
    if len(documents) != len(request.document_ids):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="One or more documents not found"
        )
    
    # Check all documents are completed
    for doc in documents:
        if doc.status != "completed":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Document {doc.id} is not ready (status: {doc.status})"
            )
    
    conversation = Conversation(
        user_id=current_user.id,
        title=request.title,
        document_ids=request.document_ids
    )
    
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    
    return conversation


@router.get("/conversations", response_model=List[ConversationResponse])
async def list_conversations(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all conversations for the current user."""
    conversations = db.query(Conversation).filter(
        Conversation.user_id == current_user.id
    ).order_by(Conversation.updated_at.desc()).offset(skip).limit(limit).all()
    
    return conversations


@router.get("/conversations/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific conversation."""
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id
    ).first()
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    return conversation


@router.get("/conversations/{conversation_id}/messages", response_model=List[MessageResponse])
async def get_conversation_messages(
    conversation_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all messages in a conversation."""
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id
    ).first()
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    messages = db.query(Message).filter(
        Message.conversation_id == conversation_id
    ).order_by(Message.created_at.asc()).all()
    
    return messages


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a conversation and its messages."""
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id
    ).first()
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    # Delete messages
    db.query(Message).filter(
        Message.conversation_id == conversation_id
    ).delete()
    
    # Delete conversation
    db.delete(conversation)
    db.commit()
    
    return {"message": "Conversation deleted successfully"}


@router.post("/messages")
async def send_message(
    request: SendMessageRequest,
    conversation_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Send a message and get a response (with optional streaming)."""
    from app.services.rag_service import RAGService
    
    # Get conversation
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id
    ).first()
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    # Save user message
    user_message = Message(
        conversation_id=conversation_id,
        role="user",
        content=request.content
    )
    db.add(user_message)
    db.commit()
    
    # Update conversation timestamp
    conversation.updated_at = db.func.now()
    db.commit()
    
    rag_service = RAGService(db)
    
    if request.stream:
        # Stream response
        async def generate():
            async for chunk in rag_service.answer_question(
                query=request.content,
                conversation_id=conversation_id,
                document_ids=conversation.document_ids,
                stream=True
            ):
                yield f"data: {json.dumps(chunk)}\n\n"
        
        return StreamingResponse(
            generate(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
            }
        )
    else:
        # Non-streaming response
        response_data = None
        async for chunk in rag_service.answer_question(
            query=request.content,
            conversation_id=conversation_id,
            document_ids=conversation.document_ids,
            stream=False
        ):
            response_data = chunk
        
        return response_data


@router.get("/conversations/{conversation_id}/export")
async def export_conversation(
    conversation_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Export conversation as text/JSON."""
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id
    ).first()
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    messages = db.query(Message).filter(
        Message.conversation_id == conversation_id
    ).order_by(Message.created_at.asc()).all()
    
    export_data = {
        "conversation": {
            "id": conversation.id,
            "title": conversation.title,
            "created_at": conversation.created_at.isoformat(),
            "document_ids": conversation.document_ids
        },
        "messages": [
            {
                "role": msg.role,
                "content": msg.content,
                "sources": msg.sources,
                "created_at": msg.created_at.isoformat()
            }
            for msg in messages
        ]
    }
    
    return export_data
