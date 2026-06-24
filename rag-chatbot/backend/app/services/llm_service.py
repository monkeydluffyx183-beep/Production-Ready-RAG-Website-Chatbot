"""LLM service for generating responses."""

from typing import List, Dict, Any, Optional, AsyncGenerator
import asyncio

from langchain.schema import HumanMessage, SystemMessage, AIMessage
from langchain_core.messages import BaseMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI

from app.core.config import settings


class LLMService:
    """Service for interacting with LLM providers."""
    
    def __init__(
        self,
        provider: str = None,
        model: str = None,
        temperature: float = None
    ):
        """
        Initialize LLM service.
        
        Args:
            provider: LLM provider ('gemini' or 'openai')
            model: Model name to use
            temperature: Temperature for generation
        """
        self.provider = provider or settings.LLM_PROVIDER
        self.model = model or settings.LLM_MODEL
        self.temperature = temperature or settings.LLM_TEMPERATURE
        self._llm = None
    
    def _get_llm(self):
        """Get or create LLM instance."""
        if self._llm is None:
            if self.provider == "gemini":
                if not settings.GEMINI_API_KEY:
                    raise ValueError("GEMINI_API_KEY not set")
                self._llm = ChatGoogleGenerativeAI(
                    model=self.model,
                    google_api_key=settings.GEMINI_API_KEY,
                    temperature=self.temperature,
                    max_output_tokens=settings.MAX_TOKENS
                )
            elif self.provider == "openai":
                if not settings.OPENAI_API_KEY:
                    raise ValueError("OPENAI_API_KEY not set")
                self._llm = ChatOpenAI(
                    model=self.model,
                    openai_api_key=settings.OPENAI_API_KEY,
                    temperature=self.temperature,
                    max_tokens=settings.MAX_TOKENS
                )
            else:
                raise ValueError(f"Unsupported LLM provider: {self.provider}")
        
        return self._llm
    
    def generate_response(
        self,
        query: str,
        context: List[str],
        system_prompt: str = None,
        conversation_history: List[Dict[str, str]] = None
    ) -> str:
        """
        Generate a response using the LLM.
        
        Args:
            query: User query
            context: List of context chunks from RAG
            system_prompt: Optional system prompt
            conversation_history: Optional conversation history
            
        Returns:
            Generated response text
        """
        llm = self._get_llm()
        
        # Build system prompt with context
        if system_prompt is None:
            system_prompt = (
                "You are a helpful assistant that answers questions based on the provided context. "
                "Always cite your sources when answering. If you don't have enough information "
                "in the context to answer the question, say so clearly."
            )
        
        context_text = "\n\n".join([f"[Context {i+1}]:\n{ctx}" for i, ctx in enumerate(context)])
        
        full_system_prompt = f"{system_prompt}\n\nRelevant Context:\n{context_text}"
        
        # Build messages
        messages: List[BaseMessage] = [SystemMessage(content=full_system_prompt)]
        
        # Add conversation history
        if conversation_history:
            for msg in conversation_history:
                if msg["role"] == "user":
                    messages.append(HumanMessage(content=msg["content"]))
                elif msg["role"] == "assistant":
                    messages.append(AIMessage(content=msg["content"]))
        
        # Add current query
        messages.append(HumanMessage(content=query))
        
        # Generate response
        response = llm.invoke(messages)
        return response.content
    
    async def generate_streaming_response(
        self,
        query: str,
        context: List[str],
        system_prompt: str = None,
        conversation_history: List[Dict[str, str]] = None
    ) -> AsyncGenerator[str, None]:
        """
        Generate a streaming response using the LLM.
        
        Args:
            query: User query
            context: List of context chunks from RAG
            system_prompt: Optional system prompt
            conversation_history: Optional conversation history
            
        Yields:
            Chunks of generated response text
        """
        llm = self._get_llm()
        
        # Build system prompt with context
        if system_prompt is None:
            system_prompt = (
                "You are a helpful assistant that answers questions based on the provided context. "
                "Always cite your sources when answering. If you don't have enough information "
                "in the context to answer the question, say so clearly."
            )
        
        context_text = "\n\n".join([f"[Context {i+1}]:\n{ctx}" for i, ctx in enumerate(context)])
        
        full_system_prompt = f"{system_prompt}\n\nRelevant Context:\n{context_text}"
        
        # Build messages
        messages: List[BaseMessage] = [SystemMessage(content=full_system_prompt)]
        
        # Add conversation history
        if conversation_history:
            for msg in conversation_history:
                if msg["role"] == "user":
                    messages.append(HumanMessage(content=msg["content"]))
                elif msg["role"] == "assistant":
                    messages.append(AIMessage(content=msg["content"]))
        
        # Add current query
        messages.append(HumanMessage(content=query))
        
        # Stream response
        async for chunk in llm.astream(messages):
            yield chunk.content


# Global LLM service instance
_llm_service: Optional[LLMService] = None


def get_llm_service() -> LLMService:
    """Get or create global LLM service."""
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service
