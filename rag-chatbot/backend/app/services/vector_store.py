"""ChromaDB vector store service."""

from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings
from langchain.schema import Document
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings

from app.core.config import settings
from app.services.embedding_service import get_embedding_service


class VectorStoreService:
    """Service for managing vector storage with ChromaDB."""
    
    def __init__(self, persist_directory: str = None):
        """
        Initialize vector store service.
        
        Args:
            persist_directory: Directory to persist ChromaDB data
        """
        self.persist_directory = persist_directory or settings.CHROMA_PERSIST_DIR
        
        # Initialize ChromaDB client with persistence
        self.client = chromadb.PersistentClient(path=self.persist_directory)
        
        # Cache for collection instances
        self._collections = {}
    
    def _get_embeddings(self):
        """Get LangChain-compatible embeddings."""
        return HuggingFaceEmbeddings(
            model_name=settings.EMBEDDING_MODEL,
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )
    
    def get_or_create_collection(self, collection_name: str) -> chromadb.Collection:
        """
        Get or create a ChromaDB collection.
        
        Args:
            collection_name: Name of the collection
            
        Returns:
            ChromaDB collection instance
        """
        if collection_name not in self._collections:
            collection = self.client.get_or_create_collection(
                name=collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            self._collections[collection_name] = collection
        
        return self._collections[collection_name]
    
    def add_documents(
        self,
        documents: List[Document],
        collection_name: str,
        batch_size: int = 100
    ) -> None:
        """
        Add documents to the vector store.
        
        Args:
            documents: List of documents to add
            collection_name: Name of the collection
            batch_size: Number of documents to process at once
        """
        if not documents:
            return
        
        collection = self.get_or_create_collection(collection_name)
        
        # Process in batches
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i + batch_size]
            
            texts = [doc.page_content for doc in batch]
            metadatas = [doc.metadata for doc in batch]
            ids = [f"{collection_name}_{i+j}" for j in range(len(batch))]
            
            collection.add(
                documents=texts,
                metadatas=metadatas,
                ids=ids
            )
    
    def similarity_search(
        self,
        query: str,
        collection_name: str,
        k: int = None,
        filter_metadata: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar documents.
        
        Args:
            query: Query text
            collection_name: Name of the collection
            k: Number of results to return
            filter_metadata: Metadata filter
            
        Returns:
            List of results with content and metadata
        """
        k = k or settings.TOP_K_RESULTS
        collection = self.get_or_create_collection(collection_name)
        
        # Convert metadata filter to ChromaDB format
        where = None
        if filter_metadata:
            where = filter_metadata
        
        results = collection.query(
            query_texts=[query],
            n_results=k,
            where=where,
            include=["documents", "metadatas", "distances"]
        )
        
        # Format results
        formatted_results = []
        if results['documents'] and results['documents'][0]:
            for i, doc in enumerate(results['documents'][0]):
                result = {
                    "content": doc,
                    "metadata": results['metadatas'][0][i] if results['metadatas'] else {},
                    "distance": results['distances'][0][i] if results['distances'] else None
                }
                formatted_results.append(result)
        
        return formatted_results
    
    def delete_collection(self, collection_name: str) -> None:
        """
        Delete a collection.
        
        Args:
            collection_name: Name of the collection to delete
        """
        self.client.delete_collection(collection_name)
        if collection_name in self._collections:
            del self._collections[collection_name]
    
    def clear_collection(self, collection_name: str) -> None:
        """
        Clear all documents from a collection.
        
        Args:
            collection_name: Name of the collection
        """
        collection = self.get_or_create_collection(collection_name)
        collection.delete(where={})
    
    def get_collection_count(self, collection_name: str) -> int:
        """
        Get the number of documents in a collection.
        
        Args:
            collection_name: Name of the collection
            
        Returns:
            Number of documents
        """
        collection = self.get_or_create_collection(collection_name)
        return collection.count()


# Global vector store service instance
_vector_store_service: Optional[VectorStoreService] = None


def get_vector_store_service() -> VectorStoreService:
    """Get or create global vector store service."""
    global _vector_store_service
    if _vector_store_service is None:
        _vector_store_service = VectorStoreService()
    return _vector_store_service
