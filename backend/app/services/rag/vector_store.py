from __future__ import annotations

import json
import math
import sqlite3
import uuid
from pathlib import Path
from typing import Any

from app.config import settings
from app.services.llm_client import llm_client
from app.services.rag.chunker import DocumentChunk


class VectorStore:
    """SQLite-backed vector index with cosine similarity retrieval."""

    def __init__(self) -> None:
        self.db_path = Path(settings.chroma_path) / "vectors.db"
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS chunks (
                    id TEXT PRIMARY KEY,
                    text TEXT NOT NULL,
                    source TEXT NOT NULL,
                    role_tags TEXT NOT NULL,
                    topic TEXT NOT NULL,
                    chunk_index INTEGER NOT NULL,
                    embedding TEXT NOT NULL
                )
                """
            )
            conn.commit()

    async def upsert_chunks(self, chunks: list[DocumentChunk]) -> int:
        if not chunks:
            return 0

        texts = [chunk.text for chunk in chunks]
        embeddings = await llm_client.embed(texts)

        with self._connect() as conn:
            for chunk, embedding in zip(chunks, embeddings):
                conn.execute(
                    """
                    INSERT OR REPLACE INTO chunks
                    (id, text, source, role_tags, topic, chunk_index, embedding)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        str(uuid.uuid4()),
                        chunk.text,
                        chunk.source,
                        ",".join(chunk.role_tags),
                        chunk.topic,
                        chunk.chunk_index,
                        json.dumps(embedding),
                    ),
                )
            conn.commit()
        return len(chunks)

    def count(self) -> int:
        with self._connect() as conn:
            row = conn.execute("SELECT COUNT(*) AS c FROM chunks").fetchone()
            return int(row["c"]) if row else 0

    async def retrieve(
        self,
        query: str,
        role_id: str,
        top_k: int | None = None,
    ) -> list[dict[str, Any]]:
        top_k = top_k or settings.retrieval_top_k
        query_embedding = (await llm_client.embed([query]))[0]

        with self._connect() as conn:
            rows = conn.execute(
                "SELECT id, text, source, role_tags, topic, chunk_index, embedding FROM chunks"
            ).fetchall()

        scored: list[dict[str, Any]] = []
        for row in rows:
            embedding = json.loads(row["embedding"])
            distance = 1.0 - _cosine_similarity(query_embedding, embedding)
            role_tags = row["role_tags"].split(",")
            role_boost = 0.0 if role_id in role_tags else 0.15
            scored.append(
                {
                    "text": row["text"],
                    "metadata": {
                        "source": row["source"],
                        "role_tags": row["role_tags"],
                        "topic": row["topic"],
                        "chunk_index": row["chunk_index"],
                    },
                    "distance": distance + role_boost,
                }
            )

        scored.sort(key=lambda item: item["distance"])
        return scored[:top_k]


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    if len(a) != len(b):
        size = min(len(a), len(b))
        a = a[:size]
        b = b[:size]
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


vector_store = VectorStore()
