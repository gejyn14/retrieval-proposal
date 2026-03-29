"""파싱 결과 데이터 모델."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class SQLStatement:
    operation: str  # SELECT, INSERT, UPDATE, DELETE, DECLARE
    tables: list[str] = field(default_factory=list)
    columns: list[str] = field(default_factory=list)
    raw_sql: str = ""


@dataclass
class StructField:
    name: str
    c_type: str
    size: str | None = None  # e.g. "12" from char[12]
    comment: str | None = None


@dataclass
class ParsedFunction:
    name: str
    file_path: str
    description: str  # 주석에서 추출
    body: str
    params: list[str] = field(default_factory=list)
    sql_statements: list[SQLStatement] = field(default_factory=list)
    called_functions: list[str] = field(default_factory=list)
    tables_used: list[str] = field(default_factory=list)
    includes: list[str] = field(default_factory=list)


@dataclass
class ParsedStruct:
    name: str
    file_path: str
    description: str
    fields: list[StructField] = field(default_factory=list)


@dataclass
class TableColumn:
    name: str
    data_type: str
    nullable: bool = True
    default: str | None = None


@dataclass
class ParsedTable:
    name: str
    file_path: str
    columns: list[TableColumn] = field(default_factory=list)
    comment: str | None = None
    primary_key: list[str] = field(default_factory=list)


@dataclass
class ParsedCodebase:
    """전체 코드베이스 파싱 결과."""
    functions: list[ParsedFunction] = field(default_factory=list)
    structs: list[ParsedStruct] = field(default_factory=list)
    tables: list[ParsedTable] = field(default_factory=list)
