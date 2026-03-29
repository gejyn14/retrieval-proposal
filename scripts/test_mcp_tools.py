#!/usr/bin/env python3
"""MCP Tool 자동화 테스트.

모든 proc-retrieval tool이 올바르게 작동하는지 검증한다.
실행: python scripts/test_mcp_tools.py
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

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

passed = 0
failed = 0


def test(name, condition, detail=""):
    global passed, failed
    if condition:
        passed += 1
        print(f"  PASS  {name}")
    else:
        failed += 1
        print(f"  FAIL  {name}  — {detail}")


def main():
    print("=" * 60)
    print("  MCP Tool Tests")
    print("=" * 60)

    # ── search_code ──
    print("\n[search_code]")

    r = search_structural("환매 수수료 계산")
    test("환매 수수료 → 매칭됨", r["matched_function"] is not None)
    test("환매 수수료 → RD 도메인", r["matched_function"].startswith("RD"),
         f"got {r['matched_function']}")
    test("환매 수수료 → 후보 있음", len(r.get("candidates", [])) >= 1)
    test("환매 수수료 → related_files 있음", len(r.get("related_files", [])) > 0)

    r = search_structural("반대매매 처리")
    test("반대매매 → LN_FORCED_01", r["matched_function"] == "LN_FORCED_01",
         f"got {r['matched_function']}")

    r = search_structural("VaR 리스크 계산")
    test("VaR → RM_VAR_01", r["matched_function"] == "RM_VAR_01",
         f"got {r['matched_function']}")

    r = search_structural("주식 매수 주문")
    test("매수주문 → ST_BUY_01", r["matched_function"] == "ST_BUY_01",
         f"got {r['matched_function']}")

    r = search_structural("배당금 세금 계산")
    test("배당금세금 → DV 도메인", r["matched_function"].startswith("DV"),
         f"got {r['matched_function']}")

    # ── get_function ──
    print("\n[get_function]")

    d = get_function_detail("RD_FEE_03")
    test("RD_FEE_03 존재", d is not None)
    test("RD_FEE_03 절대경로", d["file_path"].startswith("/"),
         f"got {d['file_path']}")
    test("RD_FEE_03 body 없음", "body" not in d)
    test("RD_FEE_03 call_graph 있음", "calls" in d["call_graph"])
    test("RD_FEE_03 calls CM_DATE_CHK", "CM_DATE_CHK" in d["call_graph"]["calls"])
    test("RD_FEE_03 calls CM_TAX_01", "CM_TAX_01" in d["call_graph"]["calls"])
    test("RD_FEE_03 called_by 있음", len(d["call_graph"]["called_by"]) > 0)
    test("RD_FEE_03 struct_files 있음", len(d["struct_files"]) > 0)
    test("RD_FEE_03 struct 절대경로", d["struct_files"][0].startswith("/"),
         f"got {d['struct_files'][0]}")
    test("RD_FEE_03 dependency_files 있음", len(d["dependency_files"]) > 0)
    test("RD_FEE_03 ddl_files 있음", len(d["ddl_files"]) > 0)
    test("RD_FEE_03 tables 있음", "TB_FEE_RATE" in d["tables"])

    d = get_function_detail("NONEXISTENT")
    test("존재하지 않는 함수 → None", d is None)

    # ── get_call_graph ──
    print("\n[get_call_graph]")

    cg = get_call_graph_data("ST_BUY_01", depth=2)
    test("ST_BUY_01 calls 있음", len(cg["calls"]) > 0)
    callee_names = [c["callee"] for c in cg["calls"]]
    test("ST_BUY_01 → ST_MARGIN_01", "ST_MARGIN_01" in callee_names)
    test("ST_BUY_01 called_by 있음", len(cg["called_by"]) > 0)

    # ── find_by_table ──
    print("\n[find_by_table]")

    tb = find_functions_by_table("TB_ACCT_MST")
    test("TB_ACCT_MST DDL 있음", tb["ddl"] is not None)
    test("TB_ACCT_MST 컬럼 있음", len(tb["ddl"]["columns"]) > 0)
    test("TB_ACCT_MST 사용함수 있음", len(tb["usages"]) > 0)
    fn_names = [u["function_name"] for u in tb["usages"]]
    test("TB_ACCT_MST → AC_OPEN_01 사용", "AC_OPEN_01" in fn_names)

    # ── get_impact ──
    print("\n[get_impact]")

    imp = get_impact_data("CM_TAX_01")
    test("CM_TAX_01 type=function", imp["type"] == "function")
    test("CM_TAX_01 affected > 10", imp["affected_count"] > 10,
         f"got {imp['affected_count']}")
    names = [s["name"] for s in imp["affected_services"]]
    test("CM_TAX_01 → BN_INT_05 영향", "BN_INT_05" in names)
    test("CM_TAX_01 → DV_PAY_01 영향", "DV_PAY_01" in names)

    imp = get_impact_data("TB_FEE_RATE")
    test("TB_FEE_RATE type=table", imp["type"] == "table")
    test("TB_FEE_RATE affected > 0", imp["affected_count"] > 0)
    names = [s["name"] for s in imp["affected_services"]]
    test("TB_FEE_RATE → RD_FEE_03 직접", "RD_FEE_03" in names)

    imp = get_impact_data("NONEXISTENT")
    test("존재하지 않는 대상 → unknown", imp["type"] == "unknown")

    # ── get_business_flow ──
    print("\n[get_business_flow]")

    flow = get_business_flow_data("FD_PAY_01", depth=3)
    test("FD_PAY_01 steps 있음", len(flow["steps"]) > 0)
    test("FD_PAY_01 tables_touched 있음", len(flow["tables_touched"]) > 0)
    step_names = [s["name"] for s in flow["steps"]]
    test("FD_PAY_01 → FD_TAX_02 포함", "FD_TAX_02" in step_names)
    has_sql = any(len(s.get("sql_operations", [])) > 0 for s in flow["steps"])
    test("FD_PAY_01 SQL 연산 포함", has_sql)

    # ── find_by_error_code ──
    print("\n[find_by_error_code]")

    err = find_by_error_code_data("E101")
    test("E101 발견", len(err["occurrences"]) > 0)
    test("E101 → ST_BUY_01", err["occurrences"][0]["function_name"] == "ST_BUY_01")
    test("E101 에러 메시지 있음", len(err["occurrences"][0]["error_message"]) > 0)

    err = find_by_error_code_data("E999")
    test("존재하지 않는 에러 → 빈 결과", len(err["occurrences"]) == 0)

    # ── search_by_domain ──
    print("\n[search_by_domain]")

    dom = search_by_domain_data("ST")
    test("ST 함수 12개", len(dom["functions"]) == 12,
         f"got {len(dom['functions'])}")
    test("ST 구조체 있음", len(dom["structs"]) > 0)

    dom = search_by_domain_data("XX")
    test("존재하지 않는 도메인 → 빈 결과", len(dom["functions"]) == 0)

    # ── list_services ──
    print("\n[list_services]")

    svcs = list_all_services()
    test("서비스 81개", len(svcs) == 81, f"got {len(svcs)}")
    test("서비스에 name 있음", "name" in svcs[0])
    test("서비스에 description 있음", "description" in svcs[0])

    # ── Summary ──
    total = passed + failed
    print(f"\n{'=' * 60}")
    print(f"  {passed}/{total} passed, {failed} failed")
    print(f"{'=' * 60}")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
