from __future__ import annotations
from pydantic import BaseModel, HttpUrl, Field


class IngestRequest(BaseModel):
    url: HttpUrl
    max_pages: int = Field(default=30, ge=1, le=200)


class IngestStatus(BaseModel):
    job_id: str
    url: str
    status: str  # pending | running | completed | failed
    pages_indexed: int = 0
    chunks_created: int = 0
    error: str | None = None


class ChatRequest(BaseModel):
    session_id: str
    question: str = Field(min_length=1, max_length=2000)


class Source(BaseModel):
    url: str
    title: str
    snippet: str
    score: float


class ChatResponse(BaseModel):
    answer: str
    sources: list[Source]
