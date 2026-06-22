from __future__ import annotations
from functools import lru_cache

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_community.embeddings import HuggingFaceEmbeddings

from app.config import get_settings


@lru_cache
def get_embeddings() -> Embeddings:
    settings = get_settings()
    return HuggingFaceEmbeddings(
        model_name=settings.embedding_model,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )


def get_collection(session_id: str) -> Chroma:
    settings = get_settings()
    return Chroma(
        collection_name=f"site_{session_id}",
        embedding_function=get_embeddings(),
        persist_directory=settings.chroma_persist_dir,
    )


def ingest_documents(session_id: str, docs: list[Document]) -> int:
    if not docs:
        return 0
    store = get_collection(session_id)
    store.add_documents(docs)
    return len(docs)


def similarity_search(session_id: str, query: str, k: int | None = None):
    settings = get_settings()
    store = get_collection(session_id)
    return store.similarity_search_with_score(query, k=k or settings.top_k)
