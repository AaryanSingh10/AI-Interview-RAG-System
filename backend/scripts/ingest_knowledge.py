"""Ingest knowledge base documents into ChromaDB."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.rag.ingest import ingest_documents


async def main() -> None:
    result = await ingest_documents()
    print("Ingestion complete:")
    for key, value in result.items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    asyncio.run(main())
