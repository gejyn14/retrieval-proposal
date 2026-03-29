#!/usr/bin/env python3
"""Pro*C Code Retrieval MCP Server.

Claude Code에서 사용할 수 있는 MCP 서버.
모든 검색은 src.retrieval.service 를 통해 수행.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from mcp.server.fastmcp import FastMCP

from src.retrieval.service import (
    search_structural,
    get_function_detail,
    get_call_graph_data,
    find_functions_by_table,
    get_impact_data,
    find_by_error_code_data,
    get_business_flow_data,
    search_by_domain_data,
    list_all_services,
)

mcp = FastMCP("proc-retrieval", instructions=(
    "증권사 Pro*C 코드베이스 검색 서버.\n"
    "자연어로 코드를 검색하면 관련 함수, 구조체, DDL, 호출 그래프를 반환합니다.\n"
    "'환매 수수료 계산', '매수 주문 처리' 등 한국어 업무 설명으로 검색하세요."
))


@mcp.tool()
def search_code(query: str) -> str:
    """코드 검색 — 자연어 쿼리로 관련 함수를 찾고 구조 정보를 반환합니다. 코드 자체는 반환하지 않으며, 파일 경로를 제공합니다.

    Args:
        query: 검색 쿼리 (예: "환매 수수료 계산", "매수 주문 처리")
    """
    result = search_structural(query)
    output = f"## Search: \"{query}\"\n\n"
    if result["matched_function"]:
        output += f"**Matched Function:** {result['matched_function']}\n"
        output += f"**Description:** {result['description']}\n"
        if result["call_graph"]:
            cg = result["call_graph"]
            parts = []
            if cg["called_by"]:
                parts.append(f"← {', '.join(cg['called_by'])}")
            parts.append(f"**{cg['entry']}**")
            if cg["calls"]:
                parts.append(f"→ {', '.join(cg['calls'])}")
            output += f"**Call Graph:** {' '.join(parts)}\n"
        if result["tables_used"]:
            output += f"**Tables:** {', '.join(result['tables_used'])}\n"
        output += "\n"
        # 후보 목록 (top-3)
        if result.get("candidates") and len(result["candidates"]) > 1:
            output += "**Other Candidates:**\n"
            for c in result["candidates"][1:]:
                output += f"- {c['name']} (score={c['score']}) — {c['description'][:50]}\n"
            output += "\n"
        if result["related_files"]:
            output += "**Related Files:**\n"
            for f in result["related_files"]:
                output += f"- `{f['filename']}` — {f['role']}\n"
    else:
        output += "매칭되는 함수를 찾을 수 없습니다.\n"
    return output


@mcp.tool()
def get_function(name: str) -> str:
    """함수 상세 조회 — 구조 정보 + 의존 파일 경로를 반환합니다. 실제 코드는 파일 경로로 직접 Read하세요.

    Args:
        name: 함수명 (예: "RD_FEE_03", "ST_BUY_01")
    """
    detail = get_function_detail(name)
    if not detail:
        return f"함수 '{name}'을 찾을 수 없습니다."

    output = f"## {name}\n"
    output += f"**Description:** {detail['description']}\n"
    output += f"**File:** `{detail['file_path']}`\n"

    if detail["call_graph"]:
        cg = detail["call_graph"]
        parts = []
        if cg["called_by"]:
            parts.append(f"← {', '.join(cg['called_by'])}")
        parts.append(f"**{name}**")
        if cg["calls"]:
            parts.append(f"→ {', '.join(cg['calls'])}")
        output += f"**Call Graph:** {' '.join(parts)}\n"

    if detail["tables"]:
        output += f"**Tables:** {', '.join(detail['tables'])}\n"

    output += "\n**Files to Read:**\n"
    output += f"- `{detail['file_path']}` — 메인 함수\n"
    for f in detail.get("struct_files", []):
        output += f"- `{f}` — 입출력 구조체\n"
    for f in detail.get("dependency_files", []):
        output += f"- `{f}` — 호출 함수\n"
    for f in detail.get("ddl_files", []):
        output += f"- `{f}` — 테이블 DDL\n"

    return output


@mcp.tool()
def get_call_graph(name: str, depth: int = 2) -> str:
    """호출 그래프 탐색 — 함수의 호출/피호출 관계를 트리로 보여줍니다.

    Args:
        name: 함수명
        depth: 탐색 깊이 (기본 2)
    """
    data = get_call_graph_data(name, depth)

    output = f"## Call Graph: {data['name']}\n\n"
    if data["called_by"]:
        output += "**Called By:**\n"
        for caller in data["called_by"]:
            output += f"  ← {caller}\n"

    output += f"\n**{data['name']}**\n"
    if data["calls"]:
        for r in data["calls"]:
            indent = "  " * r["depth"]
            output += f"{indent}→ {r['callee']}\n"
    else:
        output += "  (leaf function — no outgoing calls)\n"

    return output


@mcp.tool()
def find_by_table(table_name: str) -> str:
    """테이블 사용 함수 조회 — 특정 테이블을 참조하는 모든 함수를 찾습니다.

    Args:
        table_name: 테이블명 (예: "TB_ACCT_MST", "TB_ORD_MST")
    """
    data = find_functions_by_table(table_name)

    output = f"## Table: {data['table_name']}\n\n"

    if data["ddl"]:
        output += f"**Comment:** {data['ddl']['comment'] or 'N/A'}\n"
        if data["ddl"]["columns"]:
            output += "**Columns:**\n"
            for c in data["ddl"]["columns"]:
                output += f"  - {c['name']} {c['data_type']}"
                if not c.get("nullable", True):
                    output += " NOT NULL"
                output += "\n"

    if data["usages"]:
        output += "\n**Used By:**\n"
        for r in data["usages"]:
            output += f"  - {r['function_name']} ({r['operation']})\n"
    else:
        output += "\n(No functions reference this table)\n"

    return output


@mcp.tool()
def get_impact(name: str, depth: int = 5) -> str:
    """영향도 분석 — 함수 또는 테이블을 수정했을 때 영향 받는 서비스를 역추적합니다.

    Args:
        name: 함수명 또는 테이블명 (예: "CM_TAX_01", "TB_FEE_RATE")
        depth: 역추적 깊이 (기본 5)
    """
    data = get_impact_data(name, depth)

    if data["type"] == "unknown":
        return f"'{name}'에 해당하는 함수 또는 테이블을 찾을 수 없습니다."

    output = f"## Impact Analysis: {data['name']}\n\n"

    if data["type"] == "function":
        output += f"**Type:** 함수\n"
        output += f"**Description:** {data['description']}\n"
        if data["tables_used"]:
            output += f"**Tables Used:** {', '.join(t['table'] + '(' + t['operation'] + ')' for t in data['tables_used'])}\n"
        output += f"**Affected Services:** {data['affected_count']}개\n\n"

        if data["affected_services"]:
            by_depth: dict[int, list] = {}
            for svc in data["affected_services"]:
                by_depth.setdefault(svc["depth"], []).append(svc)

            for d in sorted(by_depth):
                label = "직접 호출자" if d == 1 else f"{d}단계 상위"
                output += f"### {label}\n"
                for svc in by_depth[d]:
                    output += f"- **{svc['name']}** — {svc['description']}\n"
                output += "\n"
        else:
            output += "이 함수를 호출하는 서비스가 없습니다. (최상위 진입점)\n"

    elif data["type"] == "table":
        output += f"**Type:** 테이블\n"
        output += f"**Comment:** {data['comment']}\n"
        output += f"**Affected Services:** {data['affected_count']}개\n\n"

        if data["affected_services"]:
            direct = [s for s in data["affected_services"] if s["depth"] == 0]
            indirect = [s for s in data["affected_services"] if s["depth"] > 0]

            if direct:
                output += "### 직접 사용 함수\n"
                for svc in direct:
                    output += f"- **{svc['name']}** ({svc['operation']}) — {svc['description']}\n"
                output += "\n"

            if indirect:
                output += "### 간접 영향 (상위 호출자)\n"
                for svc in indirect:
                    output += f"- **{svc['name']}** — {svc['description']}\n"
                output += "\n"

    return output


@mcp.tool()
def find_by_error_code(error_code: str) -> str:
    """에러 코드 추적 — 에러 코드가 설정되는 함수와 에러 메시지를 찾습니다.

    Args:
        error_code: 에러 코드 (예: "E101", "E201")
    """
    data = find_by_error_code_data(error_code)

    if not data["occurrences"]:
        return f"에러 코드 '{error_code}'를 찾을 수 없습니다."

    output = f"## Error Code: {error_code}\n\n"
    output += f"**발견:** {len(data['occurrences'])}건\n\n"

    for occ in data["occurrences"]:
        output += f"### {occ['function_name']} ({occ['file_path']})\n"
        if occ["error_message"]:
            output += f"**Message:** {occ['error_message']}\n"
        if occ["context"]:
            output += f"```c\n{occ['context']}\n```\n\n"

    return output


@mcp.tool()
def get_business_flow(entry_function: str, depth: int = 5) -> str:
    """업무 흐름 조회 — 함수를 진입점으로 SQL 연산을 포함한 전체 처리 흐름을 보여줍니다.

    Args:
        entry_function: 진입점 함수명 (예: "FD_PAY_01", "ST_BUY_01")
        depth: 탐색 깊이 (기본 5)
    """
    data = get_business_flow_data(entry_function, depth)

    if not data["steps"]:
        return f"함수 '{entry_function}'을 찾을 수 없습니다."

    output = f"## Business Flow: {data['entry']} — {data['description']}\n\n"

    for step in data["steps"]:
        indent = "  " * step["depth"]
        output += f"{indent}**{step['name']}** — {step['description']}\n"
        for sql in step.get("sql_operations", []):
            output += f"{indent}  `{sql['operation']} {sql['table']}`\n"

    if data["tables_touched"]:
        output += f"\n**Tables touched:** {', '.join(data['tables_touched'])}\n"

    return output


@mcp.tool()
def search_by_domain(domain: str) -> str:
    """도메인별 조회 — 프리픽스(ST, FD, AC 등)로 해당 도메인의 함수/테이블/구조체를 조회합니다.

    Args:
        domain: 도메인 프리픽스 (예: "ST" 주식, "FD" 펀드, "AC" 계좌, "BN" 채권)
    """
    data = search_by_domain_data(domain)

    output = f"## Domain: {domain}\n\n"

    if data["functions"]:
        output += f"### Functions ({len(data['functions'])})\n"
        for f in data["functions"]:
            output += f"- **{f['name']}** — {f['description']}\n"
        output += "\n"

    if data["tables"]:
        output += f"### Tables ({len(data['tables'])})\n"
        for t in data["tables"]:
            output += f"- **{t['name']}** — {t['comment']}\n"
        output += "\n"

    if data["structs"]:
        output += f"### Structs ({len(data['structs'])})\n"
        for s in data["structs"]:
            output += f"- **{s['name']}** ({s['file_path']})\n"
        output += "\n"

    if not data["functions"] and not data["tables"] and not data["structs"]:
        output += f"도메인 '{domain}'에 해당하는 항목이 없습니다.\n"

    return output


@mcp.tool()
def list_services() -> str:
    """전체 서비스 목록 — 등록된 모든 Pro*C 서비스 함수를 보여줍니다."""
    rows = list_all_services()

    output = "## Registered Services\n\n"
    output += f"| {'Function':<16} | {'File':<20} | Description |\n"
    output += f"|{'-'*18}|{'-'*22}|{'-'*40}|\n"
    for r in rows:
        output += f"| {r['name']:<16} | {r['file_path']:<20} | {r['description'][:38]} |\n"

    return output


if __name__ == "__main__":
    mcp.run()
