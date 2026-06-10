from pathlib import Path

from app.config import settings
from app.services.rag.chunker import chunk_text
from app.services.rag.vector_store import vector_store

ROLE_TOPIC_MAP = {
    "ml_engineer": [
        "Supervised Learning",
        "Model Evaluation",
        "Feature Engineering",
        "Ensemble Methods",
        "MLOps Basics",
        "Regularization",
    ],
    "data_scientist": [
        "Exploratory Data Analysis",
        "Statistical Inference",
        "Classification",
        "Clustering",
        "Model Interpretability",
        "Experiment Design",
    ],
    "ml_researcher": [
        "Learning Theory",
        "Optimization",
        "Neural Networks",
        "Probabilistic Models",
        "Generalization",
        "Research Methodology",
    ],
    "ai_engineer": [
        "NLP Fundamentals",
        "Embeddings & Retrieval",
        "Prompt Engineering",
        "Model Serving",
        "RAG Systems",
        "Evaluation Metrics",
    ],
}


def _infer_roles_from_filename(filename: str) -> list[str]:
    lower = filename.lower()
    if "mitchell" in lower:
        return ["ml_engineer", "ml_researcher", "data_scientist"]
    if "hundred" in lower or "100" in lower:
        return ["ml_engineer", "data_scientist", "ai_engineer"]
    if "python" in lower or "muller" in lower or "raschka" in lower:
        return ["ml_engineer", "data_scientist"]
    if "prml" in lower or "bishop" in lower or "pattern" in lower:
        return ["ml_researcher", "ml_engineer"]
    return list(ROLE_TOPIC_MAP.keys())


async def ingest_documents(knowledge_path: str | None = None) -> dict[str, int]:
    base = Path(knowledge_path or settings.knowledge_base_path).resolve()
    if not base.exists():
        raise FileNotFoundError(f"Knowledge base path not found: {base}")

    total_chunks = 0
    files_processed = 0

    for file_path in sorted(base.glob("**/*")):
        if not file_path.is_file() or file_path.suffix.lower() not in {".txt", ".md"}:
            continue

        text = file_path.read_text(encoding="utf-8", errors="ignore")
        role_tags = _infer_roles_from_filename(file_path.name)
        source = file_path.name

        file_chunks = []
        for role_id in role_tags:
            topics = ROLE_TOPIC_MAP.get(role_id, ["General ML"])
            topic = topics[files_processed % len(topics)]
            file_chunks.extend(
                chunk_text(
                    text=text,
                    source=source,
                    role_tags=[role_id],
                    topic=topic,
                    chunk_size=settings.chunk_size,
                    chunk_overlap=settings.chunk_overlap,
                )
            )

        inserted = await vector_store.upsert_chunks(file_chunks)
        total_chunks += inserted
        files_processed += 1

    return {
        "files_processed": files_processed,
        "chunks_indexed": total_chunks,
        "collection_size": vector_store.count(),
    }
