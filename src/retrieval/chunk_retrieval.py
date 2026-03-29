"""Chunk Vector 검색 — ChromaDB top-k.

일반 RAG의 한계를 자연스럽게 드러낸다:
- 6줄 chunk 반환 → 함수 전체 로직 파악 불가
- 도메인 간 유사 변수명(amt, tax, acct_no)으로 노이즈 혼입
- 구조체, DDL, 호출 함수 컨텍스트 누락
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

from ..indexer.chunk_indexer import CHROMA_DIR, COLLECTION_NAME, EMBEDDING_MODEL


@dataclass
class ChunkResult:
    file: str
    start_line: int
    end_line: int
    score: float
    text: str


@dataclass
class ChunkRetrievalResult:
    query: str
    chunks: list[ChunkResult] = field(default_factory=list)
    files_returned: list[str] = field(default_factory=list)


def search(
    query: str,
    top_k: int = 5,
    chroma_dir: str | Path | None = None,
) -> ChunkRetrievalResult:
    """ChromaDB에서 유사도 top-k chunk 검색."""
    chroma_path = Path(chroma_dir) if chroma_dir else CHROMA_DIR
    client = chromadb.PersistentClient(path=str(chroma_path))
    ef = SentenceTransformerEmbeddingFunction(model_name=EMBEDDING_MODEL)
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=ef,
    )

    results = collection.query(
        query_texts=[query],
        n_results=top_k,
    )

    chunks = []
    files = []
    for i in range(len(results["ids"][0])):
        meta = results["metadatas"][0][i]
        distance = results["distances"][0][i]
        # ChromaDB returns L2 distance; convert to similarity score
        score = 1.0 / (1.0 + distance)
        doc = results["documents"][0][i]

        chunks.append(ChunkResult(
            file=meta["file"],
            start_line=meta["start_line"],
            end_line=meta["end_line"],
            score=round(score, 4),
            text=doc,
        ))
        if meta["file"] not in files:
            files.append(meta["file"])

    return ChunkRetrievalResult(
        query=query,
        chunks=chunks,
        files_returned=files,
    )
