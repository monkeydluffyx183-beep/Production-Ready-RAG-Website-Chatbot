"""Text chunking utilities for RAG."""

from typing import List, Dict, Any
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document as LangChainDocument


def create_text_splitter(
    chunk_size: int = 500,
    chunk_overlap: int = 50,
    separators: List[str] = None
) -> RecursiveCharacterTextSplitter:
    """
    Create a text splitter with custom configuration.
    
    Args:
        chunk_size: Maximum size of each chunk
        chunk_overlap: Overlap between chunks
        separators: Custom separators for splitting
        
    Returns:
        Configured text splitter
    """
    if separators is None:
        separators = [
            "\n## ",
            "\n### ",
            "\n#### ",
            "\n##### ",
            "\n###### ",
            "\n\n",
            "\n",
            " ",
            ""
        ]
    
    return RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        separators=separators
    )


def split_text(text: str, chunk_size: int = 500, chunk_overlap: int = 50) -> List[str]:
    """
    Split text into chunks.
    
    Args:
        text: Text to split
        chunk_size: Maximum size of each chunk
        chunk_overlap: Overlap between chunks
        
    Returns:
        List of text chunks
    """
    splitter = create_text_splitter(chunk_size, chunk_overlap)
    chunks = splitter.split_text(text)
    return chunks


def split_documents(
    documents: List[LangChainDocument],
    chunk_size: int = 500,
    chunk_overlap: int = 50
) -> List[LangChainDocument]:
    """
    Split documents into chunks while preserving metadata.
    
    Args:
        documents: List of LangChain documents
        chunk_size: Maximum size of each chunk
        chunk_overlap: Overlap between chunks
        
    Returns:
        List of chunked documents with metadata
    """
    splitter = create_text_splitter(chunk_size, chunk_overlap)
    split_docs = splitter.split_documents(documents)
    return split_docs


def create_chunk_metadata(
    source: str,
    chunk_index: int,
    total_chunks: int,
    extra_metadata: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Create metadata for a chunk.
    
    Args:
        source: Source URL or filename
        chunk_index: Index of this chunk
        total_chunks: Total number of chunks
        extra_metadata: Additional metadata
        
    Returns:
        Metadata dictionary
    """
    metadata = {
        "source": source,
        "chunk_index": chunk_index,
        "total_chunks": total_chunks
    }
    
    if extra_metadata:
        metadata.update(extra_metadata)
    
    return metadata
