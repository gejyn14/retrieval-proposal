"""Shared retrieval service — MCP + API 공통 진입점.

모든 검색 로직은 이 서비스를 통해 호출된다.
MCP 서버와 FastAPI 서버 모두 이 모듈을 사용.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent

import os
_USE_LARGE = os.environ.get("USE_LARGE_CODEBASE", "1") == "1"

if _USE_LARGE and (ROOT / "data" / "structural_large.db").exists():
    DB_PATH = ROOT / "data" / "structural_large.db"
    CHROMA_DIR = ROOT / "data" / "chroma_db_large"
    CODEBASE_ROOT = Path(os.environ.get("CODEBASE_ROOT", str(ROOT / "data" / "large_codebase")))
else:
    DB_PATH = ROOT / "data" / "structural.db"
    CHROMA_DIR = ROOT / "data" / "chroma_db"
    CODEBASE_ROOT = Path(os.environ.get("CODEBASE_ROOT", str(ROOT / "data" / "sample_codebase")))

from ..indexer.db import get_connection
from . import chunk_retrieval, structural_retrieval, hybrid_retrieval
from ..evaluation.ground_truth import GROUND_TRUTH
from ..evaluation.evaluator import evaluate


# ── Individual Search ──

def search_chunk(query: str, top_k: int = 7) -> dict:
    """Chunk vector top-k 검색."""
    result = chunk_retrieval.search(query, top_k=top_k, chroma_dir=CHROMA_DIR)
    return {
        "chunks": [
            {
                "file": c.file,
                "start_line": c.start_line,
                "end_line": c.end_line,
                "score": c.score,
                "text": c.text,
            }
            for c in result.chunks
        ],
        "files_returned": result.files_returned,
    }


def search_structural(query: str) -> dict:
    """구조 기반 검색 — FTS5 매칭 → 그래프 확장. 파일 경로만 반환 (코드 body 미포함)."""
    result = structural_retrieval.search(query, db_path=DB_PATH)
    call_graph = None
    if result.call_graph:
        cg = result.call_graph
        call_graph = {
            "entry": cg.entry,
            "calls": cg.calls,
            "called_by": cg.called_by,
        }
    return {
        "matched_function": result.matched_function,
        "description": result.description,
        "tables_used": result.tables_used,
        "call_graph": call_graph,
        "candidates": [
            {"name": c.name, "description": c.description, "score": c.score}
            for c in result.candidates
        ],
        "related_files": [
            {"filename": f.filename, "role": f.role}
            for f in result.resolved_files
        ],
    }


def search_hybrid(query: str, top_k: int = 5) -> dict:
    """하이브리드 — Vector 초기매칭 → Structural 확장."""
    result = hybrid_retrieval.search(query, top_k=top_k, chroma_dir=CHROMA_DIR, db_path=DB_PATH)
    call_graph = None
    if result.call_graph:
        cg = result.call_graph
        call_graph = {
            "entry": cg.entry,
            "calls": cg.calls,
            "called_by": cg.called_by,
        }
    return {
        "selected_function": result.selected_function,
        "description": result.description,
        "vector_candidates": result.vector_candidates,
        "call_graph": call_graph,
        "files": [
            {
                "filename": f.filename,
                "content": f.content,
                "role": f.role,
                "relevance": f.relevance,
            }
            for f in result.resolved_files
        ],
        "files_returned": result.files_returned,
    }


# ── Full Comparison (Visual Demo) ──

def search_full(query: str) -> dict:
    """Chunk + Structural 동시 검색 + 평가. API 서버용."""
    gt = GROUND_TRUTH.get(query, {})
    noise_set = set(gt.get("noise_files", []))
    required_set = set(gt.get("required_files", []))
    has_gt = bool(gt)

    # Chunk
    chunk = search_chunk(query)
    chunk_eval = evaluate(query, "chunk", chunk["files_returned"])
    for item in chunk["chunks"]:
        item["is_noise"] = item["file"] in noise_set
        item["is_relevant"] = item["file"] in required_set

    # Structural
    struct = search_structural(query)
    struct_eval = evaluate(query, "structural", struct["files_returned"])
    for f in struct["files"]:
        f["is_relevant"] = f["filename"] in required_set

    def _metrics(ev):
        return {
            "precision": ev.precision,
            "recall": ev.recall,
            "noise_ratio": ev.noise_ratio,
            "context_completeness": ev.context_completeness,
            "has_function_body": ev.has_function_body,
            "has_structs": ev.has_structs,
            "has_called_functions": ev.has_called_functions,
            "has_table_ddl": ev.has_table_ddl,
        }

    return {
        "query": query,
        "has_ground_truth": has_gt,
        "ground_truth": {
            "target_function": gt.get("target_function"),
            "required_files": gt.get("required_files", []),
            "categories": gt.get("context_categories", {}),
        },
        "chunk": {
            "items": chunk["chunks"],
            "files_returned": chunk["files_returned"],
            "metrics": _metrics(chunk_eval),
            "missing_files": chunk_eval.missing_files,
            "noise_files": chunk_eval.noise_files,
        },
        "structural": {
            "matched_function": struct["matched_function"],
            "description": struct["description"],
            "call_graph": struct["call_graph"],
            "files": struct["files"],
            "files_returned": struct["files_returned"],
            "metrics": _metrics(struct_eval),
            "missing_files": struct_eval.missing_files,
            "noise_files": struct_eval.noise_files,
        },
    }


# ── Function Detail ──

def _to_abs(rel_path: str) -> str:
    """상대경로 → CODEBASE_ROOT 기준 절대경로."""
    return str(CODEBASE_ROOT / rel_path)


def get_function_detail(name: str) -> dict | None:
    """함수명으로 구조 정보 + 의존 파일 절대경로. (코드 body 미포함)"""
    conn = get_connection(DB_PATH)
    fn = conn.execute("SELECT * FROM functions WHERE name = ?", (name,)).fetchone()
    if not fn:
        conn.close()
        return None

    tables = json.loads(fn["tables_used"]) if fn["tables_used"] else []
    includes = json.loads(fn["includes"]) if fn["includes"] else []

    call_graph_obj = structural_retrieval._get_call_graph(conn, name)
    call_graph = {"calls": call_graph_obj.calls, "called_by": call_graph_obj.called_by}

    # 의존 파일 경로 수집 — 절대경로로 반환
    struct_files = [_to_abs(inc) for inc in includes if inc != "proframe.h"]
    callee_files = []
    for callee in call_graph_obj.calls:
        row = conn.execute("SELECT file_path FROM functions WHERE name = ?", (callee,)).fetchone()
        if row:
            callee_files.append(_to_abs(row["file_path"]))

    ddl_files = []
    for tbl in tables:
        row = conn.execute("SELECT file_path FROM tables_ddl WHERE name = ?", (tbl,)).fetchone()
        if row:
            ddl_files.append(_to_abs(row["file_path"]))

    conn.close()
    return {
        "name": name,
        "file_path": _to_abs(fn["file_path"]),
        "description": fn["description"],
        "tables": tables,
        "call_graph": call_graph,
        "struct_files": struct_files,
        "dependency_files": callee_files,
        "ddl_files": ddl_files,
    }


# ── Call Graph ──

def get_call_graph_data(name: str, depth: int = 2) -> dict:
    """호출 그래프 트리."""
    conn = get_connection(DB_PATH)

    rows = conn.execute(
        """
        WITH RECURSIVE call_tree(callee, caller, depth) AS (
            SELECT callee, caller, 1 FROM function_calls WHERE caller = ?
            UNION ALL
            SELECT fc.callee, fc.caller, ct.depth + 1
            FROM function_calls fc
            JOIN call_tree ct ON fc.caller = ct.callee
            WHERE ct.depth < ?
        )
        SELECT callee, caller, depth FROM call_tree ORDER BY depth, caller
        """,
        (name, depth),
    ).fetchall()

    callers = conn.execute(
        "SELECT caller FROM function_calls WHERE callee = ?", (name,)
    ).fetchall()
    conn.close()

    return {
        "name": name,
        "called_by": [r["caller"] for r in callers],
        "calls": [{"callee": r["callee"], "caller": r["caller"], "depth": r["depth"]} for r in rows],
    }


# ── Table Lookup ──

def find_functions_by_table(table_name: str) -> dict:
    """테이블을 참조하는 모든 함수."""
    conn = get_connection(DB_PATH)

    rows = conn.execute(
        "SELECT function_name, operation FROM sql_usage WHERE table_name = ? ORDER BY function_name",
        (table_name,),
    ).fetchall()

    ddl = conn.execute(
        "SELECT * FROM tables_ddl WHERE name = ?", (table_name,)
    ).fetchone()
    conn.close()

    ddl_info = None
    if ddl:
        cols = json.loads(ddl["columns"]) if ddl["columns"] else []
        ddl_info = {"comment": ddl["comment"], "columns": cols}

    return {
        "table_name": table_name,
        "ddl": ddl_info,
        "usages": [{"function_name": r["function_name"], "operation": r["operation"]} for r in rows],
    }


# ── Impact Analysis ──

def get_impact_data(name: str, depth: int = 5) -> dict:
    """영향도 분석 — 이 함수/테이블을 수정하면 어디가 영향 받는지."""
    conn = get_connection(DB_PATH)

    # 함수인지 테이블인지 판별
    fn = conn.execute("SELECT name, description FROM functions WHERE name = ?", (name,)).fetchone()
    tbl = conn.execute("SELECT name, comment FROM tables_ddl WHERE name = ?", (name,)).fetchone()

    if fn:
        # 역방향 재귀: 이 함수를 호출하는 모든 상위 함수
        rows = conn.execute(
            """
            WITH RECURSIVE impact_tree(caller, callee, depth) AS (
                SELECT caller, callee, 1 FROM function_calls WHERE callee = ?
                UNION ALL
                SELECT fc.caller, fc.callee, it.depth + 1
                FROM function_calls fc
                JOIN impact_tree it ON fc.callee = it.caller
                WHERE it.depth < ?
            )
            SELECT DISTINCT caller, depth FROM impact_tree ORDER BY depth, caller
            """,
            (name, depth),
        ).fetchall()

        # 이 함수가 사용하는 테이블
        tables = conn.execute(
            "SELECT DISTINCT table_name, operation FROM sql_usage WHERE function_name = ?",
            (name,),
        ).fetchall()

        # 영향 받는 함수들의 설명 조회
        affected = []
        for r in rows:
            desc_row = conn.execute(
                "SELECT description FROM functions WHERE name = ?", (r["caller"],)
            ).fetchone()
            affected.append({
                "name": r["caller"],
                "depth": r["depth"],
                "description": desc_row["description"] if desc_row else "",
            })

        conn.close()
        return {
            "type": "function",
            "name": name,
            "description": fn["description"],
            "affected_services": affected,
            "affected_count": len(affected),
            "tables_used": [{"table": r["table_name"], "operation": r["operation"]} for r in tables],
        }

    elif tbl:
        # 테이블: 이 테이블을 사용하는 모든 함수 + 그 함수의 상위 호출자
        direct_users = conn.execute(
            "SELECT DISTINCT function_name, operation FROM sql_usage WHERE table_name = ? ORDER BY function_name",
            (name,),
        ).fetchall()

        affected = []
        seen = set()
        for user in direct_users:
            fn_desc = conn.execute(
                "SELECT description FROM functions WHERE name = ?", (user["function_name"],)
            ).fetchone()
            if user["function_name"] not in seen:
                seen.add(user["function_name"])
                affected.append({
                    "name": user["function_name"],
                    "operation": user["operation"],
                    "depth": 0,  # 직접 사용
                    "description": fn_desc["description"] if fn_desc else "",
                })

            # 이 함수를 호출하는 상위 함수도 추적
            callers = conn.execute(
                """
                WITH RECURSIVE impact_tree(caller, depth) AS (
                    SELECT caller, 1 FROM function_calls WHERE callee = ?
                    UNION ALL
                    SELECT fc.caller, it.depth + 1
                    FROM function_calls fc
                    JOIN impact_tree it ON fc.callee = it.caller
                    WHERE it.depth < ?
                )
                SELECT DISTINCT caller, depth FROM impact_tree ORDER BY depth
                """,
                (user["function_name"], depth),
            ).fetchall()

            for c in callers:
                if c["caller"] not in seen:
                    seen.add(c["caller"])
                    c_desc = conn.execute(
                        "SELECT description FROM functions WHERE name = ?", (c["caller"],)
                    ).fetchone()
                    affected.append({
                        "name": c["caller"],
                        "operation": "indirect",
                        "depth": c["depth"],
                        "description": c_desc["description"] if c_desc else "",
                    })

        conn.close()
        return {
            "type": "table",
            "name": name,
            "comment": tbl["comment"],
            "affected_services": affected,
            "affected_count": len(affected),
        }

    conn.close()
    return {"type": "unknown", "name": name, "affected_services": [], "affected_count": 0}


# ── Error Code Search ──

def find_by_error_code_data(error_code: str) -> dict:
    """에러 코드가 설정되는 함수와 메시지, 주변 맥락을 찾는다."""
    conn = get_connection(DB_PATH)

    # body에서 에러 코드 LIKE 검색
    rows = conn.execute(
        "SELECT name, file_path, body FROM functions WHERE body LIKE ?",
        (f'%"{error_code}"%',),
    ).fetchall()

    occurrences = []
    for r in rows:
        body = r["body"]
        lines = body.split("\n")

        # 에러 코드가 포함된 라인 찾기
        for i, line in enumerate(lines):
            if f'"{error_code}"' in line:
                # 주변 컨텍스트 (앞 2줄, 뒤 3줄)
                start = max(0, i - 2)
                end = min(len(lines), i + 4)
                context = "\n".join(lines[start:end])

                # 에러 메시지 추출 (같은 블록에서 err_msg 찾기)
                err_msg = ""
                for j in range(i, min(i + 5, len(lines))):
                    if "err_msg" in lines[j]:
                        import re
                        m = re.search(r'"([^"]+)"', lines[j])
                        if m:
                            err_msg = m.group(1)
                        break

                occurrences.append({
                    "function_name": r["name"],
                    "file_path": r["file_path"],
                    "error_message": err_msg,
                    "context": context,
                    "line_no": i + 1,
                })
                break  # 함수당 첫 번째 매칭만

    conn.close()
    return {"error_code": error_code, "occurrences": occurrences}


# ── Business Flow ──

def get_business_flow_data(entry_function: str, depth: int = 5) -> dict:
    """진입점 함수부터 call graph + SQL 연산을 인터리빙한 업무 흐름."""
    conn = get_connection(DB_PATH)

    fn = conn.execute(
        "SELECT name, description FROM functions WHERE name = ?",
        (entry_function,),
    ).fetchone()
    if not fn:
        conn.close()
        return {"entry": entry_function, "description": "", "steps": [], "tables_touched": []}

    tables_touched = set()

    def _build_steps(func_name: str, current_depth: int) -> list[dict]:
        if current_depth > depth:
            return []

        # 함수 설명
        row = conn.execute(
            "SELECT description FROM functions WHERE name = ?", (func_name,)
        ).fetchone()
        desc = row["description"] if row else ""

        # SQL 연산
        sql_ops = conn.execute(
            "SELECT DISTINCT table_name, operation FROM sql_usage WHERE function_name = ?",
            (func_name,),
        ).fetchall()
        sql_list = []
        for s in sql_ops:
            sql_list.append({"table": s["table_name"], "operation": s["operation"]})
            tables_touched.add(s["table_name"])

        step = {
            "name": func_name,
            "description": desc,
            "depth": current_depth,
            "sql_operations": sql_list,
        }

        steps = [step]

        # 하위 호출 재귀
        callees = conn.execute(
            "SELECT callee FROM function_calls WHERE caller = ?", (func_name,)
        ).fetchall()
        for c in callees:
            # CM_LOG_01 같은 유틸은 흐름에서 제외
            if c["callee"] in ("CM_LOG_01",):
                continue
            steps.extend(_build_steps(c["callee"], current_depth + 1))

        return steps

    steps = _build_steps(entry_function, 0)

    conn.close()
    return {
        "entry": entry_function,
        "description": fn["description"],
        "steps": steps,
        "tables_touched": sorted(tables_touched),
    }


# ── Domain Search ──

def search_by_domain_data(domain: str) -> dict:
    """도메인 프리픽스로 함수/테이블/구조체 조회."""
    conn = get_connection(DB_PATH)
    domain_upper = domain.upper()

    functions = conn.execute(
        "SELECT name, description FROM functions WHERE name LIKE ? ORDER BY name",
        (f"{domain_upper}_%",),
    ).fetchall()

    tables = conn.execute(
        "SELECT name, comment FROM tables_ddl WHERE name LIKE ? ORDER BY name",
        (f"TB_{domain_upper}%",),
    ).fetchall()

    structs = conn.execute(
        "SELECT name, file_path FROM structs WHERE file_path LIKE ? ORDER BY name",
        (f"{domain_upper.lower()}_%",),
    ).fetchall()

    conn.close()
    return {
        "domain": domain_upper,
        "functions": [dict(r) for r in functions],
        "tables": [dict(r) for r in tables],
        "structs": [dict(r) for r in structs],
    }


# ── List Services ──

def list_all_services() -> list[dict]:
    """전체 서비스 함수 목록."""
    conn = get_connection(DB_PATH)
    rows = conn.execute(
        "SELECT name, file_path, description FROM functions ORDER BY name"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]
