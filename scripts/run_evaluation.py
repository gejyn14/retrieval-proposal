#!/usr/bin/env python3
"""전략 비교 평가 실행.

6개 쿼리 × 3개 전략(chunk/structural/hybrid) 비교.
"""

import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.retrieval import chunk_retrieval, structural_retrieval, hybrid_retrieval
from src.evaluation.ground_truth import GROUND_TRUTH
from src.evaluation.evaluator import evaluate, format_comparison_table, EvalMetrics

import os
_USE_LARGE = os.environ.get("USE_LARGE_CODEBASE", "1") == "1"

if _USE_LARGE and (ROOT / "data" / "structural_large.db").exists():
    DB_PATH = ROOT / "data" / "structural_large.db"
    CHROMA_DIR = ROOT / "data" / "chroma_db_large"
else:
    DB_PATH = ROOT / "data" / "structural.db"
    CHROMA_DIR = ROOT / "data" / "chroma_db"


def run_chunk_search(query: str) -> list[str]:
    """Chunk vector 검색 후 파일 목록 반환."""
    result = chunk_retrieval.search(query, top_k=5, chroma_dir=CHROMA_DIR)
    return result.files_returned


def run_structural_search(query: str) -> list[str]:
    """Structural 검색 후 파일 목록 반환."""
    result = structural_retrieval.search(query, db_path=DB_PATH)
    return result.files_returned


def run_hybrid_search(query: str) -> list[str]:
    """Hybrid 검색 후 파일 목록 반환."""
    result = hybrid_retrieval.search(query, top_k=5, chroma_dir=CHROMA_DIR, db_path=DB_PATH)
    return result.files_returned


def main():
    queries = list(GROUND_TRUTH.keys())
    all_metrics: list[EvalMetrics] = []

    print("=" * 60)
    print("  Pro*C Code Retrieval — Strategy Evaluation")
    print("=" * 60)

    for query in queries:
        gt = GROUND_TRUTH[query]
        print(f"\n{'─' * 60}")
        print(f"Query: \"{query}\"")
        print(f"Target: {gt['target_function']}  Required: {gt['required_files']}")
        print(f"{'─' * 60}")

        # ── Chunk Vector ──
        print("\n  [Chunk Vector]")
        t0 = time.time()
        chunk_files = run_chunk_search(query)
        t = time.time() - t0
        m = evaluate(query, "chunk", chunk_files)
        all_metrics.append(m)
        print(f"    Returned: {chunk_files}")
        print(f"    Relevant: {m.relevant_returned}  Missing: {m.missing_files}  Noise: {m.noise_files}")
        print(f"    Precision={m.precision:.1%}  Recall={m.recall:.1%}  Noise={m.noise_ratio:.1%}  Completeness={m.context_completeness:.1%}")
        print(f"    Time: {t:.3f}s")

        # ── Structural ──
        print("\n  [Structural Graph]")
        t0 = time.time()
        struct_files = run_structural_search(query)
        t = time.time() - t0
        m = evaluate(query, "structural", struct_files)
        all_metrics.append(m)
        print(f"    Returned: {struct_files}")
        print(f"    Relevant: {m.relevant_returned}  Missing: {m.missing_files}  Noise: {m.noise_files}")
        print(f"    Precision={m.precision:.1%}  Recall={m.recall:.1%}  Noise={m.noise_ratio:.1%}  Completeness={m.context_completeness:.1%}")
        print(f"    Time: {t:.3f}s")

        # ── Hybrid ──
        print("\n  [Hybrid (Vector → Structural)]")
        t0 = time.time()
        hybrid_files = run_hybrid_search(query)
        t = time.time() - t0
        m = evaluate(query, "hybrid", hybrid_files)
        all_metrics.append(m)
        print(f"    Returned: {hybrid_files}")
        print(f"    Relevant: {m.relevant_returned}  Missing: {m.missing_files}  Noise: {m.noise_files}")
        print(f"    Precision={m.precision:.1%}  Recall={m.recall:.1%}  Noise={m.noise_ratio:.1%}  Completeness={m.context_completeness:.1%}")
        print(f"    Time: {t:.3f}s")

    # ── 비교 테이블 ──
    print(format_comparison_table(all_metrics))


if __name__ == "__main__":
    main()
