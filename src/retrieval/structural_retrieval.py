"""구조 기반 검색 — FTS5 매칭 → 그래프 확장.

1. FTS5로 진입점 함수를 특정
2. 호출 그래프 탐색 (recursive CTE)
3. 사용 테이블의 DDL 수집
4. 관련 구조체 수집
5. 완결된 컨텍스트 반환
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass, field
from pathlib import Path

from ..indexer.db import DEFAULT_DB_PATH, get_connection


@dataclass
class ResolvedFile:
    filename: str
    content: str
    role: str  # "진입점 서비스", "호출 함수", "입출력 구조체", "참조 테이블 DDL"
    relevance: str  # "direct", "dependency"


@dataclass
class CallGraph:
    entry: str
    calls: list[str] = field(default_factory=list)
    called_by: list[str] = field(default_factory=list)


@dataclass
class SearchCandidate:
    name: str
    description: str
    score: int


@dataclass
class StructuralRetrievalResult:
    query: str
    matched_function: str | None = None
    description: str = ""
    candidates: list[SearchCandidate] = field(default_factory=list)
    call_graph: CallGraph | None = None
    resolved_files: list[ResolvedFile] = field(default_factory=list)
    files_returned: list[str] = field(default_factory=list)
    tables_used: list[str] = field(default_factory=list)


def _fts_search(conn: sqlite3.Connection, query: str, limit: int = 3) -> list[dict]:
    """키워드 매칭 기반 진입점 함수 탐색.

    전략:
    1. description + body에서 키워드 매칭 점수 산출 (LIMIT 없이 전체 탐색)
    2. description 매칭 가중치 3×, body 매칭 가중치 1×
    3. 점수 내림차순 정렬 → 상위 limit개 반환
    """
    keywords = [w for w in query.split() if len(w) >= 2]
    if not keywords:
        return []

    # 키워드 중 하나라도 포함하는 함수를 전체 조회 (LIMIT 없음)
    or_desc = " OR ".join(f"description LIKE '%{kw}%'" for kw in keywords)
    or_body = " OR ".join(f"body LIKE '%{kw}%'" for kw in keywords)
    rows = conn.execute(
        f"""SELECT name, description, file_path, body
            FROM functions
            WHERE ({or_desc}) OR ({or_body})""",
    ).fetchall()

    # 점수 산출: description 매칭 ×3, body 매칭 ×1
    scored = []
    for r in rows:
        desc = r["description"] or ""
        body = r["body"] or ""
        desc_score = sum(3 for kw in keywords if kw in desc)
        body_score = sum(1 for kw in keywords if kw in body)
        total = desc_score + body_score
        if total > 0:
            scored.append((total, dict(r)))

    scored.sort(key=lambda x: x[0], reverse=True)
    # 점수도 함께 반환
    for score, item in scored:
        item["_score"] = score
    return [item[1] for item in scored[:limit]]


def _get_call_graph(conn: sqlite3.Connection, func_name: str) -> CallGraph:
    """함수의 직접 호출관계 조회."""
    calls = [
        r["callee"]
        for r in conn.execute(
            "SELECT callee FROM function_calls WHERE caller = ?", (func_name,)
        ).fetchall()
    ]
    called_by = [
        r["caller"]
        for r in conn.execute(
            "SELECT caller FROM function_calls WHERE callee = ?", (func_name,)
        ).fetchall()
    ]
    return CallGraph(entry=func_name, calls=calls, called_by=called_by)


def _get_transitive_calls(conn: sqlite3.Connection, func_name: str, depth: int = 2) -> list[str]:
    """재귀적 호출 추적 (depth 제한)."""
    rows = conn.execute(
        """
        WITH RECURSIVE call_tree(callee, depth) AS (
            SELECT callee, 1 FROM function_calls WHERE caller = ?
            UNION ALL
            SELECT fc.callee, ct.depth + 1
            FROM function_calls fc
            JOIN call_tree ct ON fc.caller = ct.callee
            WHERE ct.depth < ?
        )
        SELECT DISTINCT callee FROM call_tree
        """,
        (func_name, depth),
    ).fetchall()
    return [r["callee"] for r in rows]


def _resolve_context(
    conn: sqlite3.Connection, func_name: str
) -> list[ResolvedFile]:
    """함수의 완전한 컨텍스트 수집: 본문 + 구조체 + 호출함수 + DDL."""
    files = []

    # 1. 메인 함수 본문
    fn = conn.execute(
        "SELECT * FROM functions WHERE name = ?", (func_name,)
    ).fetchone()
    if fn:
        files.append(ResolvedFile(
            filename=fn["file_path"],
            content=fn["body"],
            role="진입점 서비스",
            relevance="direct",
        ))

    # 2. 관련 구조체 (include 기반 + 이름 매칭)
    if fn:
        includes = json.loads(fn["includes"]) if fn["includes"] else []
        for inc in includes:
            if inc in ("proframe.h",):
                continue
            st = conn.execute(
                "SELECT * FROM structs WHERE file_path = ?", (inc,)
            ).fetchone()
            if st:
                fields = json.loads(st["fields"]) if st["fields"] else []
                content = f"/* {st['description']} */\n"
                content += f"typedef struct {{\n"
                for f in fields:
                    line = f"    {f['c_type']} {f['name']}"
                    if f.get("size"):
                        line += f"[{f['size']}]"
                    line += ";"
                    if f.get("comment"):
                        line += f"    /* {f['comment']} */"
                    content += line + "\n"
                content += f"}} {st['name']};"
                files.append(ResolvedFile(
                    filename=st["file_path"],
                    content=content,
                    role="입출력 구조체",
                    relevance="direct",
                ))

    # 3. 호출 함수 (재귀)
    callees = _get_transitive_calls(conn, func_name)
    for callee_name in callees:
        callee = conn.execute(
            "SELECT * FROM functions WHERE name = ?", (callee_name,)
        ).fetchone()
        if callee:
            files.append(ResolvedFile(
                filename=callee["file_path"],
                content=callee["body"],
                role=f"호출 함수 ({callee_name})",
                relevance="dependency",
            ))

    # 4. 사용 테이블 DDL
    tables = conn.execute(
        "SELECT DISTINCT table_name FROM sql_usage WHERE function_name = ?",
        (func_name,),
    ).fetchall()
    # 호출 함수의 테이블도 수집
    for callee_name in callees:
        callee_tables = conn.execute(
            "SELECT DISTINCT table_name FROM sql_usage WHERE function_name = ?",
            (callee_name,),
        ).fetchall()
        tables.extend(callee_tables)

    seen_tables = set()
    for row in tables:
        tname = row["table_name"]
        if tname in seen_tables:
            continue
        seen_tables.add(tname)
        ddl = conn.execute(
            "SELECT * FROM tables_ddl WHERE name = ?", (tname,)
        ).fetchone()
        if ddl:
            cols = json.loads(ddl["columns"]) if ddl["columns"] else []
            col_lines = []
            for c in cols:
                line = f"    {c['name']}  {c['data_type']}"
                if not c.get("nullable", True):
                    line += "  NOT NULL"
                col_lines.append(line)
            pk = json.loads(ddl["primary_key"]) if ddl["primary_key"] else []
            ddl_text = f"CREATE TABLE {tname} (\n"
            ddl_text += ",\n".join(col_lines)
            if pk:
                ddl_text += f",\n    PRIMARY KEY ({', '.join(pk)})"
            ddl_text += "\n);"
            if ddl["comment"]:
                ddl_text += f"\n-- {ddl['comment']}"
            files.append(ResolvedFile(
                filename=ddl["file_path"],
                content=ddl_text,
                role=f"참조 테이블 DDL ({tname})",
                relevance="dependency",
            ))

    return files


def search(
    query: str,
    db_path: str | Path | None = None,
) -> StructuralRetrievalResult:
    """구조 기반 검색 메인."""
    conn = get_connection(db_path)

    # FTS5 + LIKE 하이브리드로 진입점 함수 특정 (상위 3개 후보)
    matches = _fts_search(conn, query, limit=3)

    if not matches:
        conn.close()
        return StructuralRetrievalResult(query=query)

    func_name = matches[0]["name"]
    description = matches[0].get("description", "")

    # 후보 목록 (상위 3개)
    candidates = [
        SearchCandidate(
            name=m["name"],
            description=m.get("description", ""),
            score=m.get("_score", 0),
        )
        for m in matches
    ]

    call_graph = _get_call_graph(conn, func_name)
    resolved = _resolve_context(conn, func_name)

    files_returned = []
    tables_used = []
    for f in resolved:
        if f.filename not in files_returned:
            files_returned.append(f.filename)
    for row in conn.execute(
        "SELECT DISTINCT table_name FROM sql_usage WHERE function_name = ?", (func_name,)
    ).fetchall():
        tables_used.append(row["table_name"])

    conn.close()

    return StructuralRetrievalResult(
        query=query,
        matched_function=func_name,
        description=description,
        candidates=candidates,
        call_graph=call_graph,
        resolved_files=resolved,
        files_returned=files_returned,
        tables_used=tables_used,
    )
