#!/usr/bin/env python3
"""Pro*C Retrieval — API Server.

MCP와 동일한 서비스 레이어를 사용하는 웹 UI용 API.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from fastapi import FastAPI
from fastapi.responses import FileResponse, PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from src.retrieval.service import (
    search_structural,
    get_function_detail,
    get_call_graph_data,
    find_functions_by_table,
    get_impact_data,
    get_business_flow_data,
    find_by_error_code_data,
    search_by_domain_data,
    list_all_services,
)

import os
_USE_LARGE = os.environ.get("USE_LARGE_CODEBASE", "1") == "1"
CODEBASE_DIR = ROOT / "data" / ("large_codebase" if _USE_LARGE else "sample_codebase")

app = FastAPI(title="Pro*C Retrieval")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


@app.get("/")
async def index():
    return FileResponse(ROOT / "web" / "index.html")


@app.get("/api/services")
async def services():
    return list_all_services()


class SearchReq(BaseModel):
    query: str

@app.post("/api/search")
async def search(req: SearchReq):
    return search_structural(req.query)


@app.get("/api/function/{name}")
async def function_detail(name: str):
    detail = get_function_detail(name)
    if not detail:
        return {"error": f"함수 '{name}' 없음"}
    return detail


@app.get("/api/call-graph/{name}")
async def call_graph(name: str, depth: int = 2):
    return get_call_graph_data(name, depth)


@app.get("/api/impact/{name}")
async def impact(name: str, depth: int = 5):
    return get_impact_data(name, depth)


@app.get("/api/table/{name}")
async def table_usage(name: str):
    return find_functions_by_table(name)


@app.get("/api/flow/{name}")
async def business_flow(name: str, depth: int = 5):
    return get_business_flow_data(name, depth)


@app.get("/api/error/{code}")
async def error_code(code: str):
    return find_by_error_code_data(code)


@app.get("/api/domain/{domain}")
async def domain_search(domain: str):
    return search_by_domain_data(domain)


# ── Repo 파일 읽기 (Claude Code의 Read tool 시뮬레이션) ──

@app.get("/api/file/{filename:path}")
async def read_file(filename: str):
    """repo에서 실제 파일 내용 읽기."""
    file_path = CODEBASE_DIR / filename
    if not file_path.exists():
        return {"error": f"파일 '{filename}' 없음", "path": str(file_path)}
    content = file_path.read_text(encoding="utf-8", errors="replace")
    return {"filename": filename, "path": str(file_path), "content": content}


if __name__ == "__main__":
    import uvicorn
    print(f"\n  Pro*C Code Retrieval")
    print(f"  http://localhost:8000\n")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="warning")
