import re
from dataclasses import dataclass


@dataclass
class DocumentChunk:
    text: str
    source: str
    role_tags: list[str]
    topic: str
    chunk_index: int


def chunk_text(
    text: str,
    source: str,
    role_tags: list[str],
    topic: str,
    chunk_size: int = 800,
    chunk_overlap: int = 150,
) -> list[DocumentChunk]:
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    if not paragraphs:
        return []

    chunks: list[DocumentChunk] = []
    buffer = ""
    chunk_index = 0

    for paragraph in paragraphs:
        candidate = f"{buffer}\n\n{paragraph}".strip() if buffer else paragraph
        if len(candidate) <= chunk_size:
            buffer = candidate
            continue

        if buffer:
            chunks.append(
                DocumentChunk(
                    text=buffer,
                    source=source,
                    role_tags=role_tags,
                    topic=topic,
                    chunk_index=chunk_index,
                )
            )
            chunk_index += 1
            overlap = buffer[-chunk_overlap:] if len(buffer) > chunk_overlap else buffer
            buffer = f"{overlap}\n\n{paragraph}".strip()
        else:
            for i in range(0, len(paragraph), chunk_size - chunk_overlap):
                piece = paragraph[i : i + chunk_size]
                chunks.append(
                    DocumentChunk(
                        text=piece,
                        source=source,
                        role_tags=role_tags,
                        topic=topic,
                        chunk_index=chunk_index,
                    )
                )
                chunk_index += 1
            buffer = ""

    if buffer:
        chunks.append(
            DocumentChunk(
                text=buffer,
                source=source,
                role_tags=role_tags,
                topic=topic,
                chunk_index=chunk_index,
            )
        )

    return chunks
