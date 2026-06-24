"""Main RAG service orchestrating the retrieval-augmented generation pipeline."""

from typing import List, Dict, Any, Optional, AsyncGenerator
import uuid
from datetime import datetime

from langchain.schema import Document
from sqlalchemy.orm import Session

from app.models.document import Document as DocumentModel, DocumentStatus
from app.models.conversation import Conversation, Message
from app.services.web_scraper import WebScraper
from app.services.pdf_processor import PDFProcessor
from app.services.vector_store import get_vector_store_service
from app.services.llm_service import get_llm_service
from app.utils.chunking import split_documents
from app.core.config import settings


class RAGService:
    """Main RAG service for document ingestion and question answering."""
    
    def __init__(self, db: Session):
        """
        Initialize RAG service.
        
        Args:
            db: Database session
        """
        self.db = db
        self.vector_store = get_vector_store_service()
        self.llm_service = get_llm_service()
    
    def _get_collection_name(self, document_id: str) -> str:
        """Get ChromaDB collection name for a document."""
        return f"doc_{document_id}"
    
    async def ingest_website(
        self,
        url: str,
        user_id: str,
        progress_callback: Optional[callable] = None
    ) -> DocumentModel:
        """
        Ingest a website and store in vector database.
        
        Args:
            url: Website URL to crawl
            user_id: User ID
            progress_callback: Optional callback for progress updates
            
        Returns:
            Created document model
        """
        # Create document record
        doc_model = DocumentModel(
            user_id=user_id,
            url=url,
            document_type="website",
            status=DocumentStatus.PROCESSING
        )
        self.db.add(doc_model)
        self.db.commit()
        self.db.refresh(doc_model)
        
        try:
            # Crawl website
            scraper = WebScraper(
                max_pages=50,
                max_depth=3
            )
            
            async def on_progress(current, total):
                if progress_callback:
                    await progress_callback(current, total)
            
            documents = await scraper.crawl(url, on_progress)
            
            if not documents:
                doc_model.status = DocumentStatus.FAILED
                self.db.commit()
                raise ValueError("No content extracted from website")
            
            # Split documents into chunks
            chunked_docs = split_documents(
                documents,
                chunk_size=settings.CHUNK_SIZE,
                chunk_overlap=settings.CHUNK_OVERLAP
            )
            
            # Add to vector store
            collection_name = self._get_collection_name(doc_model.id)
            self.vector_store.add_documents(chunked_docs, collection_name)
            
            # Update document record
            doc_model.total_chunks = len(chunked_docs)
            doc_model.status = DocumentStatus.COMPLETED
            self.db.commit()
            
            return doc_model
            
        except Exception as e:
            doc_model.status = DocumentStatus.FAILED
            self.db.commit()
            raise e
    
    def ingest_pdf(
        self,
        file_bytes: bytes,
        filename: str,
        user_id: str
    ) -> DocumentModel:
        """
        Ingest a PDF file and store in vector database.
        
        Args:
            file_bytes: PDF file bytes
            filename: Original filename
            user_id: User ID
            
        Returns:
            Created document model
        """
        # Create document record
        doc_model = DocumentModel(
            user_id=user_id,
            filename=filename,
            document_type="pdf",
            status=DocumentStatus.PROCESSING
        )
        self.db.add(doc_model)
        self.db.commit()
        self.db.refresh(doc_model)
        
        try:
            # Process PDF
            processor = PDFProcessor()
            documents = processor.load_pdf_bytes(file_bytes, filename)
            
            if not documents:
                doc_model.status = DocumentStatus.FAILED
                self.db.commit()
                raise ValueError("No content extracted from PDF")
            
            # Split documents into chunks
            chunked_docs = split_documents(
                documents,
                chunk_size=settings.CHUNK_SIZE,
                chunk_overlap=settings.CHUNK_OVERLAP
            )
            
            # Add to vector store
            collection_name = self._get_collection_name(doc_model.id)
            self.vector_store.add_documents(chunked_docs, collection_name)
            
            # Update document record
            doc_model.total_chunks = len(chunked_docs)
            doc_model.status = DocumentStatus.COMPLETED
            self.db.commit()
            
            return doc_model
            
        except Exception as e:
            doc_model.status = DocumentStatus.FAILED
            self.db.commit()
            raise e
    
    def retrieve_context(
        self,
        query: str,
        document_ids: List[str],
        k: int = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant context from vector store.
        
        Args:
            query: User query
            document_ids: List of document IDs to search in
            k: Number of results per document
            
        Returns:
            List of retrieved context chunks with metadata
        """
        k = k or settings.TOP_K_RESULTS
        all_results = []
        
        for doc_id in document_ids:
            collection_name = self._get_collection_name(doc_id)
            results = self.vector_store.similarity_search(
                query=query,
                collection_name=collection_name,
                k=k
            )
            all_results.extend(results)
        
        # Sort by distance/similarity and take top k
        all_results.sort(key=lambda x: x.get('distance', float('inf')))
        return all_results[:k * 2]  # Return more results for better context
    
    async def answer_question(
        self,
        query: str,
        conversation_id: str,
        document_ids: List[str],
        stream: bool = True
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Answer a question using RAG.
        
        Args:
            query: User question
            conversation_id: Conversation ID
            document_ids: List of document IDs to use
            stream: Whether to stream the response
            
        Yields:
            Response chunks with metadata
        """
        # Retrieve context
        context_results = self.retrieve_context(query, document_ids)
        
        if not context_results:
            yield {
                "type": "answer",
                "content": "I couldn't find any relevant information in the provided documents to answer your question.",
                "sources": []
            }
            return
        
        # Get conversation history
        conversation = self.db.query(Conversation).filter(
            Conversation.id == conversation_id
        ).first()
        
        if not conversation:
            raise ValueError(f"Conversation {conversation_id} not found")
        
        # Get last 10 messages for context
        recent_messages = self.db.query(Message).filter(
            Message.conversation_id == conversation_id
        ).order_by(Message.created_at.desc()).limit(10).all()
        
        conversation_history = [
            {"role": msg.role, "content": msg.content}
            for msg in reversed(recent_messages)
        ]
        
        # Prepare sources
        sources = [
            {
                "source": result['metadata'].get('source', 'Unknown'),
                "chunk_index": result['metadata'].get('chunk_index', 0)
            }
            for result in context_results
        ]
        
        # Extract just the content for LLM
        context_texts = [result['content'] for result in context_results]
        
        if stream:
            # Stream response
            full_response = ""
            async for chunk in self.llm_service.generate_streaming_response(
                query=query,
                context=context_texts,
                conversation_history=conversation_history
            ):
                full_response += chunk
                yield {
                    "type": "chunk",
                    "content": chunk
                }
            
            # Save message to database
            assistant_message = Message(
                conversation_id=conversation_id,
                role="assistant",
                content=full_response,
                sources=sources
            )
            self.db.add(assistant_message)
            self.db.commit()
            
            yield {
                "type": "complete",
                "content": full_response,
                "sources": sources
            }
        else:
            # Non-streaming response
            response = self.llm_service.generate_response(
                query=query,
                context=context_texts,
                conversation_history=conversation_history
            )
            
            # Save message to database
            assistant_message = Message(
                conversation_id=conversation_id,
                role="assistant",
                content=response,
                sources=sources
            )
            self.db.add(assistant_message)
            self.db.commit()
            
            yield {
                "type": "answer",
                "content": response,
                "sources": sources
            }
    
    def delete_document(self, document_id: str) -> None:
        """
        Delete a document and its vectors.
        
        Args:
            document_id: Document ID to delete
        """
        # Delete from vector store
        collection_name = self._get_collection_name(document_id)
        self.vector_store.delete_collection(collection_name)
        
        # Delete from database
        doc_model = self.db.query(DocumentModel).filter(
            DocumentModel.id == document_id
        ).first()
        
        if doc_model:
            self.db.delete(doc_model)
            self.db.commit()
