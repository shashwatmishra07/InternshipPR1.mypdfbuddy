from __future__ import annotations

import hashlib
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import chromadb
from groq import Groq, NotFoundError
from pypdf import PdfReader
from sentence_transformers import SentenceTransformer


EMBEDDING_MODEL = "all-MiniLM-L6-v2"
DEFAULT_GENERATION_MODEL = "openai/gpt-oss-20b"
COLLECTION_NAME = "pdf_chunks_local_embeddings"


@dataclass(frozen=True)
class RetrievedChunk:
    text: str
    source: str
    page: int
    distance: float


def _normalise_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def extract_pdf_pages(pdf_bytes: bytes) -> list[tuple[int, str]]:
    """Extract non-empty text from a PDF, retaining 1-based page numbers."""
    reader = PdfReader(__import__("io").BytesIO(pdf_bytes))
    pages: list[tuple[int, str]] = []
    for page_number, page in enumerate(reader.pages, start=1):
        text = _normalise_text(page.extract_text() or "")
        if text:
            pages.append((page_number, text))
    return pages


def chunk_pages(
    pages: list[tuple[int, str]],
    chunk_size: int = 1200,
    chunk_overlap: int = 200,
) -> list[dict[str, Any]]:
    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than zero.")
    if chunk_overlap < 0 or chunk_overlap >= chunk_size:
        raise ValueError("chunk_overlap must be between zero and chunk_size - 1.")

    chunks: list[dict[str, Any]] = []
    for page_number, text in pages:
        start = 0
        while start < len(text):
            end = min(start + chunk_size, len(text))
            chunk_text = text[start:end].strip()
            if chunk_text:
                chunks.append({"text": chunk_text, "page": page_number})
            if end == len(text):
                break
            start = end - chunk_overlap
    return chunks


class RAGPipeline:
    def __init__(
        self,
        persist_directory: str = "data/chroma",
        collection_name: str = COLLECTION_NAME,
    ) -> None:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise RuntimeError(
                "GROQ_API_KEY is not set. Add it to .env before starting the app."
            )
        self.client = Groq(api_key=api_key)
        self.generation_model = os.getenv(
            "GROQ_MODEL",
            DEFAULT_GENERATION_MODEL,
        )
        self.embedding_model = SentenceTransformer(EMBEDDING_MODEL)
        self.db = chromadb.PersistentClient(path=persist_directory)
        self.collection = self.db.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    def _embed(self, texts: list[str]) -> list[list[float]]:
        embeddings = self.embedding_model.encode(
            texts,
            normalize_embeddings=True,
            convert_to_numpy=False,
        )
        return [embedding.tolist() for embedding in embeddings]

    def ingest_pdf(
        self,
        pdf_bytes: bytes,
        filename: str,
        chunk_size: int = 1200,
        chunk_overlap: int = 200,
    ) -> int:
        pages = extract_pdf_pages(pdf_bytes)
        if not pages:
            raise ValueError("No selectable text was found in this PDF.")

        chunks = chunk_pages(pages, chunk_size, chunk_overlap)
        source_id = hashlib.sha256(pdf_bytes).hexdigest()[:16]
        ids = [f"{source_id}-{index}" for index in range(len(chunks))]
        texts = [chunk["text"] for chunk in chunks]
        embeddings = self._embed(texts)
        metadatas = [
            {
                "source": filename,
                "document_id": source_id,
                "page": chunk["page"],
            }
            for chunk in chunks
        ]

        self.collection.upsert(
            ids=ids,
            documents=texts,
            embeddings=embeddings,
            metadatas=metadatas,
        )
        return len(chunks)

    def retrieve(self, question: str, top_k: int = 5) -> list[RetrievedChunk]:
        if not question.strip():
            return []
        if self.collection.count() == 0:
            return []

        query_embedding = self._embed([question])[0]
        result = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=min(top_k, self.collection.count()),
            include=["documents", "metadatas", "distances"],
        )
        documents = result.get("documents", [[]])[0]
        metadatas = result.get("metadatas", [[]])[0]
        distances = result.get("distances", [[]])[0]
        return [
            RetrievedChunk(
                text=document,
                source=str(metadata.get("source", "Unknown")),
                page=int(metadata.get("page", 0)),
                distance=float(distance),
            )
            for document, metadata, distance in zip(documents, metadatas, distances)
        ]

    def answer(self, question: str, top_k: int = 5) -> tuple[str, list[RetrievedChunk]]:
        chunks = self.retrieve(question, top_k)
        if not chunks:
            return "I could not find any indexed PDF content to answer from.", []

        context = "\n\n".join(
            f"[Source: {chunk.source}, page {chunk.page}]\n{chunk.text}"
            for chunk in chunks
        )
        prompt = f"""You answer questions using only the supplied PDF excerpts.
If the excerpts do not contain the answer, say that you do not know based on the
uploaded documents. Do not invent facts. Keep the answer concise and cite sources
using [filename, page N] format.

PDF excerpts:
{context}

Question: {question}
"""
        try:
            response = self.client.chat.completions.create(
                model=self.generation_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
            )
        except NotFoundError as error:
            raise RuntimeError(
                f"Groq model '{self.generation_model}' is unavailable. "
                "Set GROQ_MODEL in .env to a model enabled for your Groq account."
            ) from error
        answer = response.choices[0].message.content
        return answer or "The model returned an empty answer.", chunks

    def indexed_documents(self) -> list[dict[str, Any]]:
        if self.collection.count() == 0:
            return []
        result = self.collection.get(include=["metadatas"])
        seen: dict[str, dict[str, Any]] = {}
        for metadata in result.get("metadatas", []):
            if metadata:
                document_id = str(metadata["document_id"])
                seen[document_id] = {
                    "source": metadata["source"],
                    "chunks": seen.get(document_id, {}).get("chunks", 0) + 1,
                }
        return list(seen.values())

    def clear_documents(self) -> int:
        count = self.collection.count()
        if count:
            records = self.collection.get()
            ids = records.get("ids", [])
            if ids:
                self.collection.delete(ids=ids)
        return count


def ensure_data_directory(path: str = "data/chroma") -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
