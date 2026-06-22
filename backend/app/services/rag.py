from __future__ import annotations
from typing import AsyncIterator

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, SystemMessage

from app.config import get_settings
from app.services.embeddings import similarity_search


SYSTEM_PROMPT = """You are a helpful assistant that answers questions using ONLY the
content retrieved from a specific website. If the answer cannot be derived from the
provided context, say so clearly and do not invent information. Always cite the source
URL for each factual claim using [n] markers, where n matches the source index.

Context sources:
{context}
"""

QA_PROMPT = """Answer the user's question using only the context above.
If the answer is not in the context, reply: "I couldn't find that information on this site."

Question: {question}
Answer:"""


def _get_llm():
    settings = get_settings()
    if settings.llm_provider == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(
            model=settings.llm_model,
            google_api_key=settings.gemini_api_key,
            temperature=0.2,
        )
    from langchain_openai import ChatOpenAI
    return ChatOpenAI(
        model=settings.llm_model,
        api_key=settings.openai_api_key,
        temperature=0.2,
    )


def build_context(session_id: str, question: str):
    results = similarity_search(session_id, question)
    sources = []
    ctx_parts = []
    for i, (doc, score) in enumerate(results, 1):
        ctx_parts.append(
            f"[{i}] {doc.metadata.get('title','')}\n"
            f"URL: {doc.metadata.get('source')}\n"
            f"{doc.page_content}"
        )
        sources.append({
            "index": i,
            "url": doc.metadata.get("source", ""),
            "title": doc.metadata.get("title", ""),
            "snippet": doc.page_content[:300],
            "score": float(score),
        })
    return "\n\n---\n\n".join(ctx_parts), sources


def answer_question(session_id: str, question: str) -> tuple[str, list[dict]]:
    context, sources = build_context(session_id, question)
    if not sources:
        return "I don't have any indexed content for this session yet.", []

    llm = _get_llm()
    prompt = ChatPromptTemplate.from_messages([
        SystemMessage(content=SYSTEM_PROMPT.format(context=context)),
        HumanMessage(content=QA_PROMPT.format(question=question)),
    ])
    response = llm.invoke(prompt)
    return response.content, sources


async def stream_answer(session_id: str, question: str) -> AsyncIterator[str]:
    context, sources = build_context(session_id, question)
    if not sources:
        yield "I don't have any indexed content for this session yet."
        return

    llm = _get_llm()
    prompt = ChatPromptTemplate.from_messages([
        SystemMessage(content=SYSTEM_PROMPT.format(context=context)),
        HumanMessage(content=QA_PROMPT.format(question=question)),
    ])
    async for token in llm.astream(prompt):
        if token.content:
            yield token.content
