from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Enum as SQLEnum, Text
import uuid
from datetime import datetime
import enum

from app.core.database import Base


class DocumentType(str, enum.Enum):
    """Document type enum."""
    WEBSITE = "website"
    PDF = "pdf"


class DocumentStatus(str, enum.Enum):
    """Document status enum."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Document(Base):
    """Document model for storing ingested content."""
    
    __tablename__ = "documents"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    url = Column(String(2048), nullable=True)
    filename = Column(String(255), nullable=True)
    document_type = Column(SQLEnum(DocumentType), nullable=False)
    status = Column(SQLEnum(DocumentStatus), default=DocumentStatus.PENDING)
    total_chunks = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<Document {self.url or self.filename}>"
