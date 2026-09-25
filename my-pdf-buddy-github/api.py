from __future__ import annotations

import os
from functools import lru_cache

from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from rag_pipeline import RAGPipeline, ensure_data_directory


load_dotenv()

app = FastAPI(title="My PDF Buddy API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@lru_cache(maxsize=1)
def get_pipeline() -> RAGPipeline:
    persist_directory = os.getenv("CHROMA_PATH", "data/chroma")
    ensure_data_directory(persist_directory)
    return RAGPipeline(persist_directory=persist_directory)


class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=4000)
    top_k: int = Field(default=5, ge=1, le=10)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/documents")
def documents() -> dict[str, list[dict[str, object]]]:
    try:
        return {"documents": get_pipeline().indexed_documents()}
    except RuntimeError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error


@app.post("/api/documents")
async def upload_document(
    file: UploadFile = File(...),
    chunk_size: int = Form(default=1200),
    chunk_overlap: int = Form(default=200),
) -> dict[str, object]:
    if file.content_type not in {"application/pdf", "application/octet-stream"}:
        raise HTTPException(status_code=415, detail="Only PDF files are supported.")
    if chunk_size < 500 or chunk_size > 2500:
        raise HTTPException(status_code=422, detail="chunk_size must be 500-2500.")
    if chunk_overlap < 0 or chunk_overlap >= chunk_size:
        raise HTTPException(
            status_code=422,
            detail="chunk_overlap must be less than chunk_size.",
        )

    pdf_bytes = await file.read()
    if not pdf_bytes:
        raise HTTPException(status_code=400, detail="The uploaded file is empty.")

    try:
        count = get_pipeline().ingest_pdf(
            pdf_bytes,
            file.filename or "uploaded.pdf",
            chunk_size,
            chunk_overlap,
        )
    except (ValueError, RuntimeError) as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    return {
        "filename": file.filename or "uploaded.pdf",
        "chunks": count,
        "message": "Your PDF is ready to chat with.",
    }


@app.delete("/api/documents")
def delete_documents() -> dict[str, object]:
    try:
        deleted_chunks = get_pipeline().clear_documents()
    except RuntimeError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    return {
        "deleted_chunks": deleted_chunks,
        "message": "All uploaded PDF data has been erased.",
    }


@app.post("/api/chat")
def chat(request: ChatRequest) -> dict[str, object]:
    try:
        answer, chunks = get_pipeline().answer(request.question, request.top_k)
    except (RuntimeError, ValueError) as error:
        raise HTTPException(status_code=502, detail=str(error)) from error
    return {
        "answer": answer,
        "sources": [
            {
                "source": chunk.source,
                "page": chunk.page,
                "distance": chunk.distance,
            }
            for chunk in chunks
        ],
    }
