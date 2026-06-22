from __future__ import annotations
import asyncio
import uuid
import logging
from fastapi import APIRouter, BackgroundTasks, HTTPException

from app.models import IngestRequest, IngestStatus
from app.services.crawler import SiteCrawler
from app.services.chunker import chunk_pages
from app.services.embeddings import ingest_documents

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ingest", tags=["ingest"])

# In-memory job store (swap for Redis in prod)
JOBS: dict[str, IngestStatus] = {}


async def _run_ingest(job_id: str, url: str, max_pages: int):
    job = JOBS[job_id]
    try:
        job.status = "running"
        crawler = SiteCrawler(url, max_pages=max_pages)
        pages = await crawler.run()
        if not pages:
            raise RuntimeError("No meaningful pages were crawled.")
        job.pages_indexed = len(pages)
        docs = chunk_pages(pages)
        job.chunks_created = len(docs)
        ingest_documents(job_id, docs)
        job.status = "completed"
    except Exception as e:
        logger.exception("Ingest failed")
        job.status = "failed"
        job.error = str(e)


@router.post("", response_model=IngestStatus)
async def start_ingest(req: IngestRequest, bg: BackgroundTasks):
    job_id = uuid.uuid4().hex[:12]
    job = IngestStatus(job_id=job_id, url=str(req.url), status="pending")
    JOBS[job_id] = job
    bg.add_task(_run_ingest, job_id, str(req.url), req.max_pages)
    return job


@router.get("/{job_id}", response_model=IngestStatus)
async def get_status(job_id: str):
    if job_id not in JOBS:
        raise HTTPException(404, "Job not found")
    return JOBS[job_id]
