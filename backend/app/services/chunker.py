from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

from app.config import get_settings
from app.services.crawler import Page


def chunk_pages(pages: list[Page]) -> list[Document]:
    settings = get_settings()
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
        length_function=len,
    )
    docs: list[Document] = []
    for page in pages:
        parts = splitter.split_text(page.text)
        for i, chunk in enumerate(parts):
            docs.append(Document(
                page_content=chunk,
                metadata={
                    "source": page.url,
                    "title": page.title,
                    "chunk_index": i,
                },
            ))
    return docs
