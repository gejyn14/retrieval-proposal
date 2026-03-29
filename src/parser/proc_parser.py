"""Pro*C / header / DDL 파서 — 정규식 기반."""

from __future__ import annotations

import os
import re
from pathlib import Path

from .schema import (
    ParsedCodebase,
    ParsedFunction,
    ParsedStruct,
    ParsedTable,
    SQLStatement,
    StructField,
    TableColumn,
)

# ── 정규식 패턴 ──────────────────────────────────────

# 함수 정의: int FUNC_NAME(...) {
RE_FUNC = re.compile(
    r"^int\s+([A-Z][A-Z0-9_]+)\s*\(([^)]*)\)\s*\{",
    re.MULTILINE,
)

# EXEC SQL 블록 (세미콜론까지)
RE_EXEC_SQL = re.compile(
    r"EXEC\s+SQL\s+(.*?);",
    re.DOTALL | re.IGNORECASE,
)

# SQL DML 연산 + 테이블명
RE_SQL_SELECT = re.compile(r"\bSELECT\b.*?\bFROM\s+(\w+)", re.DOTALL | re.IGNORECASE)
RE_SQL_INSERT = re.compile(r"\bINSERT\s+INTO\s+(\w+)", re.IGNORECASE)
RE_SQL_UPDATE = re.compile(r"\bUPDATE\s+(\w+)", re.IGNORECASE)
RE_SQL_DELETE = re.compile(r"\bDELETE\s+FROM\s+(\w+)", re.IGNORECASE)
RE_SQL_JOIN = re.compile(r"\b(?:FROM|JOIN)\s+(\w+)", re.IGNORECASE)

# SELECT ... INTO 컬럼들
RE_SELECT_COLS = re.compile(
    r"\bSELECT\s+(.*?)\s+INTO\b",
    re.DOTALL | re.IGNORECASE,
)

# 함수 호출: FUNC_NAME(
RE_FUNC_CALL = re.compile(r"\b([A-Z][A-Z0-9_]{2,})\s*\(")

# C 표준 라이브러리 / 키워드 (호출 후보에서 제외)
C_BUILTINS = {
    "EXEC", "SQL", "BEGIN", "END", "DECLARE", "SECTION", "SELECT", "INSERT",
    "UPDATE", "DELETE", "FROM", "WHERE", "INTO", "SET", "VALUES", "AND", "OR",
    "NOT", "NULL", "BETWEEN", "ORDER", "BY", "SYSDATE", "DUAL", "NEXTVAL",
    "CURRVAL", "LPAD", "SUM", "COUNT", "CONSTRAINT", "PRIMARY", "KEY",
    "DEFAULT", "CREATE", "TABLE", "COMMENT", "OPEN", "CLOSE", "FETCH",
    "CURSOR", "FOR", "INCLUDE", "SQLCA", "SUCCESS", "FAIL",
    "TO_CHAR", "TO_DATE", "VARCHAR2", "NUMBER", "CHAR",
}

# #include "file.h"
RE_INCLUDE = re.compile(r'#include\s+"([^"]+)"')

# /* 주석 */ (첫 번째 블록 주석을 설명으로 사용)
RE_BLOCK_COMMENT = re.compile(r"/\*(.*?)\*/", re.DOTALL)

# typedef struct { ... } name_t;
RE_STRUCT = re.compile(
    r"typedef\s+struct\s*\{(.*?)\}\s*(\w+)\s*;",
    re.DOTALL,
)

# struct 필드: type name[size];  /* comment */
RE_FIELD = re.compile(
    r"^\s+([\w\s\*]+?)\s+(\w+)\s*(\[\s*\d+\s*\])?\s*;(?:\s*/\*\s*(.*?)\s*\*/)?",
    re.MULTILINE,
)

# CREATE TABLE name (
RE_CREATE_TABLE = re.compile(
    r"CREATE\s+TABLE\s+(\w+)\s*\((.*?)\);",
    re.DOTALL | re.IGNORECASE,
)

# COMMENT ON TABLE
RE_TABLE_COMMENT = re.compile(
    r"COMMENT\s+ON\s+TABLE\s+(\w+)\s+IS\s+'([^']+)'",
    re.IGNORECASE,
)

# DDL 컬럼: NAME TYPE(size) [NOT NULL] [DEFAULT ...]
RE_DDL_COL = re.compile(
    r"^\s+(\w+)\s+(VARCHAR2|NUMBER|CHAR|DATE|TIMESTAMP)\s*(\([^)]+\))?\s*(NOT\s+NULL)?\s*(DEFAULT\s+\S+)?",
    re.MULTILINE | re.IGNORECASE,
)

# CONSTRAINT ... PRIMARY KEY (cols)
RE_PK = re.compile(
    r"PRIMARY\s+KEY\s*\(([^)]+)\)",
    re.IGNORECASE,
)


# ── 파서 함수 ────────────────────────────────────────

def _extract_sql_statements(body: str) -> list[SQLStatement]:
    """EXEC SQL 블록에서 SQL 문 추출."""
    stmts = []
    for m in RE_EXEC_SQL.finditer(body):
        raw = m.group(1).strip()
        # DECLARE SECTION 등 무시
        if re.match(r"(BEGIN|END)\s+DECLARE", raw, re.IGNORECASE):
            continue
        if re.match(r"INCLUDE", raw, re.IGNORECASE):
            continue

        tables = []
        columns = []
        operation = "OTHER"

        if RE_SQL_SELECT.search(raw):
            operation = "SELECT"
            tables = [t for t in re.findall(r"\b(TB_\w+|SQ_\w+)\b", raw, re.IGNORECASE)]
            col_m = RE_SELECT_COLS.search(raw)
            if col_m:
                col_str = col_m.group(1)
                columns = [c.strip().split(".")[-1] for c in col_str.split(",")]
                columns = [re.sub(r"^:", "", c) for c in columns if c and c != "*"]
        elif RE_SQL_INSERT.search(raw):
            operation = "INSERT"
            tables = RE_SQL_INSERT.findall(raw)
        elif RE_SQL_UPDATE.search(raw):
            operation = "UPDATE"
            tables = RE_SQL_UPDATE.findall(raw)
        elif RE_SQL_DELETE.search(raw):
            operation = "DELETE"
            tables = RE_SQL_DELETE.findall(raw)
        elif re.search(r"\bDECLARE\b", raw, re.IGNORECASE):
            operation = "DECLARE"
        elif re.search(r"\bOPEN\b", raw, re.IGNORECASE):
            operation = "CURSOR"
            tables = [t for t in re.findall(r"\b(TB_\w+)\b", raw)]

        # JOIN으로 추가 테이블 수집
        if operation == "SELECT":
            for t in RE_SQL_JOIN.findall(raw):
                if t.startswith("TB_") and t not in tables:
                    tables.append(t)

        stmts.append(SQLStatement(
            operation=operation,
            tables=tables,
            columns=columns,
            raw_sql=f"EXEC SQL {raw};",
        ))
    return stmts


def _extract_function_calls(body: str, own_name: str) -> list[str]:
    """함수 본문에서 호출하는 다른 Pro*C 함수명 추출."""
    # EXEC SQL 블록 내부 제거 (테이블명 오탐 방지)
    cleaned = RE_EXEC_SQL.sub("", body)
    calls = set()
    for m in RE_FUNC_CALL.finditer(cleaned):
        name = m.group(1)
        if name != own_name and name not in C_BUILTINS and not name.startswith(("TB_", "SQ_")):
            calls.add(name)
    return sorted(calls)


def _find_function_body(text: str, start: int) -> str:
    """함수 시작 `{` 부터 매칭되는 `}` 까지 본문 추출."""
    depth = 0
    i = text.index("{", start)
    for j in range(i, len(text)):
        if text[j] == "{":
            depth += 1
        elif text[j] == "}":
            depth -= 1
            if depth == 0:
                return text[i : j + 1]
    return text[i:]


def parse_pc_file(path: Path) -> list[ParsedFunction]:
    """Pro*C (.pc) 파일에서 함수 목록 추출."""
    text = path.read_text(encoding="utf-8", errors="replace")
    filename = path.name

    # 파일 상단 주석 → 파일 설명
    file_desc = ""
    first_comment = RE_BLOCK_COMMENT.search(text)
    if first_comment:
        file_desc = first_comment.group(1).strip()

    # includes
    includes = RE_INCLUDE.findall(text)

    functions = []
    for m in RE_FUNC.finditer(text):
        func_name = m.group(1)
        params_raw = m.group(2).strip()
        params = [p.strip() for p in params_raw.split(",") if p.strip()]

        body = _find_function_body(text, m.start())
        sql_stmts = _extract_sql_statements(body)
        called = _extract_function_calls(body, func_name)

        # 모든 SQL에서 사용 테이블 수집
        all_tables = []
        for s in sql_stmts:
            for t in s.tables:
                if t not in all_tables:
                    all_tables.append(t)

        # 함수 직전 주석을 설명으로
        desc = file_desc
        preceding = text[max(0, m.start() - 200) : m.start()]
        comment_m = list(RE_BLOCK_COMMENT.finditer(preceding))
        if comment_m:
            desc = comment_m[-1].group(1).strip()

        functions.append(ParsedFunction(
            name=func_name,
            file_path=filename,
            description=desc,
            body=body,
            params=params,
            sql_statements=sql_stmts,
            called_functions=called,
            tables_used=all_tables,
            includes=includes,
        ))

    return functions


def parse_header_file(path: Path) -> list[ParsedStruct]:
    """헤더 (.h) 파일에서 구조체 정의 추출."""
    text = path.read_text(encoding="utf-8", errors="replace")
    filename = path.name

    # 파일 상단 주석
    file_desc = ""
    first_comment = RE_BLOCK_COMMENT.search(text)
    if first_comment:
        file_desc = first_comment.group(1).strip()

    structs = []
    for m in RE_STRUCT.finditer(text):
        body = m.group(1)
        struct_name = m.group(2)

        fields = []
        for fm in RE_FIELD.finditer(body):
            c_type = fm.group(1).strip()
            field_name = fm.group(2)
            size = fm.group(3).strip("[] ") if fm.group(3) else None
            comment = fm.group(4)
            fields.append(StructField(
                name=field_name,
                c_type=c_type,
                size=size,
                comment=comment,
            ))

        structs.append(ParsedStruct(
            name=struct_name,
            file_path=filename,
            description=file_desc,
            fields=fields,
        ))

    return structs


def parse_sql_file(path: Path) -> list[ParsedTable]:
    """DDL (.sql) 파일에서 테이블 정의 추출."""
    text = path.read_text(encoding="utf-8", errors="replace")
    filename = path.name

    tables = []
    for m in RE_CREATE_TABLE.finditer(text):
        table_name = m.group(1)
        body = m.group(2)

        columns = []
        for cm in RE_DDL_COL.finditer(body):
            col_name = cm.group(1)
            data_type = cm.group(2)
            type_size = cm.group(3) or ""
            not_null = bool(cm.group(4))
            default = cm.group(5).replace("DEFAULT ", "").strip() if cm.group(5) else None
            columns.append(TableColumn(
                name=col_name,
                data_type=f"{data_type}{type_size}",
                nullable=not not_null,
                default=default,
            ))

        # Primary key
        pk_m = RE_PK.search(body)
        pk_cols = [c.strip() for c in pk_m.group(1).split(",")] if pk_m else []

        # Table comment
        comment = None
        tc_m = RE_TABLE_COMMENT.search(text)
        if tc_m and tc_m.group(1) == table_name:
            comment = tc_m.group(2)

        tables.append(ParsedTable(
            name=table_name,
            file_path=filename,
            columns=columns,
            comment=comment,
            primary_key=pk_cols,
        ))

    return tables


def parse_codebase(directory: str | Path) -> ParsedCodebase:
    """디렉토리 전체를 파싱하여 ParsedCodebase 반환.

    file_path는 directory 기준 상대경로로 저장 (서브디렉토리 지원).
    """
    directory = Path(directory).resolve()
    result = ParsedCodebase()

    for path in sorted(directory.rglob("*")):
        if not path.is_file():
            continue
        ext = path.suffix.lower()
        rel_path = str(path.relative_to(directory))
        if ext == ".pc":
            funcs = parse_pc_file(path)
            for f in funcs:
                f.file_path = rel_path
            result.functions.extend(funcs)
        elif ext == ".h":
            structs = parse_header_file(path)
            for s in structs:
                s.file_path = rel_path
            result.structs.extend(structs)
        elif ext == ".sql":
            tables = parse_sql_file(path)
            for t in tables:
                t.file_path = rel_path
            result.tables.extend(tables)

    return result
