"""Embedding service for generating vector embeddings."""

from typing import List, Union
from sentence_transformers import SentenceTransformer

from app.core.config import settings


class EmbeddingService:
    """Service for generating text embeddings."""
    
    def __init__(self, model_name: str = None):
        """
        Initialize embedding service.
        
        Args:
            model_name: Name of the embedding model to use
        """
        self.model_name = model_name or settings.EMBEDDING_MODEL
        self.model = None
    
    def _load_model(self):
        """Load the embedding model if not already loaded."""
        if self.model is None:
            self.model = SentenceTransformer(self.model_name)
    
    def embed_text(self, text: str) -> List[float]:
        """
        Generate embedding for a single text.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector as list of floats
        """
        self._load_model()
        embedding = self.model.encode(text, convert_to_numpy=True)
        return embedding.tolist()
    
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors
        """
        self._load_model()
        embeddings = self.model.encode(texts, convert_to_numpy=True)
        return embeddings.tolist()
    
    def get_dimension(self) -> int:
        """Get the dimension of embeddings produced by this model."""
        self._load_model()
        return self.model.get_sentence_embedding_dimension()


# Global embedding service instance
_embedding_service: EmbeddingService = None


def get_embedding_service() -> EmbeddingService:
    """Get or create global embedding service."""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service
