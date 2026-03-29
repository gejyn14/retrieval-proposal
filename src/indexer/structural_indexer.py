"""구조 기반 인덱서 — 파싱 결과를 SQLite 그래프로 저장."""

from __future__ import annotations

import json
import sqlite3
from dataclasses import asdict
from pathlib import Path

from ..parser.schema import ParsedCodebase
from .db import init_db, reset_db


def index_codebase(codebase: ParsedCodebase, db_path: Path | str | None = None, *, reset: bool = True) -> sqlite3.Connection:
    """ParsedCodebase를 SQLite에 인덱싱."""
    conn = reset_db(db_path) if reset else init_db(db_path)

    # 함수
    for fn in codebase.functions:
        conn.execute(
            "INSERT OR REPLACE INTO functions (name, file_path, description, body, params, tables_used, includes) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                fn.name,
                fn.file_path,
                fn.description,
                fn.body,
                json.dumps(fn.params),
                json.dumps(fn.tables_used),
                json.dumps(fn.includes),
            ),
        )

        # 호출관계
        for callee in fn.called_functions:
            conn.execute(
                "INSERT OR IGNORE INTO function_calls (caller, callee) VALUES (?, ?)",
                (fn.name, callee),
            )

        # SQL 사용
        for sql in fn.sql_statements:
            for table in sql.tables:
                conn.execute(
                    "INSERT INTO sql_usage (function_name, table_name, operation, raw_sql) VALUES (?, ?, ?, ?)",
                    (fn.name, table, sql.operation, sql.raw_sql),
                )

    # 구조체
    for st in codebase.structs:
        fields_json = json.dumps([asdict(f) for f in st.fields], ensure_ascii=False)
        conn.execute(
            "INSERT OR REPLACE INTO structs (name, file_path, description, fields) VALUES (?, ?, ?, ?)",
            (st.name, st.file_path, st.description, fields_json),
        )

    # DDL 테이블
    for tb in codebase.tables:
        cols_json = json.dumps([asdict(c) for c in tb.columns], ensure_ascii=False)
        conn.execute(
            "INSERT OR REPLACE INTO tables_ddl (name, file_path, ddl, comment, columns, primary_key) VALUES (?, ?, ?, ?, ?, ?)",
            (tb.name, tb.file_path, "", tb.comment, cols_json, json.dumps(tb.primary_key)),
        )

    conn.commit()
    return conn
