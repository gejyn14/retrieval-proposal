"""SQLite 구조 DB — 스키마 정의 및 연결 관리."""

from __future__ import annotations

import sqlite3
from pathlib import Path

DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "structural.db"

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS functions (
    name        TEXT PRIMARY KEY,
    file_path   TEXT NOT NULL,
    description TEXT,
    body        TEXT,
    params      TEXT,       -- JSON array
    tables_used TEXT,       -- JSON array
    includes    TEXT        -- JSON array
);

CREATE TABLE IF NOT EXISTS function_calls (
    caller TEXT NOT NULL,
    callee TEXT NOT NULL,
    PRIMARY KEY (caller, callee)
);

CREATE TABLE IF NOT EXISTS sql_usage (
    function_name TEXT NOT NULL,
    table_name    TEXT NOT NULL,
    operation     TEXT NOT NULL,
    raw_sql       TEXT
);

CREATE TABLE IF NOT EXISTS structs (
    name        TEXT PRIMARY KEY,
    file_path   TEXT NOT NULL,
    description TEXT,
    fields      TEXT        -- JSON array
);

CREATE TABLE IF NOT EXISTS tables_ddl (
    name        TEXT PRIMARY KEY,
    file_path   TEXT NOT NULL,
    ddl         TEXT,
    comment     TEXT,
    columns     TEXT,       -- JSON array
    primary_key TEXT        -- JSON array
);

-- FTS5 full-text index for keyword search
CREATE VIRTUAL TABLE IF NOT EXISTS functions_fts USING fts5(
    name, description, body,
    content='functions',
    content_rowid='rowid'
);

-- Trigger to keep FTS in sync
CREATE TRIGGER IF NOT EXISTS functions_ai AFTER INSERT ON functions BEGIN
    INSERT INTO functions_fts(rowid, name, description, body)
    VALUES (new.rowid, new.name, new.description, new.body);
END;
"""


def get_connection(db_path: Path | str | None = None) -> sqlite3.Connection:
    """SQLite 연결 반환. WAL 모드 활성화."""
    db_path = Path(db_path) if db_path else DEFAULT_DB_PATH
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db(db_path: Path | str | None = None) -> sqlite3.Connection:
    """DB 초기화 — 테이블 생성."""
    conn = get_connection(db_path)
    conn.executescript(SCHEMA_SQL)
    conn.commit()
    return conn


def reset_db(db_path: Path | str | None = None) -> sqlite3.Connection:
    """DB 초기화 — 기존 데이터 삭제 후 재생성."""
    db_path = Path(db_path) if db_path else DEFAULT_DB_PATH
    if db_path.exists():
        db_path.unlink()
    return init_db(db_path)
