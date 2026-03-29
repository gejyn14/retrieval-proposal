"""평가 엔진 — Precision, Recall, Context Completeness, Noise Ratio 측정."""

from __future__ import annotations

from dataclasses import dataclass, field

from .ground_truth import GROUND_TRUTH


@dataclass
class EvalMetrics:
    query: str
    strategy: str
    # 핵심 지표
    precision: float = 0.0      # 반환 파일 중 정답 비율
    recall: float = 0.0         # 정답 파일 중 반환 비율
    noise_ratio: float = 0.0    # 반환 파일 중 노이즈 비율
    # 컨텍스트 완결성 (4가지 카테고리)
    has_function_body: bool = False
    has_structs: bool = False
    has_called_functions: bool = False
    has_table_ddl: bool = False
    context_completeness: float = 0.0  # 4가지 중 확보 비율
    # 상세
    returned_files: list[str] = field(default_factory=list)
    relevant_returned: list[str] = field(default_factory=list)
    missing_files: list[str] = field(default_factory=list)
    noise_files: list[str] = field(default_factory=list)


def evaluate(
    query: str,
    strategy: str,
    returned_files: list[str],
) -> EvalMetrics:
    """단일 쿼리에 대한 검색 결과 평가."""
    gt = GROUND_TRUTH.get(query)
    if not gt:
        return EvalMetrics(query=query, strategy=strategy, returned_files=returned_files)

    required = set(gt["required_files"])
    noise_set = set(gt.get("noise_files", []))
    returned_set = set(returned_files)

    relevant_returned = returned_set & required
    noise_returned = returned_set & noise_set
    missing = required - returned_set

    precision = len(relevant_returned) / len(returned_set) if returned_set else 0.0
    recall = len(relevant_returned) / len(required) if required else 0.0
    noise_ratio = len(noise_returned) / len(returned_set) if returned_set else 0.0

    # 컨텍스트 완결성
    categories = gt.get("context_categories", {})
    checks = {
        "has_function_body": any(f in returned_set for f in categories.get("function_body", [])),
        "has_structs": (
            not categories.get("structs")  # 필요 없으면 True
            or any(f in returned_set for f in categories.get("structs", []))
        ),
        "has_called_functions": (
            not categories.get("called_functions")
            or any(f in returned_set for f in categories.get("called_functions", []))
        ),
        "has_table_ddl": (
            not categories.get("table_ddl")
            or any(f in returned_set for f in categories.get("table_ddl", []))
        ),
    }
    completeness_count = sum(checks.values())
    context_completeness = completeness_count / 4.0

    return EvalMetrics(
        query=query,
        strategy=strategy,
        precision=round(precision, 3),
        recall=round(recall, 3),
        noise_ratio=round(noise_ratio, 3),
        has_function_body=checks["has_function_body"],
        has_structs=checks["has_structs"],
        has_called_functions=checks["has_called_functions"],
        has_table_ddl=checks["has_table_ddl"],
        context_completeness=round(context_completeness, 3),
        returned_files=returned_files,
        relevant_returned=sorted(relevant_returned),
        missing_files=sorted(missing),
        noise_files=sorted(noise_returned),
    )


def format_comparison_table(all_metrics: list[EvalMetrics]) -> str:
    """모든 전략의 평가 결과를 비교 테이블로 포맷."""
    # 쿼리별, 전략별 그룹화
    queries = list(dict.fromkeys(m.query for m in all_metrics))
    strategies = list(dict.fromkeys(m.strategy for m in all_metrics))

    lines = []
    sep = "─" * 100

    # 헤더
    lines.append(f"\n{'RETRIEVAL STRATEGY COMPARISON':^100}")
    lines.append(sep)
    lines.append(
        f"{'Query':<24} {'Strategy':<12} {'Prec':>6} {'Recall':>7} {'Noise':>7} "
        f"{'Body':>5} {'Struct':>7} {'Calls':>6} {'DDL':>5} {'Compl':>7}"
    )
    lines.append(sep)

    for query in queries:
        for strategy in strategies:
            m = next((x for x in all_metrics if x.query == query and x.strategy == strategy), None)
            if not m:
                continue
            body = "Y" if m.has_function_body else "-"
            structs = "Y" if m.has_structs else "-"
            calls = "Y" if m.has_called_functions else "-"
            ddl = "Y" if m.has_table_ddl else "-"
            lines.append(
                f"{query:<24} {strategy:<12} {m.precision:>6.1%} {m.recall:>7.1%} {m.noise_ratio:>7.1%} "
                f"{body:>5} {structs:>7} {calls:>6} {ddl:>5} {m.context_completeness:>7.1%}"
            )
        lines.append("─" * 100)

    # 전략별 평균
    lines.append(f"\n{'STRATEGY AVERAGES':^100}")
    lines.append(sep)
    for strategy in strategies:
        metrics = [m for m in all_metrics if m.strategy == strategy]
        if not metrics:
            continue
        avg_prec = sum(m.precision for m in metrics) / len(metrics)
        avg_recall = sum(m.recall for m in metrics) / len(metrics)
        avg_noise = sum(m.noise_ratio for m in metrics) / len(metrics)
        avg_compl = sum(m.context_completeness for m in metrics) / len(metrics)
        lines.append(
            f"  {strategy:<14} Precision={avg_prec:.1%}  Recall={avg_recall:.1%}  "
            f"Noise={avg_noise:.1%}  Completeness={avg_compl:.1%}"
        )

    lines.append(sep)
    return "\n".join(lines)
