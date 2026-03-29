"""Pro*C 코드 구조 분석기 — 함수 body에서 핵심 로직을 추출.

EXEC SQL, 함수 호출, 데이터 흐름, 에러 처리를 구조화하여
Claude가 Pro*C 함수를 빠르게 이해할 수 있도록 한다.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass
class SQLStatement:
    """추출된 EXEC SQL 문."""
    operation: str          # SELECT, INSERT, UPDATE, DELETE, DECLARE, OPEN, FETCH, CLOSE
    raw_sql: str            # 원본 SQL
    tables: list[str]       # 참조 테이블
    columns: list[str]      # 참조 컬럼 (INTO 절 등)
    condition: str          # SQL 앞의 if 조건 (있으면)
    comment: str            # SQL 위의 주석 (있으면)
    line_no: int            # 시작 라인


@dataclass
class ServiceCall:
    """추출된 함수 호출."""
    name: str               # 호출 함수명
    args: str               # 인자 (원본 텍스트)
    comment: str            # 호출 위의 주석
    line_no: int


@dataclass
class ErrorHandler:
    """에러 처리 패턴."""
    condition: str           # if (SQLCA.sqlcode != 0) 등
    action: str              # return FAIL, strcpy(err_msg, ...) 등
    line_no: int


@dataclass
class ProCAnalysis:
    """Pro*C 함수 분석 결과."""
    function_name: str
    description: str
    sql_statements: list[SQLStatement] = field(default_factory=list)
    service_calls: list[ServiceCall] = field(default_factory=list)
    error_handlers: list[ErrorHandler] = field(default_factory=list)
    input_fields: list[str] = field(default_factory=list)
    output_fields: list[str] = field(default_factory=list)
    host_variables: list[str] = field(default_factory=list)


# C 표준 함수 — 서비스 호출에서 제외
_C_BUILTINS = {
    "strcpy", "strncpy", "strcmp", "strncmp", "strlen", "sprintf", "printf",
    "memcpy", "memset", "malloc", "free", "sizeof", "pow", "sqrt", "abs",
    "atoi", "atof", "atol", "if", "while", "for", "switch", "return",
}

# EXEC SQL 추출 패턴 (멀티라인)
_EXEC_SQL_RE = re.compile(
    r"EXEC\s+SQL\s+(.*?);",
    re.DOTALL | re.IGNORECASE,
)

# 테이블명 추출 (FROM, INTO, UPDATE, INSERT INTO, DELETE FROM)
_TABLE_RE = re.compile(
    r"\b(?:FROM|INTO|UPDATE|JOIN)\s+(\w+)",
    re.IGNORECASE,
)

# SELECT ... INTO :var 에서 호스트 변수 추출
_INTO_VAR_RE = re.compile(r"INTO\s+:(\w+)", re.IGNORECASE)

# 함수 호출 패턴 (대문자 시작, 서비스 호출)
_CALL_RE = re.compile(r"\b([A-Z][A-Z0-9_]{2,})\s*\(([^)]*)\)")

# in-> 필드 접근
_INPUT_RE = re.compile(r"\bin->(\w+)")

# out-> 필드 접근
_OUTPUT_RE = re.compile(r"\bout->(\w+)")

# SQLCA 에러 체크
_SQLCA_RE = re.compile(r"SQLCA\.sqlcode\s*!=\s*0|SQLCA\.sqlcode\s*<\s*0|SQLCA\.sqlerrd")

# SQL 연산 타입 추출
_SQL_OP_RE = re.compile(
    r"^\s*(SELECT|INSERT|UPDATE|DELETE|DECLARE|OPEN|FETCH|CLOSE|COMMIT|ROLLBACK)",
    re.IGNORECASE,
)


def _extract_comment_above(lines: list[str], target_line: int) -> str:
    """target_line 바로 위의 주석을 추출."""
    idx = target_line - 1
    while idx >= 0:
        stripped = lines[idx].strip()
        if stripped.startswith("/*") and stripped.endswith("*/"):
            return stripped[2:-2].strip()
        elif stripped.startswith("/*") or stripped.startswith("*") or stripped.endswith("*/"):
            # 멀티라인 주석 — 첫 줄만
            return stripped.lstrip("/* ").rstrip(" */").strip()
        elif stripped == "":
            idx -= 1
            continue
        else:
            break
        idx -= 1
    return ""


def _extract_condition_above(lines: list[str], target_line: int) -> str:
    """target_line 위의 if 조건을 추출."""
    idx = target_line - 1
    while idx >= 0:
        stripped = lines[idx].strip()
        if stripped.startswith("if ") or stripped.startswith("if("):
            return stripped
        elif stripped == "" or stripped == "{":
            idx -= 1
            continue
        else:
            break
        idx -= 1
    return ""


def analyze(function_name: str, description: str, body: str) -> ProCAnalysis:
    """Pro*C 함수 body를 분석하여 구조화된 결과 반환."""
    result = ProCAnalysis(
        function_name=function_name,
        description=description,
    )

    lines = body.split("\n")

    # 입출력 필드 추출
    result.input_fields = sorted(set(_INPUT_RE.findall(body)))
    result.output_fields = sorted(set(_OUTPUT_RE.findall(body)))

    # EXEC SQL 추출
    # 라인별로 EXEC SQL 시작 위치를 찾고, ; 까지 수집
    i = 0
    while i < len(lines):
        line = lines[i]
        if "EXEC SQL" in line.upper() and "DECLARE SECTION" not in line.upper() and "INCLUDE" not in line.upper():
            # EXEC SQL 시작 — ; 까지 수집
            sql_lines = [line]
            sql_start = i
            while not line.rstrip().endswith(";") and i + 1 < len(lines):
                i += 1
                line = lines[i]
                sql_lines.append(line)

            raw_sql = " ".join(l.strip() for l in sql_lines)
            raw_sql = re.sub(r"\s+", " ", raw_sql).strip()

            # 연산 타입
            op_match = _SQL_OP_RE.search(raw_sql.replace("EXEC SQL", "").strip())
            operation = op_match.group(1).upper() if op_match else "OTHER"

            # 테이블 추출
            tables = _TABLE_RE.findall(raw_sql)
            # 호스트 변수 제외 (: 접두사)
            tables = [t for t in tables if not t.startswith(":") and t.upper().startswith("TB_")]

            # INTO 변수
            columns = _INTO_VAR_RE.findall(raw_sql)

            # 위의 주석/조건
            comment = _extract_comment_above(lines, sql_start)
            condition = _extract_condition_above(lines, sql_start)

            result.sql_statements.append(SQLStatement(
                operation=operation,
                raw_sql=raw_sql,
                tables=tables,
                columns=columns,
                condition=condition,
                comment=comment,
                line_no=sql_start + 1,
            ))

        i += 1

    # 호스트 변수 추출 (DECLARE SECTION 내부)
    in_declare = False
    for line in lines:
        if "BEGIN DECLARE SECTION" in line:
            in_declare = True
            continue
        if "END DECLARE SECTION" in line:
            in_declare = False
            continue
        if in_declare:
            # char v_acct[11]; / double v_amt; 등
            var_match = re.match(r"\s+\w+\s+(\w+)", line)
            if var_match:
                result.host_variables.append(var_match.group(1))

    # 서비스 호출 추출
    for i, line in enumerate(lines):
        for m in _CALL_RE.finditer(line):
            name = m.group(1)
            if name in _C_BUILTINS:
                continue
            if name.startswith("EXEC") or name.startswith("SQL"):
                continue
            # DECLARE SECTION 내부 무시
            if "DECLARE" in line:
                continue

            comment = _extract_comment_above(lines, i)
            result.service_calls.append(ServiceCall(
                name=name,
                args=m.group(2).strip(),
                comment=comment,
                line_no=i + 1,
            ))

    # 에러 처리 추출
    for i, line in enumerate(lines):
        if _SQLCA_RE.search(line):
            # 다음 라인들에서 return FAIL 또는 err_msg 찾기
            action_lines = []
            for j in range(i + 1, min(i + 5, len(lines))):
                stripped = lines[j].strip()
                if "return" in stripped or "err_cd" in stripped or "err_msg" in stripped:
                    action_lines.append(stripped)
            result.error_handlers.append(ErrorHandler(
                condition=line.strip(),
                action=" | ".join(action_lines) if action_lines else "",
                line_no=i + 1,
            ))

    return result


def format_analysis(analysis: ProCAnalysis, include_raw: bool = False, raw_body: str = "") -> str:
    """분석 결과를 마크다운으로 포맷."""
    out = f"## {analysis.function_name}\n"
    out += f"**설명:** {analysis.description}\n\n"

    # 데이터 흐름
    if analysis.input_fields or analysis.output_fields:
        out += "### Data Flow\n"
        if analysis.input_fields:
            out += f"- **Input:** {', '.join(analysis.input_fields)}\n"
        if analysis.output_fields:
            out += f"- **Output:** {', '.join(analysis.output_fields)}\n"
        out += "\n"

    # SQL 로직 (핵심)
    if analysis.sql_statements:
        out += "### SQL Logic\n"
        for i, sql in enumerate(analysis.sql_statements, 1):
            if sql.comment:
                out += f"**{i}. {sql.comment}**\n"
            else:
                out += f"**{i}. {sql.operation}**\n"
            if sql.condition:
                out += f"  조건: `{sql.condition}`\n"
            out += f"```sql\n{sql.raw_sql}\n```\n"
            if sql.tables:
                out += f"  Tables: {', '.join(sql.tables)}\n"
            out += "\n"

    # 서비스 호출
    if analysis.service_calls:
        out += "### Service Calls\n"
        seen = set()
        for call in analysis.service_calls:
            if call.name in seen:
                continue
            seen.add(call.name)
            desc = f" — {call.comment}" if call.comment else ""
            out += f"- **{call.name}**({call.args}){desc}\n"
        out += "\n"

    # 에러 처리
    if analysis.error_handlers:
        out += "### Error Handling\n"
        for err in analysis.error_handlers:
            out += f"- `{err.condition}`\n"
            if err.action:
                out += f"  → {err.action}\n"
        out += "\n"

    # 원본 코드 (옵션)
    if include_raw and raw_body:
        out += "### Full Code\n"
        out += f"```c\n{raw_body}\n```\n"

    return out
