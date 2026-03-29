"""평가용 Ground Truth — 쿼리별 기대 결과 정의.

각 시나리오는:
- target_function: 정답 진입점 함수
- required_files: 완전한 컨텍스트를 위해 반드시 필요한 파일들
- context_categories: 함수 본문 / 구조체 / 호출함수 / DDL 각각 필요 파일
- noise_files: 이 쿼리에 대해 반환되면 노이즈인 파일들

대규모 코드베이스(128파일, 81함수) 기준으로 노이즈 파일을 확장.
"""

GROUND_TRUTH: dict[str, dict] = {
    "환매 수수료 계산 로직": {
        "target_function": "RD_FEE_03",
        "required_files": [
            "RD_FEE_03.pc",     # 메인 함수
            "rd_fee_str.h",     # 입출력 구조체
            "CM_TAX_01.pc",     # 호출: 세금 계산
            "CM_DATE_CHK.pc",   # 호출: 일수 계산
            "TB_FEE_RATE.sql",  # 참조 테이블
        ],
        "context_categories": {
            "function_body": ["RD_FEE_03.pc"],
            "structs": ["rd_fee_str.h"],
            "called_functions": ["CM_TAX_01.pc", "CM_DATE_CHK.pc"],
            "table_ddl": ["TB_FEE_RATE.sql"],
        },
        "noise_files": [
            "BN_INT_05.pc",       # 채권 이자 — tax_amt, rate 유사
            "DV_PAY_01.pc",       # 배당금 — gross_amt/tax_amt 유사
            "FD_TAX_02.pc",       # 분배금 과세 — tax_rate 유사
            "ST_SETL_01.pc",      # 결제 — 무관
            "CM_FEE_CALC.pc",     # 수수료 단어 유사 but 다른 수수료
            "BN_COUPON_01.pc",    # rate/days 유사
            "FD_REDEEM_01.pc",    # 환매 단어 유사
            "RD_PENALTY_01.pc",   # 환매 도메인이지만 다른 함수
            "LN_INTEREST_01.pc",  # 이자/rate 유사
        ],
    },
    "분배금 지급 프로세스": {
        "target_function": "FD_PAY_01",
        "required_files": [
            "FD_PAY_01.pc",
            "fd_pay_str.h",
            "FD_TAX_02.pc",
            "FD_KSD_IF_01.pc",
            "TB_FUND_DIST.sql",
        ],
        "context_categories": {
            "function_body": ["FD_PAY_01.pc"],
            "structs": ["fd_pay_str.h"],
            "called_functions": ["FD_TAX_02.pc", "FD_KSD_IF_01.pc"],
            "table_ddl": ["TB_FUND_DIST.sql"],
        },
        "noise_files": [
            "DV_PAY_01.pc",       # 배당금 '지급' — 유사 단어
            "CM_TRANSFER_01.pc",  # '입금' 유사
            "RD_FEE_03.pc",       # 무관
            "FD_SUBSCRIBE_01.pc", # 같은 FD 도메인
            "FD_REDEEM_01.pc",    # 같은 FD 도메인
            "BN_INT_05.pc",       # 이자 '지급' 유사
            "FD_NAV_01.pc",       # 같은 도메인이지만 다른 로직
        ],
    },
    "주식 매수 주문": {
        "target_function": "ST_BUY_01",
        "required_files": [
            "ST_BUY_01.pc",
            "st_buy_str.h",
            "ST_MARGIN_01.pc",
            "TB_ORD_MST.sql",
        ],
        "context_categories": {
            "function_body": ["ST_BUY_01.pc"],
            "structs": ["st_buy_str.h"],
            "called_functions": ["ST_MARGIN_01.pc"],
            "table_ddl": ["TB_ORD_MST.sql"],
        },
        "noise_files": [
            "ST_SELL_01.pc",      # 매도 — ORD_MST/STK_CD 유사
            "ST_SETL_01.pc",      # 결제 — STK_CD/ACCT_NO 유사
            "JG_BAL_02.pc",       # 잔고 — STK_CD/QTY 유사
            "ST_CREDIT_01.pc",    # 신용매수 — ST_BUY_01 호출하지만 다른 함수
            "ST_BLOCK_01.pc",     # 대량매매 — ST_BUY_01 호출
            "ST_MODIFY_01.pc",    # 정정 — ORD_MST 유사
            "DV_REINVEST_01.pc",  # 배당재투자 — ST_BUY_01 호출
        ],
    },
    "계좌 개설 프로세스": {
        "target_function": "AC_OPEN_01",
        "required_files": [
            "AC_OPEN_01.pc",
            "ac_open_str.h",
            "CM_ACCT_GEN.pc",
            "AC_KYC_CHK.pc",
            "TB_ACCT_MST.sql",
        ],
        "context_categories": {
            "function_body": ["AC_OPEN_01.pc"],
            "structs": ["ac_open_str.h"],
            "called_functions": ["CM_ACCT_GEN.pc", "AC_KYC_CHK.pc"],
            "table_ddl": ["TB_ACCT_MST.sql"],
        },
        "noise_files": [
            "AC_CLOSE_01.pc",     # 해지 — ACCT_MST 유사
            "AC_CHANGE_01.pc",    # 변경 — ACCT_MST 유사
            "AC_FREEZE_01.pc",    # 동결 — ACCT_MST 유사
            "AC_GRADE_01.pc",     # 등급 — CUST_MST 유사
            "CM_TRANSFER_01.pc",  # 이체 — ACCT_BAL 유사
            "AC_MERGE_01.pc",     # 통합 — ACCT_MST 유사
            "AC_DORMANT_01.pc",   # 휴면 — ACCT_MST 유사
        ],
    },
    "T+2 결제 처리": {
        "target_function": "ST_SETL_01",
        "required_files": [
            "ST_SETL_01.pc",
            "st_setl_str.h",
            "TB_EXEC_HST.sql",
            "TB_SETL_MST.sql",
        ],
        "context_categories": {
            "function_body": ["ST_SETL_01.pc"],
            "structs": ["st_setl_str.h"],
            "called_functions": [],
            "table_ddl": ["TB_EXEC_HST.sql", "TB_SETL_MST.sql"],
        },
        "noise_files": [
            "ST_BUY_01.pc",       # 매수 — ORD_MST 유사
            "ST_SELL_01.pc",      # 매도 — STK_BAL 유사
            "JG_BAL_02.pc",       # 잔고 — STK_BAL 유사
            "CM_TRANSFER_01.pc",  # 이체 — ACCT_BAL 유사
            "RD_SETTLE_01.pc",    # '결제' 단어 유사
            "ST_CANCEL_01.pc",    # ORD_MST 유사
        ],
    },
    "배당금 세금 계산": {
        "target_function": "DV_PAY_01",
        "required_files": [
            "DV_PAY_01.pc",
            "dv_pay_str.h",
            "CM_TAX_01.pc",
            "CM_TRANSFER_01.pc",
            "TB_DIV_MST.sql",
        ],
        "context_categories": {
            "function_body": ["DV_PAY_01.pc"],
            "structs": ["dv_pay_str.h"],
            "called_functions": ["CM_TAX_01.pc", "CM_TRANSFER_01.pc"],
            "table_ddl": ["TB_DIV_MST.sql"],
        },
        "noise_files": [
            "FD_TAX_02.pc",       # 분배금 과세 — '과세' 유사
            "BN_INT_05.pc",       # 채권 이자 — tax_amt 유사
            "RD_FEE_03.pc",       # 환매 — tax_amt 유사
            "DV_WITHHOLD_01.pc",  # 원천징수 — 같은 DV 도메인
            "DV_CALC_01.pc",      # 배당산정 — 같은 DV 도메인
            "DV_REINVEST_01.pc",  # 재투자 — 같은 DV 도메인
            "FD_PAY_01.pc",       # 분배금 '지급' 유사
        ],
    },
    # ── 대규모 코드베이스 추가 시나리오 ──
    "신용매수 주문 처리": {
        "target_function": "ST_CREDIT_01",
        "required_files": [
            "ST_CREDIT_01.pc",
            "st_credit_str.h",
            "LN_CREDIT_01.pc",
            "ST_BUY_01.pc",
        ],
        "context_categories": {
            "function_body": ["ST_CREDIT_01.pc"],
            "structs": ["st_credit_str.h"],
            "called_functions": ["LN_CREDIT_01.pc", "ST_BUY_01.pc"],
            "table_ddl": [],
        },
        "noise_files": [
            "ST_SELL_01.pc",
            "ST_MARGIN_01.pc",
            "LN_MARGIN_01.pc",
            "ST_SHORT_01.pc",
            "ST_BLOCK_01.pc",
            "LN_REPAY_01.pc",
        ],
    },
    "채권 이자 지급": {
        "target_function": "BN_INT_05",
        "required_files": [
            "BN_INT_05.pc",
            "bn_int_str.h",
            "CM_TAX_01.pc",
            "CM_TRANSFER_01.pc",
            "TB_BND_ISSUE.sql",
        ],
        "context_categories": {
            "function_body": ["BN_INT_05.pc"],
            "structs": ["bn_int_str.h"],
            "called_functions": ["CM_TAX_01.pc", "CM_TRANSFER_01.pc"],
            "table_ddl": ["TB_BND_ISSUE.sql"],
        },
        "noise_files": [
            "BN_COUPON_01.pc",
            "BN_MATURE_01.pc",
            "FD_PAY_01.pc",
            "DV_PAY_01.pc",
            "LN_INTEREST_01.pc",
            "BN_ACCRUED_01.pc",
        ],
    },
    "반대매매 처리": {
        "target_function": "LN_FORCED_01",
        "required_files": [
            "LN_FORCED_01.pc",
            "ST_SELL_01.pc",
            "TB_LOAN_MST.sql",
        ],
        "context_categories": {
            "function_body": ["LN_FORCED_01.pc"],
            "structs": [],
            "called_functions": ["ST_SELL_01.pc"],
            "table_ddl": ["TB_LOAN_MST.sql"],
        },
        "noise_files": [
            "LN_CREDIT_01.pc",
            "LN_MARGIN_01.pc",
            "LN_REPAY_01.pc",
            "ST_BUY_01.pc",
            "RM_CREDIT_01.pc",
            "ST_SHORT_01.pc",
        ],
    },
    "VaR 리스크 계산": {
        "target_function": "RM_VAR_01",
        "required_files": [
            "RM_VAR_01.pc",
            "rm_var_str.h",
            "JG_POS_01.pc",
        ],
        "context_categories": {
            "function_body": ["RM_VAR_01.pc"],
            "structs": ["rm_var_str.h"],
            "called_functions": ["JG_POS_01.pc"],
            "table_ddl": [],
        },
        "noise_files": [
            "RM_STRESS_01.pc",
            "RM_EXPOSURE_01.pc",
            "RM_CREDIT_01.pc",
            "RM_LIMIT_01.pc",
            "JG_ASSET_01.pc",
            "JG_PNL_01.pc",
        ],
    },
}
