#!/usr/bin/env python3
"""파싱 → 인덱싱 파이프라인.

Usage:
    python scripts/index_all.py              # sample_codebase (기본)
    python scripts/index_all.py large        # large_codebase
    python scripts/index_all.py large fixed  # large + fixed chunk 전략
"""

import sys
import time
from pathlib import Path

# 프로젝트 루트를 path에 추가
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.parser.proc_parser import parse_codebase
from src.indexer.structural_indexer import index_codebase
from src.indexer.chunk_indexer import index_directory

# CLI 인자 파싱
_args = sys.argv[1:]
USE_LARGE = "large" in _args
CHUNK_STRATEGY = "fixed" if "fixed" in _args else "semantic"

if USE_LARGE:
    CODEBASE_DIR = ROOT / "data" / "large_codebase"
    DB_PATH = ROOT / "data" / "structural_large.db"
    CHROMA_DIR = ROOT / "data" / "chroma_db_large"
else:
    CODEBASE_DIR = ROOT / "data" / "sample_codebase"
    DB_PATH = ROOT / "data" / "structural.db"
    CHROMA_DIR = ROOT / "data" / "chroma_db"


def main():
    print("=" * 60)
    print(f"  Pro*C Code Retrieval — Indexing Pipeline")
    print(f"  Codebase: {CODEBASE_DIR.name}  |  Chunk: {CHUNK_STRATEGY}")
    print("=" * 60)

    # Step 1: Parse
    print("\n[1/3] Parsing codebase...")
    t0 = time.time()
    codebase = parse_codebase(CODEBASE_DIR)
    t_parse = time.time() - t0

    print(f"  Functions: {len(codebase.functions)}")
    for fn in codebase.functions:
        calls = ", ".join(fn.called_functions) if fn.called_functions else "(none)"
        tables = ", ".join(fn.tables_used) if fn.tables_used else "(none)"
        print(f"    {fn.name:<16} calls=[{calls}]  tables=[{tables}]")

    print(f"  Structs:   {len(codebase.structs)}")
    for st in codebase.structs:
        print(f"    {st.name:<20} fields={len(st.fields)}")

    print(f"  Tables:    {len(codebase.tables)}")
    for tb in codebase.tables:
        print(f"    {tb.name:<20} cols={len(tb.columns)}  comment={tb.comment}")

    print(f"  Parse time: {t_parse:.3f}s")

    # Step 2: Structural index
    print("\n[2/3] Building structural index (SQLite)...")
    t0 = time.time()
    conn = index_codebase(codebase, DB_PATH, reset=True)
    t_struct = time.time() - t0

    # 검증
    fn_count = conn.execute("SELECT COUNT(*) FROM functions").fetchone()[0]
    call_count = conn.execute("SELECT COUNT(*) FROM function_calls").fetchone()[0]
    sql_count = conn.execute("SELECT COUNT(*) FROM sql_usage").fetchone()[0]
    struct_count = conn.execute("SELECT COUNT(*) FROM structs").fetchone()[0]
    table_count = conn.execute("SELECT COUNT(*) FROM tables_ddl").fetchone()[0]
    conn.close()

    print(f"  functions: {fn_count}, calls: {call_count}, sql_usage: {sql_count}")
    print(f"  structs: {struct_count}, tables_ddl: {table_count}")
    print(f"  DB path: {DB_PATH}")
    print(f"  Index time: {t_struct:.3f}s")

    # Step 3: Chunk vector index
    print("\n[3/3] Building chunk vector index (ChromaDB)...")
    t0 = time.time()
    collection = index_directory(CODEBASE_DIR, CHROMA_DIR, reset=True,
                                 strategy=CHUNK_STRATEGY)
    t_chunk = time.time() - t0

    print(f"  Chunks indexed: {collection.count()}")
    print(f"  ChromaDB path: {CHROMA_DIR}")
    print(f"  Index time: {t_chunk:.3f}s")

    print(f"\n{'=' * 60}")
    print(f"  Total time: {t_parse + t_struct + t_chunk:.3f}s")
    print(f"  Ready for evaluation!")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
