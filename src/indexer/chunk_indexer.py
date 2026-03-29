"""Chunk Vector 인덱서 — 두 가지 전략 지원.

1. fixed (기존): 6줄 고정 윈도우, 2줄 overlap — 순수 RAG 기준선
2. semantic (개선): 함수 경계 인식, 파일 유형별 분할, 컨텍스트 프리픽스
"""

from __future__ import annotations

import re
import shutil
from pathlib import Path

import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

CHROMA_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "chroma_db"
COLLECTION_NAME = "proc_chunks"
EMBEDDING_MODEL = "intfloat/multilingual-e5-small"

# 기본 전략
CHUNK_STRATEGY = "semantic"

# fixed 전략 파라미터
FIXED_CHUNK_SIZE = 6
FIXED_CHUNK_OVERLAP = 2

# 함수 시작 패턴: int FUNC_NAME(...)  또는  int FUNC_NAME(
_FUNC_START_RE = re.compile(r"^int\s+([A-Z][A-Z0-9_]+)\s*\(")


# ============================================================
# Fixed 전략 (기존 6줄 윈도우)
# ============================================================

def _chunk_file_fixed(path: Path) -> list[dict]:
    """파일을 6줄 고정 윈도우로 분할."""
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = text.split("\n")
    filename = path.name
    chunks = []
    step = FIXED_CHUNK_SIZE - FIXED_CHUNK_OVERLAP
    for i in range(0, len(lines), step):
        chunk_lines = lines[i : i + FIXED_CHUNK_SIZE]
        if not any(line.strip() for line in chunk_lines):
            continue
        chunks.append({
            "id": f"{filename}:{i+1}-{i+len(chunk_lines)}",
            "text": "\n".join(chunk_lines),
            "metadata": {
                "file": filename,
                "file_type": path.suffix.lstrip("."),
                "start_line": i + 1,
                "end_line": i + len(chunk_lines),
            },
        })
    return chunks


# ============================================================
# Semantic 전략 (함수 경계 인식)
# ============================================================

def _extract_header(lines: list[str]) -> tuple[str, int]:
    """파일 상단의 주석 + #include 영역을 추출. (context prefix용)"""
    header_lines = []
    idx = 0
    for idx, line in enumerate(lines):
        stripped = line.strip()
        # 주석, #include, #define, 빈줄, EXEC SQL INCLUDE
        if (stripped.startswith("/*") or stripped.startswith("*") or
            stripped.startswith("//") or stripped.startswith("#") or
            stripped.startswith("EXEC SQL INCLUDE") or
            stripped == "" or stripped.endswith("*/")):
            header_lines.append(line)
        else:
            break
    return "\n".join(header_lines), idx


def _find_function_boundaries(lines: list[str]) -> list[tuple[int, int, str]]:
    """함수 시작-끝 라인 인덱스와 함수명 추출.

    Returns: [(start_idx, end_idx, func_name), ...]
    """
    functions = []
    i = 0
    while i < len(lines):
        m = _FUNC_START_RE.match(lines[i].strip())
        if m:
            func_name = m.group(1)
            start = i
            # 여는 중괄호 찾기
            brace_depth = 0
            found_open = False
            j = i
            while j < len(lines):
                for ch in lines[j]:
                    if ch == "{":
                        brace_depth += 1
                        found_open = True
                    elif ch == "}":
                        brace_depth -= 1
                if found_open and brace_depth == 0:
                    functions.append((start, j, func_name))
                    i = j + 1
                    break
                j += 1
            else:
                # 닫는 중괄호를 못 찾음 — 파일 끝까지
                functions.append((start, len(lines) - 1, func_name))
                i = len(lines)
            continue
        i += 1
    return functions


def _chunk_pc_semantic(path: Path) -> list[dict]:
    """Pro*C 파일을 함수 단위로 분할. 헤더를 컨텍스트 프리픽스로 포함."""
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = text.split("\n")
    filename = path.name

    header_text, header_end = _extract_header(lines)
    funcs = _find_function_boundaries(lines)

    if not funcs:
        # 함수 경계를 못 찾으면 파일 전체를 하나의 청크로
        return [{
            "id": f"{filename}:1-{len(lines)}",
            "text": text,
            "metadata": {
                "file": filename,
                "file_type": "pc",
                "function_name": "",
                "start_line": 1,
                "end_line": len(lines),
                "has_sql": "EXEC SQL" in text,
            },
        }]

    chunks = []
    for start, end, func_name in funcs:
        # 함수 앞의 주석(설명)도 포함 — 함수 바로 위 주석 블록 탐색
        comment_start = start
        while comment_start > header_end and comment_start > 0:
            prev = lines[comment_start - 1].strip()
            if prev.startswith("/*") or prev.startswith("*") or prev.endswith("*/") or prev == "":
                comment_start -= 1
            else:
                break

        func_lines = lines[comment_start : end + 1]
        func_text = "\n".join(func_lines)

        # 컨텍스트 프리픽스: 파일 헤더 + 함수 본문
        if header_text.strip() and comment_start > header_end:
            chunk_text = header_text.rstrip() + "\n\n" + func_text
        else:
            chunk_text = func_text

        has_sql = "EXEC SQL" in func_text

        chunks.append({
            "id": f"{filename}:{func_name}",
            "text": chunk_text,
            "metadata": {
                "file": filename,
                "file_type": "pc",
                "function_name": func_name,
                "start_line": comment_start + 1,
                "end_line": end + 1,
                "has_sql": has_sql,
            },
        })

    return chunks


def _chunk_header_semantic(path: Path) -> list[dict]:
    """헤더 파일은 전체를 하나의 청크로."""
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = text.split("\n")
    return [{
        "id": f"{path.name}:full",
        "text": text,
        "metadata": {
            "file": path.name,
            "file_type": "h",
            "function_name": "",
            "start_line": 1,
            "end_line": len(lines),
            "has_sql": False,
        },
    }]


def _chunk_sql_semantic(path: Path) -> list[dict]:
    """SQL(DDL) 파일은 전체를 하나의 청크로."""
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = text.split("\n")
    return [{
        "id": f"{path.name}:full",
        "text": text,
        "metadata": {
            "file": path.name,
            "file_type": "sql",
            "function_name": "",
            "start_line": 1,
            "end_line": len(lines),
            "has_sql": True,
        },
    }]


def _chunk_file_semantic(path: Path) -> list[dict]:
    """파일 유형별 semantic chunking 분기."""
    suffix = path.suffix.lower()
    if suffix == ".pc":
        return _chunk_pc_semantic(path)
    elif suffix == ".h":
        return _chunk_header_semantic(path)
    elif suffix == ".sql":
        return _chunk_sql_semantic(path)
    return []


# ============================================================
# 공통 인덱싱 로직
# ============================================================

def index_directory(
    directory: str | Path,
    chroma_dir: str | Path | None = None,
    *,
    reset: bool = True,
    strategy: str | None = None,
) -> chromadb.Collection:
    """디렉토리의 모든 .pc/.h/.sql 파일을 chunk → embed → ChromaDB.

    Args:
        strategy: "fixed" (6줄 윈도우) 또는 "semantic" (함수 경계 인식).
                  None이면 모듈 기본값(CHUNK_STRATEGY) 사용.
    """
    use_strategy = strategy or CHUNK_STRATEGY
    chunk_fn = _chunk_file_semantic if use_strategy == "semantic" else _chunk_file_fixed

    chroma_path = Path(chroma_dir) if chroma_dir else CHROMA_DIR
    if reset and chroma_path.exists():
        shutil.rmtree(chroma_path)
    chroma_path.mkdir(parents=True, exist_ok=True)

    client = chromadb.PersistentClient(path=str(chroma_path))
    ef = SentenceTransformerEmbeddingFunction(model_name=EMBEDDING_MODEL)

    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=ef,
    )

    directory = Path(directory)
    all_chunks = []
    for path in sorted(directory.iterdir()):
        if path.is_file() and path.suffix.lower() in (".pc", ".h", ".sql"):
            all_chunks.extend(chunk_fn(path))

    if not all_chunks:
        return collection

    # ChromaDB는 bool 메타데이터 미지원 — 문자열로 변환
    for c in all_chunks:
        if "has_sql" in c["metadata"]:
            c["metadata"]["has_sql"] = str(c["metadata"]["has_sql"])

    batch_size = 100
    for i in range(0, len(all_chunks), batch_size):
        batch = all_chunks[i : i + batch_size]
        collection.add(
            ids=[c["id"] for c in batch],
            documents=[c["text"] for c in batch],
            metadatas=[c["metadata"] for c in batch],
        )

    return collection
