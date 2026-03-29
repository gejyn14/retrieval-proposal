"""하이브리드 검색 — Vector 초기 매칭 → Structural 확장.

1. Vector로 후보 chunk 매칭
2. chunk에서 함수명 추출
3. Structural로 매칭된 함수의 전체 컨텍스트 확장
→ vector의 유연한 매칭 + structural의 완결 컨텍스트
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from . import chunk_retrieval, structural_retrieval


@dataclass
class HybridRetrievalResult:
    query: str
    vector_candidates: list[str] = field(default_factory=list)  # 후보 함수명
    selected_function: str | None = None
    description: str = ""
    call_graph: structural_retrieval.CallGraph | None = None
    resolved_files: list[structural_retrieval.ResolvedFile] = field(default_factory=list)
    files_returned: list[str] = field(default_factory=list)

# Pro*C 함수명 패턴
RE_FUNC_NAME = re.compile(r"\b([A-Z][A-Z0-9_]{3,})\b")
C_BUILTINS = {
    "EXEC", "SQL", "BEGIN", "END", "DECLARE", "SECTION", "SELECT", "INSERT",
    "UPDATE", "DELETE", "FROM", "WHERE", "INTO", "SET", "VALUES", "AND", "OR",
    "NOT", "NULL", "BETWEEN", "ORDER", "SYSDATE", "DUAL", "NEXTVAL",
    "CURRVAL", "LPAD", "SUM", "COUNT", "CONSTRAINT", "PRIMARY", "KEY",
    "DEFAULT", "CREATE", "TABLE", "COMMENT", "OPEN", "CLOSE", "FETCH",
    "CURSOR", "INCLUDE", "SQLCA", "SUCCESS", "FAIL", "VARCHAR2", "NUMBER",
    "CHAR", "TO_CHAR", "TO_DATE",
}


def _extract_function_names_from_chunks(chunks: list[chunk_retrieval.ChunkResult]) -> list[str]:
    """chunk 텍스트에서 Pro*C 함수명 후보 추출."""
    candidates = {}
    for chunk in chunks:
        for m in RE_FUNC_NAME.finditer(chunk.text):
            name = m.group(1)
            if name not in C_BUILTINS and name.startswith(("TB_", "SQ_")) is False:
                if name not in candidates:
                    candidates[name] = chunk.score
                else:
                    candidates[name] = max(candidates[name], chunk.score)
    # 점수순 정렬
    return sorted(candidates, key=lambda n: candidates[n], reverse=True)


def search(
    query: str,
    top_k: int = 5,
    chroma_dir: str | Path | None = None,
    db_path: str | Path | None = None,
) -> HybridRetrievalResult:
    """하이브리드 검색 메인."""
    # 1. Vector로 후보 chunk 검색
    vec_result = chunk_retrieval.search(query, top_k=top_k, chroma_dir=chroma_dir)

    # 2. chunk에서 함수명 후보 추출
    candidates = _extract_function_names_from_chunks(vec_result.chunks)

    if not candidates:
        return HybridRetrievalResult(query=query)

    # 3. 최상위 후보를 Structural로 확장
    best_candidate = candidates[0]
    struct_result = structural_retrieval.search(best_candidate, db_path=db_path)

    # structural이 매칭 못하면 FTS로 원래 쿼리 시도
    if not struct_result.matched_function:
        struct_result = structural_retrieval.search(query, db_path=db_path)

    return HybridRetrievalResult(
        query=query,
        vector_candidates=candidates[:5],
        selected_function=struct_result.matched_function,
        description=struct_result.description,
        call_graph=struct_result.call_graph,
        resolved_files=struct_result.resolved_files,
        files_returned=struct_result.files_returned,
    )
