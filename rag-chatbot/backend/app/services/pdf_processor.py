"""PDF processing service."""

import io
from typing import List, Optional
from pathlib import Path

from langchain.schema import Document
from langchain_community.document_loaders import PyPDFLoader


class PDFProcessor:
    """Service for processing PDF files."""
    
    def __init__(self):
        """Initialize PDF processor."""
        pass
    
    def load_pdf(self, file_path: str) -> List[Document]:
        """
        Load a PDF file and extract content.
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            List of documents (one per page)
        """
        loader = PyPDFLoader(file_path)
        documents = loader.load()
        return documents
    
    def load_pdf_bytes(self, file_bytes: bytes, filename: str = "uploaded.pdf") -> List[Document]:
        """
        Load PDF from bytes.
        
        Args:
            file_bytes: PDF file bytes
            filename: Temporary filename for the PDF
            
        Returns:
            List of documents (one per page)
        """
        # Create temporary file
        import tempfile
        
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
            tmp_file.write(file_bytes)
            tmp_path = tmp_file.name
        
        try:
            documents = self.load_pdf(tmp_path)
            
            # Update metadata with original filename
            for doc in documents:
                doc.metadata["source"] = filename
            
            return documents
        finally:
            # Clean up temp file
            Path(tmp_path).unlink(missing_ok=True)
    
    def process_pdf(
        self,
        file_path: str,
        metadata: Optional[dict] = None
    ) -> List[Document]:
        """
        Process a PDF file and return documents with metadata.
        
        Args:
            file_path: Path to the PDF file
            metadata: Additional metadata to add
            
        Returns:
            List of processed documents
        """
        documents = self.load_pdf(file_path)
        
        if metadata:
            for doc in documents:
                doc.metadata.update(metadata)
        
        return documents
