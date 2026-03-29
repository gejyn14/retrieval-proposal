#!/usr/bin/env python3
"""대규모 Pro*C 코드베이스 생성기.

증권사 실무 도메인 ~85개 함수, ~20개 테이블, ~23개 구조체를 생성한다.
도메인: CM(공통), AC(계좌), ST(주식), BN(채권), FD(펀드), RD(환매),
       DV(배당), JG(잔고), RM(리스크), IF(외부연동), LN(대출)
"""

from pathlib import Path

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "data" / "large_codebase"

# ============================================================
# 1. TABLE DDL DEFINITIONS
# ============================================================

TABLES = {
    "TB_ACCT_MST.sql": """\
CREATE TABLE TB_ACCT_MST (
    ACCT_NO     VARCHAR2(11)  NOT NULL,
    CUST_NO     VARCHAR2(10)  NOT NULL,
    CI_NO       VARCHAR2(64),
    ACCT_TP     VARCHAR2(2),
    ACCT_ST     VARCHAR2(2)   DEFAULT '01',
    BRNCH_CD    VARCHAR2(4),
    OPEN_DT     VARCHAR2(8),
    CLOSE_DT    VARCHAR2(8),
    CLOSE_YN    CHAR(1)       DEFAULT 'N',
    GRADE_CD    VARCHAR2(2),
    DORMANT_YN  CHAR(1)       DEFAULT 'N',
    FREEZE_YN   CHAR(1)       DEFAULT 'N',
    FREEZE_RSN  VARCHAR2(100),
    UPD_DT      VARCHAR2(14),
    CONSTRAINT PK_ACCT_MST PRIMARY KEY (ACCT_NO)
);
COMMENT ON TABLE TB_ACCT_MST IS '계좌 마스터';
""",
    "TB_CUST_MST.sql": """\
CREATE TABLE TB_CUST_MST (
    CUST_NO     VARCHAR2(10)  NOT NULL,
    CUST_NM     VARCHAR2(50),
    CI_NO       VARCHAR2(64),
    ID_TYPE     VARCHAR2(2),
    ID_NO       VARCHAR2(20),
    BIRTH_DT    VARCHAR2(8),
    CUST_TP     VARCHAR2(2),
    GRADE_CD    VARCHAR2(2)   DEFAULT '05',
    KYC_LEVEL   NUMBER(1)     DEFAULT 0,
    KYC_DT      VARCHAR2(8),
    AML_YN      CHAR(1)       DEFAULT 'N',
    EMAIL       VARCHAR2(100),
    PHONE       VARCHAR2(20),
    REG_DT      VARCHAR2(8),
    CONSTRAINT PK_CUST_MST PRIMARY KEY (CUST_NO)
);
COMMENT ON TABLE TB_CUST_MST IS '고객 마스터';
""",
    "TB_ORD_MST.sql": """\
CREATE TABLE TB_ORD_MST (
    ORD_NO      NUMBER(12)    NOT NULL,
    ACCT_NO     VARCHAR2(11)  NOT NULL,
    STK_CD      VARCHAR2(7),
    ORD_TP      VARCHAR2(4),
    ORD_SIDE    VARCHAR2(4),
    PRICE       NUMBER(12,2),
    QTY         NUMBER(10),
    EXEC_QTY    NUMBER(10)    DEFAULT 0,
    ORD_DT      VARCHAR2(8),
    ORD_TM      VARCHAR2(6),
    ORD_ST      VARCHAR2(2),
    ORIG_ORD_NO NUMBER(12),
    CREDIT_TP   VARCHAR2(2),
    CHANNEL     VARCHAR2(4),
    CONSTRAINT PK_ORD_MST PRIMARY KEY (ORD_NO)
);
COMMENT ON TABLE TB_ORD_MST IS '주문 원장';
""",
    "TB_EXEC_HST.sql": """\
CREATE TABLE TB_EXEC_HST (
    EXEC_NO     NUMBER(12)    NOT NULL,
    ORD_NO      NUMBER(12)    NOT NULL,
    ACCT_NO     VARCHAR2(11),
    STK_CD      VARCHAR2(7),
    EXEC_SIDE   VARCHAR2(4),
    EXEC_PRICE  NUMBER(12,2),
    EXEC_QTY    NUMBER(10),
    EXEC_AMT    NUMBER(15,2),
    EXEC_DT     VARCHAR2(8),
    EXEC_TM     VARCHAR2(6),
    SETL_DT     VARCHAR2(8),
    SETL_ST     VARCHAR2(2)   DEFAULT '00',
    CONSTRAINT PK_EXEC_HST PRIMARY KEY (EXEC_NO)
);
COMMENT ON TABLE TB_EXEC_HST IS '체결 내역';
""",
    "TB_STK_BAL.sql": """\
CREATE TABLE TB_STK_BAL (
    ACCT_NO     VARCHAR2(11)  NOT NULL,
    STK_CD      VARCHAR2(7)   NOT NULL,
    HOLD_QTY    NUMBER(10)    DEFAULT 0,
    AVG_PRICE   NUMBER(12,2),
    BUY_AMT     NUMBER(15,2),
    EVAL_AMT    NUMBER(15,2),
    SELL_AVAIL  NUMBER(10)    DEFAULT 0,
    UPD_DT      VARCHAR2(14),
    CONSTRAINT PK_STK_BAL PRIMARY KEY (ACCT_NO, STK_CD)
);
COMMENT ON TABLE TB_STK_BAL IS '주식 잔고';
""",
    "TB_ACCT_BAL.sql": """\
CREATE TABLE TB_ACCT_BAL (
    ACCT_NO     VARCHAR2(11)  NOT NULL,
    CASH_BAL    NUMBER(15,2)  DEFAULT 0,
    AVAIL_AMT   NUMBER(15,2)  DEFAULT 0,
    D1_AMT      NUMBER(15,2)  DEFAULT 0,
    D2_AMT      NUMBER(15,2)  DEFAULT 0,
    MARGIN_AMT  NUMBER(15,2)  DEFAULT 0,
    LOAN_AMT    NUMBER(15,2)  DEFAULT 0,
    UPD_DT      VARCHAR2(14),
    CONSTRAINT PK_ACCT_BAL PRIMARY KEY (ACCT_NO)
);
COMMENT ON TABLE TB_ACCT_BAL IS '계좌 잔액';
""",
    "TB_BND_BAL.sql": """\
CREATE TABLE TB_BND_BAL (
    ACCT_NO     VARCHAR2(11)  NOT NULL,
    BND_CD      VARCHAR2(12)  NOT NULL,
    HOLD_QTY    NUMBER(15,2)  DEFAULT 0,
    HOLD_AMT    NUMBER(15,2),
    BUY_PRICE   NUMBER(12,6),
    BUY_DT      VARCHAR2(8),
    EVAL_AMT    NUMBER(15,2),
    UPD_DT      VARCHAR2(14),
    CONSTRAINT PK_BND_BAL PRIMARY KEY (ACCT_NO, BND_CD)
);
COMMENT ON TABLE TB_BND_BAL IS '채권 잔고';
""",
    "TB_FND_BAL.sql": """\
CREATE TABLE TB_FND_BAL (
    ACCT_NO     VARCHAR2(11)  NOT NULL,
    FUND_CD     VARCHAR2(12)  NOT NULL,
    HOLD_QTY    NUMBER(15,2)  DEFAULT 0,
    BUY_AMT     NUMBER(15,2),
    EVAL_AMT    NUMBER(15,2),
    BUY_DT      VARCHAR2(8),
    UPD_DT      VARCHAR2(14),
    CONSTRAINT PK_FND_BAL PRIMARY KEY (ACCT_NO, FUND_CD)
);
COMMENT ON TABLE TB_FND_BAL IS '펀드 잔고';
""",
    "TB_FEE_RATE.sql": """\
CREATE TABLE TB_FEE_RATE (
    FUND_CD     VARCHAR2(12)  NOT NULL,
    SEQ         NUMBER(3)     NOT NULL,
    FR_DAYS     NUMBER(5),
    TO_DAYS     NUMBER(5),
    FEE_RATE    NUMBER(10,6),
    USE_YN      CHAR(1)       DEFAULT 'Y',
    CONSTRAINT PK_FEE_RATE PRIMARY KEY (FUND_CD, SEQ)
);
COMMENT ON TABLE TB_FEE_RATE IS '펀드 환매수수료율 관리';
""",
    "TB_FUND_DIST.sql": """\
CREATE TABLE TB_FUND_DIST (
    FUND_CD     VARCHAR2(12)  NOT NULL,
    DIST_DT     VARCHAR2(8)   NOT NULL,
    DIST_TP     VARCHAR2(4),
    DIST_AMT    NUMBER(12,4),
    BASE_DT     VARCHAR2(8),
    PAY_DT      VARCHAR2(8),
    USE_YN      CHAR(1)       DEFAULT 'Y',
    CONSTRAINT PK_FUND_DIST PRIMARY KEY (FUND_CD, DIST_DT)
);
COMMENT ON TABLE TB_FUND_DIST IS '펀드 분배금';
""",
    "TB_TAX_MST.sql": """\
CREATE TABLE TB_TAX_MST (
    TAX_TYPE    VARCHAR2(10)  NOT NULL,
    TAX_RATE    NUMBER(10,6),
    SURTAX_RATE NUMBER(10,6),
    LOCAL_RATE  NUMBER(10,6),
    EFF_FR_DT   VARCHAR2(8),
    EFF_TO_DT   VARCHAR2(8),
    USE_YN      CHAR(1)       DEFAULT 'Y',
    CONSTRAINT PK_TAX_MST PRIMARY KEY (TAX_TYPE)
);
COMMENT ON TABLE TB_TAX_MST IS '세금율 마스터';
""",
    "TB_MARGIN_MST.sql": """\
CREATE TABLE TB_MARGIN_MST (
    STK_CD      VARCHAR2(7)   NOT NULL,
    MARGIN_GRP  VARCHAR2(2),
    MARGIN_RATE NUMBER(5,2),
    SUBST_RATE  NUMBER(5,2),
    EFF_DT      VARCHAR2(8),
    USE_YN      CHAR(1)       DEFAULT 'Y',
    CONSTRAINT PK_MARGIN_MST PRIMARY KEY (STK_CD)
);
COMMENT ON TABLE TB_MARGIN_MST IS '증거금율 마스터';
""",
    "TB_HOLIDAY.sql": """\
CREATE TABLE TB_HOLIDAY (
    BASE_DT     VARCHAR2(8)   NOT NULL,
    MKT_TP      VARCHAR2(4)   DEFAULT 'KRX',
    HOLIDAY_NM  VARCHAR2(50),
    USE_YN      CHAR(1)       DEFAULT 'Y',
    CONSTRAINT PK_HOLIDAY PRIMARY KEY (BASE_DT, MKT_TP)
);
COMMENT ON TABLE TB_HOLIDAY IS '휴장일 관리';
""",
    "TB_RATE_MST.sql": """\
CREATE TABLE TB_RATE_MST (
    RATE_TP     VARCHAR2(10)  NOT NULL,
    BASE_DT     VARCHAR2(8)   NOT NULL,
    RATE_VAL    NUMBER(12,6),
    CUR_CD      VARCHAR2(3),
    USE_YN      CHAR(1)       DEFAULT 'Y',
    CONSTRAINT PK_RATE_MST PRIMARY KEY (RATE_TP, BASE_DT)
);
COMMENT ON TABLE TB_RATE_MST IS '금리/환율 마스터';
""",
    "TB_LIMIT_MST.sql": """\
CREATE TABLE TB_LIMIT_MST (
    LIMIT_TP    VARCHAR2(10)  NOT NULL,
    LIMIT_CD    VARCHAR2(20)  NOT NULL,
    LIMIT_AMT   NUMBER(15,2),
    USED_AMT    NUMBER(15,2)  DEFAULT 0,
    WARN_RATE   NUMBER(5,2)   DEFAULT 80,
    EFF_DT      VARCHAR2(8),
    USE_YN      CHAR(1)       DEFAULT 'Y',
    CONSTRAINT PK_LIMIT_MST PRIMARY KEY (LIMIT_TP, LIMIT_CD)
);
COMMENT ON TABLE TB_LIMIT_MST IS '한도 관리';
""",
    "TB_DIV_MST.sql": """\
CREATE TABLE TB_DIV_MST (
    STK_CD      VARCHAR2(7)   NOT NULL,
    DIV_DT      VARCHAR2(8)   NOT NULL,
    DIV_TP      VARCHAR2(4),
    DIV_AMT     NUMBER(12,2),
    RECORD_DT   VARCHAR2(8),
    PAY_DT      VARCHAR2(8),
    TAX_RATE    NUMBER(10,6),
    USE_YN      CHAR(1)       DEFAULT 'Y',
    CONSTRAINT PK_DIV_MST PRIMARY KEY (STK_CD, DIV_DT)
);
COMMENT ON TABLE TB_DIV_MST IS '배당금 마스터';
""",
    "TB_BND_ISSUE.sql": """\
CREATE TABLE TB_BND_ISSUE (
    BND_CD      VARCHAR2(12)  NOT NULL,
    BND_NM      VARCHAR2(100),
    ISSUE_DT    VARCHAR2(8),
    MATURE_DT   VARCHAR2(8),
    COUPON_RATE NUMBER(10,6),
    COUPON_FREQ NUMBER(2)     DEFAULT 2,
    FACE_AMT    NUMBER(15,2),
    ISSUER      VARCHAR2(50),
    CREDIT_GRD  VARCHAR2(5),
    BND_TP      VARCHAR2(4),
    USE_YN      CHAR(1)       DEFAULT 'Y',
    CONSTRAINT PK_BND_ISSUE PRIMARY KEY (BND_CD)
);
COMMENT ON TABLE TB_BND_ISSUE IS '채권 발행 정보';
""",
    "TB_SETL_MST.sql": """\
CREATE TABLE TB_SETL_MST (
    SETL_NO     NUMBER(12)    NOT NULL,
    EXEC_NO     NUMBER(12),
    ACCT_NO     VARCHAR2(11),
    SETL_TP     VARCHAR2(4),
    SETL_DT     VARCHAR2(8),
    SETL_AMT    NUMBER(15,2),
    SETL_ST     VARCHAR2(2)   DEFAULT '00',
    PROC_DT     VARCHAR2(8),
    CONSTRAINT PK_SETL_MST PRIMARY KEY (SETL_NO)
);
COMMENT ON TABLE TB_SETL_MST IS '결제 원장';
""",
    "TB_LOAN_MST.sql": """\
CREATE TABLE TB_LOAN_MST (
    LOAN_NO     NUMBER(12)    NOT NULL,
    ACCT_NO     VARCHAR2(11)  NOT NULL,
    LOAN_TP     VARCHAR2(4),
    LOAN_AMT    NUMBER(15,2),
    LOAN_BAL    NUMBER(15,2),
    INT_RATE    NUMBER(10,6),
    LOAN_DT     VARCHAR2(8),
    DUE_DT      VARCHAR2(8),
    LOAN_ST     VARCHAR2(2)   DEFAULT '01',
    COLL_TP     VARCHAR2(4),
    COLL_AMT    NUMBER(15,2),
    CONSTRAINT PK_LOAN_MST PRIMARY KEY (LOAN_NO)
);
COMMENT ON TABLE TB_LOAN_MST IS '대출 원장';
""",
    "TB_TX_HIST.sql": """\
CREATE TABLE TB_TX_HIST (
    TX_NO       NUMBER(15)    NOT NULL,
    TX_DT       VARCHAR2(8),
    TX_TM       VARCHAR2(6),
    SVC_NM      VARCHAR2(20),
    ACCT_NO     VARCHAR2(11),
    TX_TP       VARCHAR2(10),
    TX_AMT      NUMBER(15,2),
    TX_DESC     VARCHAR2(200),
    RESULT_CD   VARCHAR2(4),
    ERR_MSG     VARCHAR2(200),
    USER_ID     VARCHAR2(20),
    CONSTRAINT PK_TX_HIST PRIMARY KEY (TX_NO)
);
COMMENT ON TABLE TB_TX_HIST IS '거래 이력';
""",
    "TB_KSD_IF.sql": """\
CREATE TABLE TB_KSD_IF (
    IF_NO       NUMBER(12)    NOT NULL,
    IF_DT       VARCHAR2(8),
    IF_TP       VARCHAR2(10),
    FUND_CD     VARCHAR2(12),
    ACCT_NO     VARCHAR2(11),
    QTY         NUMBER(15,2),
    AMT         NUMBER(15,2),
    SEND_ST     VARCHAR2(2)   DEFAULT '00',
    RECV_ST     VARCHAR2(2),
    ERR_CD      VARCHAR2(10),
    CONSTRAINT PK_KSD_IF PRIMARY KEY (IF_NO)
);
COMMENT ON TABLE TB_KSD_IF IS 'KSD 인터페이스 전문';
""",
    "TB_FND_NAV.sql": """\
CREATE TABLE TB_FND_NAV (
    FUND_CD     VARCHAR2(12)  NOT NULL,
    BASE_DT     VARCHAR2(8)   NOT NULL,
    NAV         NUMBER(15,6),
    TOT_ASSET   NUMBER(18,2),
    TOT_UNITS   NUMBER(18,2),
    PREV_NAV    NUMBER(15,6),
    CHG_RATE    NUMBER(10,6),
    CONSTRAINT PK_FND_NAV PRIMARY KEY (FUND_CD, BASE_DT)
);
COMMENT ON TABLE TB_FND_NAV IS '펀드 기준가';
""",
}

# ============================================================
# 2. STRUCT HEADER DEFINITIONS
# ============================================================

HEADERS = {
    # --- Account ---
    "ac_open_str.h": """\
/* 계좌 개설 전문 구조체 */
typedef struct {
    char cust_no[11];
    char ci_no[65];
    char acct_type[3];
    char brnch_cd[5];
    char id_type[3];
    char id_no[21];
} ac_open_in_t;

typedef struct {
    char acct_no[11];
    int  kyc_result;
    char err_cd[5];
    char err_msg[101];
} ac_open_out_t;
""",
    "ac_close_str.h": """\
/* 계좌 해지 전문 구조체 */
typedef struct {
    char acct_no[11];
    char close_rsn[5];
    char auth_key[33];
} ac_close_in_t;

typedef struct {
    double refund_amt;
    char close_dt[9];
    char err_cd[5];
    char err_msg[101];
} ac_close_out_t;
""",
    "ac_grade_str.h": """\
/* 고객 등급 산정 전문 구조체 */
typedef struct {
    char cust_no[11];
    char base_dt[9];
} ac_grade_in_t;

typedef struct {
    char prev_grade[3];
    char new_grade[3];
    double total_asset;
    int  tx_count;
    char err_cd[5];
    char err_msg[101];
} ac_grade_out_t;
""",
    # --- Stock ---
    "st_buy_str.h": """\
/* 주식 매수 전문 구조체 */
typedef struct {
    char acct_no[11];
    char stk_cd[7];
    double price;
    long qty;
    char ord_type[3];   /* 00:지정가 01:시장가 */
    char credit_tp[3];  /* 00:보통 01:신용 */
} st_buy_in_t;

typedef struct {
    long ord_no;
    double margin_amt;
    double order_amt;
    char err_cd[5];
    char err_msg[101];
} st_buy_out_t;
""",
    "st_sell_str.h": """\
/* 주식 매도 전문 구조체 */
typedef struct {
    char acct_no[11];
    char stk_cd[7];
    double price;
    long qty;
    char ord_type[3];
} st_sell_in_t;

typedef struct {
    long ord_no;
    double est_proceeds;
    double est_tax;
    char err_cd[5];
    char err_msg[101];
} st_sell_out_t;
""",
    "st_setl_str.h": """\
/* 주식 결제 전문 구조체 */
typedef struct {
    char setl_dt[9];
    char acct_no[11];
    long exec_no;
} st_setl_in_t;

typedef struct {
    double setl_amt;
    long setl_qty;
    char setl_st[3];
    char err_cd[5];
    char err_msg[101];
} st_setl_out_t;
""",
    "st_credit_str.h": """\
/* 신용매수 전문 구조체 */
typedef struct {
    char acct_no[11];
    char stk_cd[7];
    double price;
    long qty;
    char credit_tp[3];
    int  credit_days;
} st_credit_in_t;

typedef struct {
    long ord_no;
    long loan_no;
    double loan_amt;
    double margin_amt;
    double int_rate;
    char err_cd[5];
    char err_msg[101];
} st_credit_out_t;
""",
    # --- Bond ---
    "bn_buy_str.h": """\
/* 채권 매수 전문 구조체 */
typedef struct {
    char acct_no[11];
    char bnd_cd[13];
    double face_amt;
    double price;
    char buy_tp[3];
} bn_buy_in_t;

typedef struct {
    double buy_amt;
    double accrued_int;
    double total_amt;
    char err_cd[5];
    char err_msg[101];
} bn_buy_out_t;
""",
    "bn_int_str.h": """\
/* 채권 이자 전문 구조체 */
typedef struct {
    char acct_no[11];
    char bnd_cd[13];
    char pay_dt[9];
} bn_int_in_t;

typedef struct {
    double gross_int;
    double tax_amt;
    double net_int;
    char err_cd[5];
    char err_msg[101];
} bn_int_out_t;
""",
    "bn_coupon_str.h": """\
/* 이표 계산 전문 구조체 */
typedef struct {
    char bnd_cd[13];
    char from_dt[9];
    char to_dt[9];
    double face_amt;
} bn_coupon_in_t;

typedef struct {
    double coupon_amt;
    int  accrued_days;
    double accrued_int;
    char err_cd[5];
    char err_msg[101];
} bn_coupon_out_t;
""",
    "bn_mature_str.h": """\
/* 채권 만기 상환 전문 구조체 */
typedef struct {
    char acct_no[11];
    char bnd_cd[13];
} bn_mature_in_t;

typedef struct {
    double face_amt;
    double last_coupon;
    double tax_amt;
    double net_amt;
    char err_cd[5];
    char err_msg[101];
} bn_mature_out_t;
""",
    # --- Fund ---
    "fd_sub_str.h": """\
/* 펀드 가입(설정) 전문 구조체 */
typedef struct {
    char acct_no[11];
    char fund_cd[13];
    double invest_amt;
    char reinvest_yn[2];
} fd_sub_in_t;

typedef struct {
    double nav;
    double alloc_qty;
    double fee_amt;
    double net_invest;
    char err_cd[5];
    char err_msg[101];
} fd_sub_out_t;
""",
    "fd_redeem_str.h": """\
/* 펀드 환매 전문 구조체 */
typedef struct {
    char acct_no[11];
    char fund_cd[13];
    double redeem_qty;
    char redeem_tp[3];   /* 01:전액 02:일부 */
} fd_redeem_in_t;

typedef struct {
    double nav;
    double gross_amt;
    double fee_amt;
    double tax_amt;
    double net_amt;
    char err_cd[5];
    char err_msg[101];
} fd_redeem_out_t;
""",
    "fd_pay_str.h": """\
/* 분배금 지급 전문 구조체 */
typedef struct {
    char acct_no[11];
    char fund_cd[13];
    char pay_dt[9];
    char acct_type[3];
} fd_pay_in_t;

typedef struct {
    double gross_amt;
    double tax_amt;
    double net_amt;
    char err_cd[5];
    char err_msg[101];
} fd_pay_out_t;
""",
    # --- Redeem ---
    "rd_fee_str.h": """\
/* 환매 수수료 전문 구조체 */
typedef struct {
    char fund_cd[13];
    char buy_dt[9];
    char sell_dt[9];
    double sell_amt;
    long sell_qty;
} rd_fee_in_t;

typedef struct {
    double fee_rate;
    double fee_amt;
    double tax_amt;
    double net_amt;
    int  hold_days;
    char err_cd[5];
    char err_msg[101];
} rd_fee_out_t;
""",
    "rd_proc_str.h": """\
/* 수익증권 환매 처리 전문 구조체 */
typedef struct {
    char acct_no[11];
    char fund_cd[13];
    long sell_qty;
} rd_proc_in_t;

typedef struct {
    double sell_amt;
    double fee_amt;
    double tax_amt;
    double net_amt;
    char err_cd[5];
    char err_msg[101];
} rd_proc_out_t;
""",
    # --- Dividend ---
    "dv_pay_str.h": """\
/* 배당금 지급 전문 구조체 */
typedef struct {
    char acct_no[11];
    char stk_cd[7];
    char div_dt[9];
    long hold_qty;
} dv_pay_in_t;

typedef struct {
    double gross_amt;
    double tax_amt;
    double net_amt;
    char err_cd[5];
    char err_msg[101];
} dv_pay_out_t;
""",
    # --- Balance ---
    "jg_bal_str.h": """\
/* 잔고 조회 전문 구조체 */
typedef struct {
    char acct_no[11];
    char qry_tp[3];     /* 01:주식 02:채권 03:펀드 04:전체 */
    char base_dt[9];
} jg_bal_in_t;

typedef struct {
    double stk_eval;
    double bnd_eval;
    double fnd_eval;
    double cash_bal;
    double total_asset;
    int  item_cnt;
    char err_cd[5];
    char err_msg[101];
} jg_bal_out_t;
""",
    "jg_asset_str.h": """\
/* 자산 평가 전문 구조체 */
typedef struct {
    char acct_no[11];
    char base_dt[9];
    char eval_tp[3];    /* 01:시가 02:장부가 */
} jg_asset_in_t;

typedef struct {
    double stk_eval;
    double bnd_eval;
    double fnd_eval;
    double cash_bal;
    double total_asset;
    double pnl_amt;
    double pnl_rate;
    char err_cd[5];
    char err_msg[101];
} jg_asset_out_t;
""",
    # --- Risk ---
    "rm_exposure_str.h": """\
/* 익스포저 산출 전문 구조체 */
typedef struct {
    char acct_no[11];
    char asset_tp[3];
    char base_dt[9];
} rm_exposure_in_t;

typedef struct {
    double gross_exposure;
    double net_exposure;
    double limit_amt;
    double usage_rate;
    char risk_level[3];
    char err_cd[5];
    char err_msg[101];
} rm_exposure_out_t;
""",
    "rm_var_str.h": """\
/* VaR 계산 전문 구조체 */
typedef struct {
    char acct_no[11];
    char method[5];     /* HIST:역사적 PARA:모수적 MONTE:몬테카를로 */
    int  conf_level;
    int  hold_period;
    char base_dt[9];
} rm_var_in_t;

typedef struct {
    double var_amt;
    double cvar_amt;
    double portfolio_val;
    double var_rate;
    char err_cd[5];
    char err_msg[101];
} rm_var_out_t;
""",
    # --- Loan ---
    "ln_credit_str.h": """\
/* 신용 대출 전문 구조체 */
typedef struct {
    char acct_no[11];
    char loan_tp[5];
    double loan_amt;
    int  loan_days;
    char coll_tp[5];
} ln_credit_in_t;

typedef struct {
    long loan_no;
    double approved_amt;
    double int_rate;
    char due_dt[9];
    char err_cd[5];
    char err_msg[101];
} ln_credit_out_t;
""",
    "ln_repay_str.h": """\
/* 대출 상환 전문 구조체 */
typedef struct {
    long loan_no;
    char acct_no[11];
    double repay_amt;
    char repay_tp[3];   /* 01:전액 02:일부 03:이자만 */
} ln_repay_in_t;

typedef struct {
    double principal;
    double interest;
    double total_repay;
    double remain_bal;
    char err_cd[5];
    char err_msg[101];
} ln_repay_out_t;
""",
    # --- Interface ---
    "if_krx_str.h": """\
/* 거래소(KRX) 인터페이스 전문 구조체 */
typedef struct {
    char msg_tp[5];
    char stk_cd[7];
    char ord_side[3];
    double price;
    long qty;
    long ord_no;
} if_krx_in_t;

typedef struct {
    char resp_cd[5];
    long krx_ord_no;
    char recv_tm[7];
    char err_cd[5];
    char err_msg[101];
} if_krx_out_t;
""",
    "if_ksd_str.h": """\
/* 예탁원(KSD) 인터페이스 전문 구조체 */
typedef struct {
    char msg_tp[5];
    char fund_cd[13];
    char acct_no[11];
    double qty;
    double amt;
} if_ksd_in_t;

typedef struct {
    char resp_cd[5];
    long ksd_ref_no;
    char proc_dt[9];
    char err_cd[5];
    char err_msg[101];
} if_ksd_out_t;
""",
}

# ============================================================
# 3. FUNCTION DEFINITIONS (Pro*C)
# ============================================================

FUNCTIONS = {
    # ========== Common (CM) ==========
    "CM_LOG_01.pc": """\
/* 거래 로그 기록 공통 - 모든 서비스 호출 시 거래내역 이력 저장 처리 */
#include "proframe.h"

EXEC SQL INCLUDE SQLCA;

int CM_LOG_01(const char *svc_nm, const char *acct_no, const char *tx_desc) {
    EXEC SQL BEGIN DECLARE SECTION;
    char    v_svc[21];
    char    v_acct[11];
    char    v_desc[201];
    EXEC SQL END DECLARE SECTION;

    strcpy(v_svc, svc_nm);
    strcpy(v_acct, acct_no);
    strcpy(v_desc, tx_desc);

    EXEC SQL INSERT INTO TB_TX_HIST
        (TX_NO, TX_DT, TX_TM, SVC_NM, ACCT_NO, TX_TP, TX_DESC, RESULT_CD)
        VALUES (SQ_TX_NO.NEXTVAL, TO_CHAR(SYSDATE,'YYYYMMDD'),
                TO_CHAR(SYSDATE,'HH24MISS'), :v_svc, :v_acct, 'NORMAL',
                :v_desc, '0000');

    if (SQLCA.sqlcode != 0) {
        return FAIL;
    }
    return SUCCESS;
}
""",
    "CM_AUTH_01.pc": """\
/* 사용자 권한 검증 처리 - 계좌 상태 및 동결 여부 확인, 인증 레벨 체크 */
#include "proframe.h"

EXEC SQL INCLUDE SQLCA;

int CM_AUTH_01(const char *acct_no, const char *auth_key, int auth_level) {
    EXEC SQL BEGIN DECLARE SECTION;
    char    v_acct[11];
    char    v_auth[33];
    int     v_level;
    int     v_result;
    EXEC SQL END DECLARE SECTION;

    strcpy(v_acct, acct_no);
    strcpy(v_auth, auth_key);
    v_level = auth_level;

    EXEC SQL SELECT CASE WHEN ACCT_ST = '01' AND FREEZE_YN = 'N' THEN 1 ELSE 0 END
        INTO :v_result
        FROM TB_ACCT_MST
        WHERE ACCT_NO = :v_acct;

    if (SQLCA.sqlcode != 0 || v_result == 0) {
        return FAIL;
    }
    return SUCCESS;
}
""",
    "CM_SEQ_GEN.pc": """\
/* 시퀀스 채번 공통 처리 - 거래번호 일련번호 자동 생성 */
#include "proframe.h"

EXEC SQL INCLUDE SQLCA;

int CM_SEQ_GEN(const char *seq_name, long *seq_val) {
    EXEC SQL BEGIN DECLARE SECTION;
    long    v_seq;
    char    v_sql[100];
    EXEC SQL END DECLARE SECTION;

    EXEC SQL SELECT SQ_COMMON.NEXTVAL INTO :v_seq FROM DUAL;

    if (SQLCA.sqlcode != 0) {
        return FAIL;
    }
    *seq_val = v_seq;
    return SUCCESS;
}
""",
    "CM_ACCT_GEN.pc": """\
/* 계좌번호 채번 처리 - 지점코드 기반 신규 계좌번호 생성 */
#include "proframe.h"

EXEC SQL INCLUDE SQLCA;

int CM_ACCT_GEN(const char *brnch_cd, char *acct_no) {
    EXEC SQL BEGIN DECLARE SECTION;
    char    v_brnch[5];
    long    v_seq;
    EXEC SQL END DECLARE SECTION;

    strcpy(v_brnch, brnch_cd);

    /* 시퀀스 채번 */
    CM_SEQ_GEN("ACCT", &v_seq);

    /* 지점코드(4) + 일련번호(6) + 체크(1) */
    sprintf(acct_no, "%s%06ld%d", v_brnch, v_seq, (int)(v_seq % 10));

    return SUCCESS;
}
""",
    "CM_FEE_CALC.pc": """\
/* 공통 수수료 계산 처리 - 수수료 유형별 수수료율 조회 및 수수료 금액 산출 */
#include "proframe.h"

EXEC SQL INCLUDE SQLCA;

int CM_FEE_CALC(const char *fee_type, double base_amt, double *fee_amt) {
    EXEC SQL BEGIN DECLARE SECTION;
    char    v_type[11];
    double  v_rate;
    double  v_min_fee;
    EXEC SQL END DECLARE SECTION;

    strcpy(v_type, fee_type);

    EXEC SQL SELECT FEE_RATE, MIN_FEE INTO :v_rate, :v_min_fee
        FROM TB_FEE_MST
        WHERE FEE_TYPE = :v_type AND USE_YN = 'Y';

    if (SQLCA.sqlcode != 0) {
        *fee_amt = 0;
        return FAIL;
    }

    *fee_amt = base_amt * v_rate;
    if (*fee_amt < v_min_fee) {
        *fee_amt = v_min_fee;
    }

    return SUCCESS;
}
""",
    "CM_HOLIDAY_CHK.pc": """\
/* 휴장일 체크 조회 - 영업일 여부 판단, 시장 유형별 휴장일 확인 */
#include "proframe.h"

EXEC SQL INCLUDE SQLCA;

int CM_HOLIDAY_CHK(const char *base_dt, const char *mkt_tp) {
    EXEC SQL BEGIN DECLARE SECTION;
    char    v_dt[9];
    char    v_mkt[5];
    int     v_cnt;
    EXEC SQL END DECLARE SECTION;

    strcpy(v_dt, base_dt);
    strcpy(v_mkt, mkt_tp);

    EXEC SQL SELECT COUNT(*) INTO :v_cnt
        FROM TB_HOLIDAY
        WHERE BASE_DT = :v_dt
        AND MKT_TP = :v_mkt
        AND USE_YN = 'Y';

    return (v_cnt > 0) ? 1 : 0;  /* 1=휴장일, 0=영업일 */
}
""",
    "CM_DATE_CHK.pc": """\
/* 영업일 일수 계산 처리 - 두 날짜 간 역일 차이에서 휴장일 제외한 영업일수 산출 */
#include "proframe.h"

EXEC SQL INCLUDE SQLCA;

int CM_DATE_CHK(const char *from_dt, const char *to_dt) {
    EXEC SQL BEGIN DECLARE SECTION;
    int     diff_days;
    int     holiday_cnt;
    char    v_from[9];
    char    v_to[9];
    EXEC SQL END DECLARE SECTION;

    strcpy(v_from, from_dt);
    strcpy(v_to, to_dt);

    /* 역일 차이 */
    EXEC SQL SELECT TO_DATE(:v_to,'YYYYMMDD') - TO_DATE(:v_from,'YYYYMMDD')
        INTO :diff_days FROM DUAL;

    /* 휴장일 제외 */
    EXEC SQL SELECT COUNT(*) INTO :holiday_cnt
        FROM TB_HOLIDAY
        WHERE BASE_DT BETWEEN :v_from AND :v_to
        AND USE_YN = 'Y';

    /* 주말 제외 로직은 CM_HOLIDAY_CHK로 위임 */
    CM_HOLIDAY_CHK(from_dt, "KRX");

    return diff_days - holiday_cnt;
}
""",
    "CM_RATE_01.pc": """\
/* 금리 환율 조회 처리 - 기준일자별 금리 이자율 환율 시세 조회 */
#include "proframe.h"

EXEC SQL INCLUDE SQLCA;

int CM_RATE_01(const char *rate_tp, const char *base_dt, double *rate_val) {
    EXEC SQL BEGIN DECLARE SECTION;
    char    v_tp[11];
    char    v_dt[9];
    double  v_rate;
    EXEC SQL END DECLARE SECTION;

    strcpy(v_tp, rate_tp);
    strcpy(v_dt, base_dt);

    EXEC SQL SELECT RATE_VAL INTO :v_rate
        FROM TB_RATE_MST
        WHERE RATE_TP = :v_tp
        AND BASE_DT = (SELECT MAX(BASE_DT) FROM TB_RATE_MST
                        WHERE RATE_TP = :v_tp AND BASE_DT <= :v_dt);

    if (SQLCA.sqlcode != 0) {
        *rate_val = 0;
        return FAIL;
    }
    *rate_val = v_rate;
    return SUCCESS;
}
""",
    "CM_LIMIT_CHK.pc": """\
/* 한도 체크 처리 - 거래 한도 잔여 한도 확인 및 사용액 갱신 */
#include "proframe.h"

EXEC SQL INCLUDE SQLCA;

int CM_LIMIT_CHK(const char *limit_tp, const char *limit_cd, double req_amt) {
    EXEC SQL BEGIN DECLARE SECTION;
    char    v_tp[11];
    char    v_cd[21];
    double  v_limit;
    double  v_used;
    EXEC SQL END DECLARE SECTION;

    strcpy(v_tp, limit_tp);
    strcpy(v_cd, limit_cd);

    EXEC SQL SELECT LIMIT_AMT, USED_AMT INTO :v_limit, :v_used
        FROM TB_LIMIT_MST
        WHERE LIMIT_TP = :v_tp AND LIMIT_CD = :v_cd AND USE_YN = 'Y';

    if (SQLCA.sqlcode != 0) {
        return FAIL;
    }

    if (v_used + req_amt > v_limit) {
        return FAIL;  /* 한도 초과 */
    }

    /* 사용액 갱신 */
    EXEC SQL UPDATE TB_LIMIT_MST
        SET USED_AMT = USED_AMT + :req_amt
        WHERE LIMIT_TP = :v_tp AND LIMIT_CD = :v_cd;

    return SUCCESS;
}
""",
    "CM_NOTIFY_01.pc": """\
/* 알림 발송 공통 처리 - 고객 SMS 이메일 알림 메시지 발송 큐 등록 */
#include "proframe.h"

EXEC SQL INCLUDE SQLCA;

int CM_NOTIFY_01(const char *cust_no, const char *msg_tp, const char *msg_body) {
    EXEC SQL BEGIN DECLARE SECTION;
    char    v_cust[11];
    char    v_email[101];
    char    v_phone[21];
    EXEC SQL END DECLARE SECTION;

    strcpy(v_cust, cust_no);

    EXEC SQL SELECT EMAIL, PHONE INTO :v_email, :v_phone
        FROM TB_CUST_MST
        WHERE CUST_NO = :v_cust;

    if (SQLCA.sqlcode != 0) {
        return FAIL;
    }

    /* SMS/이메일 발송 큐 등록 */
    EXEC SQL INSERT INTO TB_NOTIFY_QUEUE
        (SEQ, CUST_NO, MSG_TP, MSG_BODY, SEND_ST, REG_DT)
        VALUES (SQ_NOTIFY.NEXTVAL, :v_cust, :msg_tp, :msg_body,
                '00', TO_CHAR(SYSDATE,'YYYYMMDD'));

    return SUCCESS;
}
""",
    "CM_CRYPTO_01.pc": """\
/* 암호화 복호화 공통 처리 - 개인정보 계좌번호 암호화 및 복호화 */
#include "proframe.h"

EXEC SQL INCLUDE SQLCA;

int CM_CRYPTO_01(const char *plain, char *cipher, const char *direction) {
    EXEC SQL BEGIN DECLARE SECTION;
    char    v_plain[256];
    char    v_cipher[256];
    char    v_dir[4];
    EXEC SQL END DECLARE SECTION;

    strcpy(v_plain, plain);
    strcpy(v_dir, direction);

    if (strcmp(v_dir, "ENC") == 0) {
        EXEC SQL SELECT CRYPTO_ENC(:v_plain) INTO :v_cipher FROM DUAL;
    } else {
        EXEC SQL SELECT CRYPTO_DEC(:v_plain) INTO :v_cipher FROM DUAL;
    }

    if (SQLCA.sqlcode != 0) {
        return FAIL;
    }
    strcpy(cipher, v_cipher);
    return SUCCESS;
}
""",
    "CM_TAX_01.pc": """\
/* 공통 세금 계산 처리 - 소득세 주민세 원천징수 세액 산출 */
#include "proframe.h"

EXEC SQL INCLUDE SQLCA;

int CM_TAX_01(double amt, double *tax) {
    EXEC SQL BEGIN DECLARE SECTION;
    double  tax_rate;
    double  surtax_rate;
    EXEC SQL END DECLARE SECTION;

    EXEC SQL SELECT TAX_RATE, SURTAX_RATE INTO :tax_rate, :surtax_rate
        FROM TB_TAX_MST
        WHERE TAX_TYPE = 'DEFAULT'
        AND USE_YN = 'Y';

    if (SQLCA.sqlcode != 0) {
        *tax = 0;
        return FAIL;
    }

    *tax = amt * tax_rate * (1 + surtax_rate);
    return SUCCESS;
}
""",
    "CM_TRANSFER_01.pc": """\
/* 계좌 간 이체 공통 처리 - 출금 입금 대체 자금이동 잔액 갱신 */
#include "proframe.h"

EXEC SQL INCLUDE SQLCA;

int CM_TRANSFER_01(const char *from_acct, const char *to_acct, double amt) {
    EXEC SQL BEGIN DECLARE SECTION;
    char    v_from[11];
    char    v_to[11];
    double  v_amt;
    double  v_avail;
    EXEC SQL END DECLARE SECTION;

    strcpy(v_from, from_acct);
    strcpy(v_to, to_acct);
    v_amt = amt;

    /* 출금 계좌 잔액 확인 */
    EXEC SQL SELECT AVAIL_AMT INTO :v_avail
        FROM TB_ACCT_BAL WHERE ACCT_NO = :v_from;

    if (v_avail < v_amt) {
        return FAIL;
    }

    /* 출금 */
    EXEC SQL UPDATE TB_ACCT_BAL
        SET CASH_BAL = CASH_BAL - :v_amt, AVAIL_AMT = AVAIL_AMT - :v_amt
        WHERE ACCT_NO = :v_from;

    /* 입금 */
    EXEC SQL UPDATE TB_ACCT_BAL
        SET CASH_BAL = CASH_BAL + :v_amt, AVAIL_AMT = AVAIL_AMT + :v_amt
        WHERE ACCT_NO = :v_to;

    CM_LOG_01("CM_TRANSFER_01", v_from, "이체출금");

    return SUCCESS;
}
""",

    # ========== Account (AC) ==========
    "AC_OPEN_01.pc": """\
/* 계좌 개설 처리 - 신규 계좌 등록, 계좌번호 채번, KYC 검증, 잔액 원장 초기화 */
#include "proframe.h"
#include "ac_open_str.h"

EXEC SQL INCLUDE SQLCA;

int AC_OPEN_01(ac_open_in_t *in, ac_open_out_t *out) {
    EXEC SQL BEGIN DECLARE SECTION;
    char    new_acct[11];
    char    ci_no[65];
    int     acct_cnt;
    EXEC SQL END DECLARE SECTION;

    strcpy(ci_no, in->ci_no);

    /* 동일 CI 기존 계좌 수 확인 */
    EXEC SQL SELECT COUNT(*) INTO :acct_cnt
        FROM TB_ACCT_MST
        WHERE CI_NO = :ci_no AND CLOSE_YN = 'N';

    if (acct_cnt >= 5) {
        strcpy(out->err_cd, "E201");
        strcpy(out->err_msg, "최대 계좌 수 초과");
        return FAIL;
    }

    /* 계좌번호 채번 */
    CM_ACCT_GEN(in->brnch_cd, new_acct);

    /* 계좌 마스터 등록 */
    EXEC SQL INSERT INTO TB_ACCT_MST
        (ACCT_NO, CUST_NO, CI_NO, ACCT_TP, OPEN_DT, CLOSE_YN)
        VALUES (:new_acct, :in->cust_no, :ci_no,
                :in->acct_type, TO_CHAR(SYSDATE,'YYYYMMDD'), 'N');

    /* 잔액 원장 초기화 */
    EXEC SQL INSERT INTO TB_ACCT_BAL (ACCT_NO, CASH_BAL, AVAIL_AMT)
        VALUES (:new_acct, 0, 0);

    /* 고객 정보 검증 */
    AC_KYC_CHK(in->cust_no, &out->kyc_result);

    CM_LOG_01("AC_OPEN_01", new_acct, "계좌개설");

    strcpy(out->acct_no, new_acct);
    return SUCCESS;
}
""",
    "AC_KYC_CHK.pc": """\
/* KYC 적합성 검증 처리 - 고객 본인확인 투자자 적합성 검증, AML 자금세탁 방지 확인 */
#include "proframe.h"

EXEC SQL INCLUDE SQLCA;

int AC_KYC_CHK(const char *cust_no, int *kyc_result) {
    EXEC SQL BEGIN DECLARE SECTION;
    char    v_cust[11];
    int     v_kyc_level;
    char    v_aml_yn[2];
    EXEC SQL END DECLARE SECTION;

    strcpy(v_cust, cust_no);

    EXEC SQL SELECT KYC_LEVEL, AML_YN INTO :v_kyc_level, :v_aml_yn
        FROM TB_CUST_MST
        WHERE CUST_NO = :v_cust;

    if (SQLCA.sqlcode != 0) {
        *kyc_result = -1;
        return FAIL;
    }

    /* AML 의심 고객 */
    if (v_aml_yn[0] == 'Y') {
        *kyc_result = 0;
        return FAIL;
    }

    *kyc_result = v_kyc_level;
    return SUCCESS;
}
""",
    "AC_CLOSE_01.pc": """\
/* 계좌 해지 처리 - 보유종목 확인, 잔여 현금 환불, 계좌 상태 폐쇄 변경 */
#include "proframe.h"
#include "ac_close_str.h"

EXEC SQL INCLUDE SQLCA;

int AC_CLOSE_01(ac_close_in_t *in, ac_close_out_t *out) {
    EXEC SQL BEGIN DECLARE SECTION;
    char    v_acct[11];
    double  v_cash;
    int     v_stk_cnt;
    EXEC SQL END DECLARE SECTION;

    strcpy(v_acct, in->acct_no);

    /* 권한 검증 */
    if (CM_AUTH_01(v_acct, in->auth_key, 3) != SUCCESS) {
        strcpy(out->err_cd, "E401");
        strcpy(out->err_msg, "권한 검증 실패");
        return FAIL;
    }

    /* 보유 종목 확인 — 잔고 있으면 해지 불가 */
    EXEC SQL SELECT COUNT(*) INTO :v_stk_cnt
        FROM TB_STK_BAL
        WHERE ACCT_NO = :v_acct AND HOLD_QTY > 0;

    if (v_stk_cnt > 0) {
        strcpy(out->err_cd, "E202");
        strcpy(out->err_msg, "보유종목 존재하여 해지 불가");
        return FAIL;
    }

    /* 잔여 현금 환불 */
    EXEC SQL SELECT CASH_BAL INTO :v_cash
        FROM TB_ACCT_BAL WHERE ACCT_NO = :v_acct;
    out->refund_amt = v_cash;

    /* 계좌 상태 변경 */
    EXEC SQL UPDATE TB_ACCT_MST
        SET CLOSE_YN = 'Y', CLOSE_DT = TO_CHAR(SYSDATE,'YYYYMMDD'),
            ACCT_ST = '09'
        WHERE ACCT_NO = :v_acct;

    CM_LOG_01("AC_CLOSE_01", v_acct, "계좌해지");

    return SUCCESS;
}
""",
    "AC_CHANGE_01.pc": """\
/* 계좌 정보 변경 처리 - 계좌 유형 지점코드 등 계좌 마스터 정보 수정 */
#include "proframe.h"

EXEC SQL INCLUDE SQLCA;

int AC_CHANGE_01(const char *acct_no, const char *field, const char *value) {
    EXEC SQL BEGIN DECLARE SECTION;
    char    v_acct[11];
    char    v_value[101];
    EXEC SQL END DECLARE SECTION;

    strcpy(v_acct, acct_no);
    strcpy(v_value, value);

    if (CM_AUTH_01(v_acct, "", 2) != SUCCESS) {
        return FAIL;
    }

    /* 변경 가능 필드만 허용 */
    if (strcmp(field, "ACCT_TP") == 0) {
        EXEC SQL UPDATE TB_ACCT_MST SET ACCT_TP = :v_value
            WHERE ACCT_NO = :v_acct;
    } else if (strcmp(field, "BRNCH_CD") == 0) {
        EXEC SQL UPDATE TB_ACCT_MST SET BRNCH_CD = :v_value
            WHERE ACCT_NO = :v_acct;
    } else {
        return FAIL;
    }

    CM_LOG_01("AC_CHANGE_01", v_acct, "계좌정보변경");
    return SUCCESS;
}
""",
    "AC_FREEZE_01.pc": """\
/* 계좌 동결 처리 - 사고 신고 법적 요청 등에 의한 계좌 거래 정지 */
#include "proframe.h"

EXEC SQL INCLUDE SQLCA;

int AC_FREEZE_01(const char *acct_no, const char *freeze_rsn) {
    EXEC SQL BEGIN DECLARE SECTION;
    char    v_acct[11];
    char    v_rsn[101];
    EXEC SQL END DECLARE SECTION;

    strcpy(v_acct, acct_no);
    strcpy(v_rsn, freeze_rsn);

    if (CM_AUTH_01(v_acct, "", 5) != SUCCESS) {
        return FAIL;
    }

    EXEC SQL UPDATE TB_ACCT_MST
        SET FREEZE_YN = 'Y', FREEZE_RSN = :v_rsn,
            UPD_DT = TO_CHAR(SYSDATE,'YYYYMMDDHH24MISS')
        WHERE ACCT_NO = :v_acct;

    CM_LOG_01("AC_FREEZE_01", v_acct, "계좌동결");
    return SUCCESS;
}
""",
    "AC_UNFREEZE_01.pc": """\
/* 계좌 동결 해제 처리 - 동결 사유 해소 후 거래 정지 해제 */
#include "proframe.h"

EXEC SQL INCLUDE SQLCA;

int AC_UNFREEZE_01(const char *acct_no, const char *auth_key) {
    EXEC SQL BEGIN DECLARE SECTION;
    char    v_acct[11];
    EXEC SQL END DECLARE SECTION;

    strcpy(v_acct, acct_no);

    if (CM_AUTH_01(v_acct, auth_key, 5) != SUCCESS) {
        return FAIL;
    }

    EXEC SQL UPDATE TB_ACCT_MST
        SET FREEZE_YN = 'N', FREEZE_RSN = NULL,
            UPD_DT = TO_CHAR(SYSDATE,'YYYYMMDDHH24MISS')
        WHERE ACCT_NO = :v_acct;

    CM_LOG_01("AC_UNFREEZE_01", v_acct, "동결해제");
    return SUCCESS;
}
""",
    "AC_GRADE_01.pc": """\
/* 고객 등급 산정 배치 처리 - 총자산 거래건수 기준 VIP 우수 일반 등급 재산정 */
#include "proframe.h"
#include "ac_grade_str.h"

EXEC SQL INCLUDE SQLCA;

int AC_GRADE_01(ac_grade_in_t *in, ac_grade_out_t *out) {
    EXEC SQL BEGIN DECLARE SECTION;
    char    v_cust[11];
    char    v_base_dt[9];
    double  v_total_asset;
    int     v_tx_count;
    char    v_prev_grade[3];
    EXEC SQL END DECLARE SECTION;

    strcpy(v_cust, in->cust_no);
    strcpy(v_base_dt, in->base_dt);

    /* 기존 등급 */
    EXEC SQL SELECT GRADE_CD INTO :v_prev_grade
        FROM TB_CUST_MST WHERE CUST_NO = :v_cust;
    strcpy(out->prev_grade, v_prev_grade);

    /* 총 자산 집계 */
    EXEC SQL SELECT NVL(SUM(EVAL_AMT),0) INTO :v_total_asset
        FROM (
            SELECT EVAL_AMT FROM TB_STK_BAL WHERE ACCT_NO IN
                (SELECT ACCT_NO FROM TB_ACCT_MST WHERE CUST_NO = :v_cust)
            UNION ALL
            SELECT EVAL_AMT FROM TB_BND_BAL WHERE ACCT_NO IN
                (SELECT ACCT_NO FROM TB_ACCT_MST WHERE CUST_NO = :v_cust)
            UNION ALL
            SELECT EVAL_AMT FROM TB_FND_BAL WHERE ACCT_NO IN
                (SELECT ACCT_NO FROM TB_ACCT_MST WHERE CUST_NO = :v_cust)
        );
    out->total_asset = v_total_asset;

    /* 거래 건수 */
    EXEC SQL SELECT COUNT(*) INTO :v_tx_count
        FROM TB_TX_HIST
        WHERE ACCT_NO IN (SELECT ACCT_NO FROM TB_ACCT_MST WHERE CUST_NO = :v_cust)
        AND TX_DT >= TO_CHAR(ADD_MONTHS(TO_DATE(:v_base_dt,'YYYYMMDD'),-3),'YYYYMMDD');
    out->tx_count = v_tx_count;

    /* 등급 산정: VIP(01) > 우수(02) > 일반(03) > 관리(04) > 신규(05) */
    if (v_total_asset >= 1000000000 && v_tx_count >= 50)
        strcpy(out->new_grade, "01");
    else if (v_total_asset >= 300000000 && v_tx_count >= 20)
        strcpy(out->new_grade, "02");
    else if (v_total_asset >= 50000000)
        strcpy(out->new_grade, "03");
    else if (v_tx_count < 3)
        strcpy(out->new_grade, "05");
    else
        strcpy(out->new_grade, "04");

    /* 등급 갱신 */
    EXEC SQL UPDATE TB_CUST_MST SET GRADE_CD = :out->new_grade
        WHERE CUST_NO = :v_cust;

    CM_LOG_01("AC_GRADE_01", v_cust, "등급산정");
    return SUCCESS;
}
""",
    "AC_DORMANT_01.pc": """\
/* 휴면계좌 전환 배치 처리 - 1년 이상 미거래 계좌 휴면 전환 및 고객 알림 */
#include "proframe.h"

EXEC SQL INCLUDE SQLCA;

int AC_DORMANT_01(const char *base_dt) {
    EXEC SQL BEGIN DECLARE SECTION;
    char    v_dt[9];
    char    v_cutoff[9];
    int     v_cnt;
    EXEC SQL END DECLARE SECTION;

    strcpy(v_dt, base_dt);

    /* 1년 이상 거래 없는 계좌 추출 */
    EXEC SQL SELECT TO_CHAR(ADD_MONTHS(TO_DATE(:v_dt,'YYYYMMDD'),-12),'YYYYMMDD')
        INTO :v_cutoff FROM DUAL;

    EXEC SQL UPDATE TB_ACCT_MST
        SET DORMANT_YN = 'Y', UPD_DT = TO_CHAR(SYSDATE,'YYYYMMDDHH24MISS')
        WHERE CLOSE_YN = 'N' AND DORMANT_YN = 'N'
        AND ACCT_NO NOT IN (
            SELECT DISTINCT ACCT_NO FROM TB_TX_HIST
            WHERE TX_DT >= :v_cutoff
        );

    v_cnt = SQLCA.sqlerrd[2];

    /* 대상 고객 알림 */
    CM_NOTIFY_01("BATCH", "DORMANT", "휴면계좌 전환 안내");

    CM_LOG_01("AC_DORMANT_01", "BATCH", "휴면전환");
    return v_cnt;
}
""",
    "AC_HIST_01.pc": """\
/* 계좌 거래 이력 조회 처리 - 기간별 거래내역 조회 */
#include "proframe.h"

EXEC SQL INCLUDE SQLCA;

int AC_HIST_01(const char *acct_no, const char *from_dt, const char *to_dt,
               void *result_set, int *count) {
    EXEC SQL BEGIN DECLARE SECTION;
    char    v_acct[11];
    char    v_from[9];
    char    v_to[9];
    int     v_cnt;
    EXEC SQL END DECLARE SECTION;

    strcpy(v_acct, acct_no);
    strcpy(v_from, from_dt);
    strcpy(v_to, to_dt);

    EXEC SQL SELECT COUNT(*) INTO :v_cnt
        FROM TB_TX_HIST
        WHERE ACCT_NO = :v_acct
        AND TX_DT BETWEEN :v_from AND :v_to;

    *count = v_cnt;
    return SUCCESS;
}
""",
    "AC_MERGE_01.pc": """\
/* 계좌 통합 처리 - 복수 계좌 잔고 이전, 현금 이체, 원계좌 해지 */
#include "proframe.h"

EXEC SQL INCLUDE SQLCA;

int AC_MERGE_01(const char *from_acct, const char *to_acct, const char *auth_key) {
    EXEC SQL BEGIN DECLARE SECTION;
    char    v_from[11];
    char    v_to[11];
    double  v_cash;
    EXEC SQL END DECLARE SECTION;

    strcpy(v_from, from_acct);
    strcpy(v_to, to_acct);

    if (CM_AUTH_01(v_from, auth_key, 5) != SUCCESS) {
        return FAIL;
    }

    /* 주식 잔고 이전 */
    EXEC SQL UPDATE TB_STK_BAL SET ACCT_NO = :v_to
        WHERE ACCT_NO = :v_from;

    /* 현금 이체 */
    EXEC SQL SELECT CASH_BAL INTO :v_cash
        FROM TB_ACCT_BAL WHERE ACCT_NO = :v_from;

    if (v_cash > 0) {
        CM_TRANSFER_01(v_from, v_to, v_cash);
    }

    /* 원계좌 해지 */
    EXEC SQL UPDATE TB_ACCT_MST
        SET CLOSE_YN = 'Y', ACCT_ST = '09',
            CLOSE_DT = TO_CHAR(SYSDATE,'YYYYMMDD')
        WHERE ACCT_NO = :v_from;

    CM_LOG_01("AC_MERGE_01", v_from, "계좌통합");
    return SUCCESS;
}
""",

    # ========== Stock (ST) ==========
    "ST_BUY_01.pc": """\
/* 주식 매수 주문 처리 - 호가 검증, 증거금 계산, 주문 원장 등록, 거래소 전송 */
#include "proframe.h"
#include "st_buy_str.h"

EXEC SQL INCLUDE SQLCA;

int ST_BUY_01(st_buy_in_t *in, st_buy_out_t *out) {
    EXEC SQL BEGIN DECLARE SECTION;
    double  avail_amt;
    double  order_amt;
    char    acct_no[11];
    char    stk_cd[7];
    EXEC SQL END DECLARE SECTION;

    strcpy(acct_no, in->acct_no);
    strcpy(stk_cd, in->stk_cd);
    order_amt = in->price * in->qty;

    /* 호가 단위 검증 */
    if (ST_LOT_01(stk_cd, in->price) != SUCCESS) {
        strcpy(out->err_cd, "E100");
        strcpy(out->err_msg, "호가단위 오류");
        return FAIL;
    }

    /* 주문가능금액 확인 */
    EXEC SQL SELECT AVAIL_AMT INTO :avail_amt
        FROM TB_ACCT_BAL
        WHERE ACCT_NO = :acct_no;

    /* 증거금 계산 */
    ST_MARGIN_01(stk_cd, order_amt, &out->margin_amt);

    if (avail_amt < out->margin_amt) {
        strcpy(out->err_cd, "E101");
        strcpy(out->err_msg, "주문가능금액 부족");
        return FAIL;
    }

    /* 주문 원장 등록 */
    EXEC SQL INSERT INTO TB_ORD_MST
        (ORD_NO, ACCT_NO, STK_CD, ORD_TP, ORD_SIDE, PRICE, QTY, ORD_DT, ORD_ST)
        VALUES (SQ_ORD_NO.NEXTVAL, :acct_no, :stk_cd,
                :in->ord_type, 'BUY', :in->price, :in->qty,
                TO_CHAR(SYSDATE,'YYYYMMDD'), '01');

    /* 거래소 전송 */
    IF_KRX_01(NULL, NULL);

    CM_LOG_01("ST_BUY_01", acct_no, "매수주문");
    out->order_amt = order_amt;
    return SUCCESS;
}
""",
    "ST_SELL_01.pc": """\
/* 주식 매도 주문 처리 - 매도가능수량 확인, 선차감, 주문 등록, 거래소 전송 */
#include "proframe.h"
#include "st_sell_str.h"

EXEC SQL INCLUDE SQLCA;

int ST_SELL_01(st_sell_in_t *in, st_sell_out_t *out) {
    EXEC SQL BEGIN DECLARE SECTION;
    char    acct_no[11];
    char    stk_cd[7];
    long    sell_avail;
    EXEC SQL END DECLARE SECTION;

    strcpy(acct_no, in->acct_no);
    strcpy(stk_cd, in->stk_cd);

    /* 매도가능수량 확인 */
    EXEC SQL SELECT SELL_AVAIL INTO :sell_avail
        FROM TB_STK_BAL
        WHERE ACCT_NO = :acct_no AND STK_CD = :stk_cd;

    if (SQLCA.sqlcode != 0 || sell_avail < in->qty) {
        strcpy(out->err_cd, "E301");
        strcpy(out->err_msg, "매도가능수량 부족");
        return FAIL;
    }

    /* 호가 단위 검증 */
    ST_LOT_01(stk_cd, in->price);

    /* 매도가능수량 차감 (선차감) */
    EXEC SQL UPDATE TB_STK_BAL
        SET SELL_AVAIL = SELL_AVAIL - :in->qty
        WHERE ACCT_NO = :acct_no AND STK_CD = :stk_cd;

    /* 주문 원장 등록 */
    EXEC SQL INSERT INTO TB_ORD_MST
        (ORD_NO, ACCT_NO, STK_CD, ORD_TP, ORD_SIDE, PRICE, QTY, ORD_DT, ORD_ST)
        VALUES (SQ_ORD_NO.NEXTVAL, :acct_no, :stk_cd,
                :in->ord_type, 'SELL', :in->price, :in->qty,
                TO_CHAR(SYSDATE,'YYYYMMDD'), '01');

    /* 거래소 전송 */
    IF_KRX_01(NULL, NULL);

    /* 예상 수익/세금 */
    out->est_proceeds = in->price * in->qty;
    CM_TAX_01(out->est_proceeds, &out->est_tax);

    CM_LOG_01("ST_SELL_01", acct_no, "매도주문");
    return SUCCESS;
}
""",
    "ST_CANCEL_01.pc": """\
/* 주문 취소 처리 - 미체결 주문 취소, 매도가능수량 복원, 거래소 취소 전송 */
#include "proframe.h"

EXEC SQL INCLUDE SQLCA;

int ST_CANCEL_01(long ord_no, const char *acct_no) {
    EXEC SQL BEGIN DECLARE SECTION;
    long    v_ord_no;
    char    v_acct[11];
    char    v_ord_st[3];
    char    v_side[5];
    long    v_qty;
    long    v_exec_qty;
    EXEC SQL END DECLARE SECTION;

    v_ord_no = ord_no;
    strcpy(v_acct, acct_no);

    /* 주문 상태 확인 */
    EXEC SQL SELECT ORD_ST, ORD_SIDE, QTY, EXEC_QTY
        INTO :v_ord_st, :v_side, :v_qty, :v_exec_qty
        FROM TB_ORD_MST
        WHERE ORD_NO = :v_ord_no AND ACCT_NO = :v_acct;

    if (strcmp(v_ord_st, "01") != 0) {
        return FAIL;  /* 접수 상태가 아님 */
    }

    /* 미체결 수량만 취소 */
    EXEC SQL UPDATE TB_ORD_MST
        SET ORD_ST = '09'
        WHERE ORD_NO = :v_ord_no;

    /* 매도 취소시 매도가능수량 복원 */
    if (strcmp(v_side, "SELL") == 0) {
        EXEC SQL UPDATE TB_STK_BAL
            SET SELL_AVAIL = SELL_AVAIL + (:v_qty - :v_exec_qty)
            WHERE ACCT_NO = :v_acct;
    }

    IF_KRX_01(NULL, NULL);
    CM_LOG_01("ST_CANCEL_01", v_acct, "주문취소");
    return SUCCESS;
}
""",
    "ST_MODIFY_01.pc": """\
/* 주문 정정 처리 - 가격 수량 변경, 증거금 재계산, 원주문 취소 후 신규 등록 */
#include "proframe.h"

EXEC SQL INCLUDE SQLCA;

int ST_MODIFY_01(long orig_ord_no, double new_price, long new_qty,
                 const char *acct_no) {
    EXEC SQL BEGIN DECLARE SECTION;
    long    v_orig;
    char    v_acct[11];
    char    v_stk_cd[7];
    char    v_ord_st[3];
    double  v_price;
    EXEC SQL END DECLARE SECTION;

    v_orig = orig_ord_no;
    strcpy(v_acct, acct_no);
    v_price = new_price;

    /* 원주문 확인 */
    EXEC SQL SELECT ORD_ST, STK_CD INTO :v_ord_st, :v_stk_cd
        FROM TB_ORD_MST
        WHERE ORD_NO = :v_orig AND ACCT_NO = :v_acct;

    if (strcmp(v_ord_st, "01") != 0) {
        return FAIL;
    }

    /* 증거금 재계산 */
    double margin;
    ST_MARGIN_01(v_stk_cd, new_price * new_qty, &margin);

    /* 원주문 취소 + 신규 등록 */
    EXEC SQL UPDATE TB_ORD_MST SET ORD_ST = '08' WHERE ORD_NO = :v_orig;

    EXEC SQL INSERT INTO TB_ORD_MST
        (ORD_NO, ACCT_NO, STK_CD, ORD_TP, PRICE, QTY, ORD_DT, ORD_ST, ORIG_ORD_NO)
        VALUES (SQ_ORD_NO.NEXTVAL, :v_acct, :v_stk_cd,
                'LIMIT', :v_price, :new_qty,
                TO_CHAR(SYSDATE,'YYYYMMDD'), '01', :v_orig);

    IF_KRX_01(NULL, NULL);
    CM_LOG_01("ST_MODIFY_01", v_acct, "주문정정");
    return SUCCESS;
}
""",
    "ST_MARGIN_01.pc": """\
/* 증거금 계산 처리 - 종목별 증거금율 조회 및 위탁 증거금 금액 산출 */
#include "proframe.h"

EXEC SQL INCLUDE SQLCA;

int ST_MARGIN_01(const char *stk_cd, double order_amt, double *margin_amt) {
    EXEC SQL BEGIN DECLARE SECTION;
    char    v_stk[7];
    double  v_margin_rate;
    EXEC SQL END DECLARE SECTION;

    strcpy(v_stk, stk_cd);

    EXEC SQL SELECT MARGIN_RATE INTO :v_margin_rate
        FROM TB_MARGIN_MST
        WHERE STK_CD = :v_stk AND USE_YN = 'Y';

    if (SQLCA.sqlcode != 0) {
        v_margin_rate = 100.0;  /* 기본 100% */
    }

    *margin_amt = order_amt * (v_margin_rate / 100.0);
    return SUCCESS;
}
""",
    "ST_SETL_01.pc": """\
/* T+2 결제 처리 - 체결 건 대금 결제, 매수 현금차감 잔고증가, 매도 현금증가 잔고차감 */
#include "proframe.h"
#include "st_setl_str.h"

EXEC SQL INCLUDE SQLCA;

int ST_SETL_01(st_setl_in_t *in, st_setl_out_t *out) {
    EXEC SQL BEGIN DECLARE SECTION;
    char    v_setl_dt[9];
    char    v_acct[11];
    char    v_stk_cd[7];
    char    v_side[5];
    double  v_exec_amt;
    long    v_exec_qty;
    EXEC SQL END DECLARE SECTION;

    strcpy(v_setl_dt, in->setl_dt);

    /* 당일 결제 대상 체결 조회 */
    EXEC SQL DECLARE c_setl CURSOR FOR
        SELECT ACCT_NO, STK_CD, EXEC_SIDE, EXEC_AMT, EXEC_QTY
        FROM TB_EXEC_HST
        WHERE SETL_DT = :v_setl_dt AND SETL_ST = '00';

    EXEC SQL OPEN c_setl;

    while (1) {
        EXEC SQL FETCH c_setl
            INTO :v_acct, :v_stk_cd, :v_side, :v_exec_amt, :v_exec_qty;
        if (SQLCA.sqlcode != 0) break;

        if (strcmp(v_side, "BUY") == 0) {
            /* 매수 결제: 현금 차감 + 잔고 증가 */
            EXEC SQL UPDATE TB_ACCT_BAL
                SET CASH_BAL = CASH_BAL - :v_exec_amt
                WHERE ACCT_NO = :v_acct;
            EXEC SQL UPDATE TB_STK_BAL
                SET HOLD_QTY = HOLD_QTY + :v_exec_qty,
                    SELL_AVAIL = SELL_AVAIL + :v_exec_qty
                WHERE ACCT_NO = :v_acct AND STK_CD = :v_stk_cd;
        } else {
            /* 매도 결제: 현금 증가 + 잔고 차감 */
            EXEC SQL UPDATE TB_ACCT_BAL
                SET CASH_BAL = CASH_BAL + :v_exec_amt
                WHERE ACCT_NO = :v_acct;
            EXEC SQL UPDATE TB_STK_BAL
                SET HOLD_QTY = HOLD_QTY - :v_exec_qty
                WHERE ACCT_NO = :v_acct AND STK_CD = :v_stk_cd;
        }

        /* 결제 완료 처리 */
        EXEC SQL UPDATE TB_EXEC_HST SET SETL_ST = '01'
            WHERE EXEC_NO = :in->exec_no;

        /* 결제 원장 등록 */
        EXEC SQL INSERT INTO TB_SETL_MST
            (SETL_NO, EXEC_NO, ACCT_NO, SETL_TP, SETL_DT, SETL_AMT, SETL_ST)
            VALUES (SQ_SETL.NEXTVAL, :in->exec_no, :v_acct,
                    :v_side, :v_setl_dt, :v_exec_amt, '01');

        /* KSD 통보 */
        IF_KSD_01(NULL, NULL);
    }

    EXEC SQL CLOSE c_setl;

    CM_LOG_01("ST_SETL_01", "BATCH", "T+2결제");
    return SUCCESS;
}
""",
    "ST_PRICE_01.pc": """\
/* 시세 조회 처리 - 종목별 현재가 전일종가 시세 정보 조회 */
#include "proframe.h"

EXEC SQL INCLUDE SQLCA;

int ST_PRICE_01(const char *stk_cd, double *cur_price, double *prev_close) {
    EXEC SQL BEGIN DECLARE SECTION;
    char    v_stk[7];
    double  v_cur;
    double  v_prev;
    EXEC SQL END DECLARE SECTION;

    strcpy(v_stk, stk_cd);

    EXEC SQL SELECT CUR_PRICE, PREV_CLOSE INTO :v_cur, :v_prev
        FROM TB_STK_PRICE
        WHERE STK_CD = :v_stk;

    if (SQLCA.sqlcode != 0) {
        *cur_price = 0;
        *prev_close = 0;
        return FAIL;
    }

    *cur_price = v_cur;
    *prev_close = v_prev;
    return SUCCESS;
}
""",
    "ST_LOT_01.pc": """\
/* 호가 단위 검증 처리 - 가격대별 호가 단위 적합성 검증 */
#include "proframe.h"

int ST_LOT_01(const char *stk_cd, double price) {
    int lot_size;

    /* 가격대별 호가 단위 */
    if (price < 1000)        lot_size = 1;
    else if (price < 5000)   lot_size = 5;
    else if (price < 10000)  lot_size = 10;
    else if (price < 50000)  lot_size = 50;
    else if (price < 100000) lot_size = 100;
    else if (price < 500000) lot_size = 500;
    else                     lot_size = 1000;

    if ((int)price % lot_size != 0) {
        return FAIL;
    }
    return SUCCESS;
}
""",
    "ST_CREDIT_01.pc": """\
/* 신용매수 주문 처리 - 신용 대출 실행 후 주식 매수 주문, 신용한도 체크 */
#include "proframe.h"
#include "st_credit_str.h"

EXEC SQL INCLUDE SQLCA;

int ST_CREDIT_01(st_credit_in_t *in, st_credit_out_t *out) {
    EXEC SQL BEGIN DECLARE SECTION;
    char    v_acct[11];
    EXEC SQL END DECLARE SECTION;

    strcpy(v_acct, in->acct_no);

    /* 신용한도 체크 */
    double order_amt = in->price * in->qty;
    if (CM_LIMIT_CHK("CREDIT", v_acct, order_amt) != SUCCESS) {
        strcpy(out->err_cd, "E501");
        strcpy(out->err_msg, "신용한도 초과");
        return FAIL;
    }

    /* 신용 대출 실행 */
    ln_credit_in_t ln_in;
    ln_credit_out_t ln_out;
    strcpy(ln_in.acct_no, v_acct);
    strcpy(ln_in.loan_tp, "CRED");
    ln_in.loan_amt = order_amt * 0.6;  /* 자기자금 40% */
    ln_in.loan_days = in->credit_days;
    LN_CREDIT_01(&ln_in, &ln_out);
    out->loan_no = ln_out.loan_no;
    out->loan_amt = ln_out.approved_amt;
    out->int_rate = ln_out.int_rate;

    /* 매수 주문 실행 */
    st_buy_in_t buy_in;
    st_buy_out_t buy_out;
    strcpy(buy_in.acct_no, v_acct);
    strcpy(buy_in.stk_cd, in->stk_cd);
    buy_in.price = in->price;
    buy_in.qty = in->qty;
    strcpy(buy_in.credit_tp, "01");
    ST_BUY_01(&buy_in, &buy_out);

    out->ord_no = buy_out.ord_no;
    out->margin_amt = buy_out.margin_amt;
    return SUCCESS;
}
""",
    "ST_SHORT_01.pc": """\
/* 공매도 주문 처리 - 무보유 매도, 공매도 한도 및 리스크 익스포저 확인 */
#include "proframe.h"

EXEC SQL INCLUDE SQLCA;

int ST_SHORT_01(const char *acct_no, const char *stk_cd,
                double price, long qty) {
    EXEC SQL BEGIN DECLARE SECTION;
    char    v_acct[11];
    char    v_stk[7];
    EXEC SQL END DECLARE SECTION;

    strcpy(v_acct, acct_no);
    strcpy(v_stk, stk_cd);

    double order_amt = price * qty;

    /* 공매도 한도 체크 */
    if (CM_LIMIT_CHK("SHORT", v_stk, order_amt) != SUCCESS) {
        return FAIL;
    }

    /* 익스포저 확인 */
    rm_exposure_in_t rm_in;
    rm_exposure_out_t rm_out;
    strcpy(rm_in.acct_no, v_acct);
    RM_EXPOSURE_01(&rm_in, &rm_out);

    if (rm_out.usage_rate > 90.0) {
        return FAIL;  /* 리스크 한도 초과 */
    }

    /* 매도 주문으로 처리 */
    st_sell_in_t sell_in;
    st_sell_out_t sell_out;
    strcpy(sell_in.acct_no, v_acct);
    strcpy(sell_in.stk_cd, v_stk);
    sell_in.price = price;
    sell_in.qty = qty;
    ST_SELL_01(&sell_in, &sell_out);

    CM_LOG_01("ST_SHORT_01", v_acct, "공매도");
    return SUCCESS;
}
""",
    "ST_AFTER_01.pc": """\
/* 시간외 거래 처리 - 장 마감 후 종가 기준 시간외 매수 매도 주문 */
#include "proframe.h"
#include "st_buy_str.h"

EXEC SQL INCLUDE SQLCA;

int ST_AFTER_01(const char *acct_no, const char *stk_cd,
                const char *side, long qty) {
    EXEC SQL BEGIN DECLARE SECTION;
    char    v_stk[7];
    double  v_close_price;
    EXEC SQL END DECLARE SECTION;

    strcpy(v_stk, stk_cd);

    /* 종가 조회 (시간외는 종가 기준) */
    EXEC SQL SELECT PREV_CLOSE INTO :v_close_price
        FROM TB_STK_PRICE WHERE STK_CD = :v_stk;

    if (strcmp(side, "BUY") == 0) {
        st_buy_in_t in;
        st_buy_out_t out;
        strcpy(in.acct_no, acct_no);
        strcpy(in.stk_cd, stk_cd);
        in.price = v_close_price;
        in.qty = qty;
        strcpy(in.ord_type, "02");  /* 시간외 */
        return ST_BUY_01(&in, &out);
    } else {
        st_sell_in_t in;
        st_sell_out_t out;
        strcpy(in.acct_no, acct_no);
        strcpy(in.stk_cd, stk_cd);
        in.price = v_close_price;
        in.qty = qty;
        return ST_SELL_01(&in, &out);
    }
}
""",
    "ST_BLOCK_01.pc": """\
/* 대량매매 블록딜 처리 - 10억 이상 대량 주문, 별도 권한 및 한도 확인 */
#include "proframe.h"
#include "st_buy_str.h"

EXEC SQL INCLUDE SQLCA;

int ST_BLOCK_01(const char *acct_no, const char *stk_cd,
                const char *side, double price, long qty) {
    EXEC SQL BEGIN DECLARE SECTION;
    char    v_acct[11];
    EXEC SQL END DECLARE SECTION;

    strcpy(v_acct, acct_no);
    double order_amt = price * qty;

    /* 대량매매 권한 (레벨5) */
    if (CM_AUTH_01(v_acct, "", 5) != SUCCESS) {
        return FAIL;
    }

    /* 대량매매 한도 체크 (10억 이상) */
    if (order_amt < 1000000000) {
        return FAIL;  /* 대량매매 최소금액 미달 */
    }
    if (CM_LIMIT_CHK("BLOCK", v_acct, order_amt) != SUCCESS) {
        return FAIL;
    }

    /* 매수/매도 주문 */
    if (strcmp(side, "BUY") == 0) {
        st_buy_in_t in;
        st_buy_out_t out;
        strcpy(in.acct_no, acct_no);
        strcpy(in.stk_cd, stk_cd);
        in.price = price;
        in.qty = qty;
        ST_BUY_01(&in, &out);
    }

    CM_LOG_01("ST_BLOCK_01", v_acct, "대량매매");
    return SUCCESS;
}
""",

    # ========== Bond (BN) ==========
    "BN_BUY_01.pc": """\
/* 채권 매수 처리 - 채권 발행정보 조회, 경과이자 계산, 매수대금 산출, 잔고 등록 */
#include "proframe.h"
#include "bn_buy_str.h"

EXEC SQL INCLUDE SQLCA;

int BN_BUY_01(bn_buy_in_t *in, bn_buy_out_t *out) {
    EXEC SQL BEGIN DECLARE SECTION;
    char    v_acct[11];
    char    v_bnd[13];
    double  v_coupon_rate;
    char    v_issue_dt[9];
    double  v_avail;
    EXEC SQL END DECLARE SECTION;

    strcpy(v_acct, in->acct_no);
    strcpy(v_bnd, in->bnd_cd);

    /* 채권 발행 정보 조회 */
    EXEC SQL SELECT COUPON_RATE, ISSUE_DT INTO :v_coupon_rate, :v_issue_dt
        FROM TB_BND_ISSUE
        WHERE BND_CD = :v_bnd AND USE_YN = 'Y';

    if (SQLCA.sqlcode != 0) {
        strcpy(out->err_cd, "E601");
        strcpy(out->err_msg, "채권 정보 없음");
        return FAIL;
    }

    /* 경과이자 계산 */
    bn_coupon_in_t coupon_in;
    bn_coupon_out_t coupon_out;
    strcpy(coupon_in.bnd_cd, v_bnd);
    coupon_in.face_amt = in->face_amt;
    BN_ACCRUED_01(&coupon_in, &coupon_out);
    out->accrued_int = coupon_out.accrued_int;

    /* 매수금액 = 액면 × 매수단가 + 경과이자 */
    out->buy_amt = in->face_amt * (in->price / 100.0);
    out->total_amt = out->buy_amt + out->accrued_int;

    /* 잔액 확인 */
    EXEC SQL SELECT AVAIL_AMT INTO :v_avail
        FROM TB_ACCT_BAL WHERE ACCT_NO = :v_acct;

    if (v_avail < out->total_amt) {
        strcpy(out->err_cd, "E602");
        strcpy(out->err_msg, "주문가능금액 부족");
        return FAIL;
    }

    /* 채권 잔고 등록 */
    EXEC SQL INSERT INTO TB_BND_BAL
        (ACCT_NO, BND_CD, HOLD_QTY, HOLD_AMT, BUY_PRICE, BUY_DT)
        VALUES (:v_acct, :v_bnd, :in->face_amt, :out->total_amt,
                :in->price, TO_CHAR(SYSDATE,'YYYYMMDD'));

    /* 대금 차감 */
    EXEC SQL UPDATE TB_ACCT_BAL
        SET CASH_BAL = CASH_BAL - :out->total_amt,
            AVAIL_AMT = AVAIL_AMT - :out->total_amt
        WHERE ACCT_NO = :v_acct;

    CM_LOG_01("BN_BUY_01", v_acct, "채권매수");
    return SUCCESS;
}
""",
    "BN_SELL_01.pc": """\
/* 채권 매도 처리 - 보유 채권 매도, 경과이자 정산, 양도차익 세금 계산 */
#include "proframe.h"

EXEC SQL INCLUDE SQLCA;

int BN_SELL_01(const char *acct_no, const char *bnd_cd,
               double face_amt, double sell_price) {
    EXEC SQL BEGIN DECLARE SECTION;
    char    v_acct[11];
    char    v_bnd[13];
    double  v_hold_qty;
    double  v_buy_price;
    EXEC SQL END DECLARE SECTION;

    strcpy(v_acct, acct_no);
    strcpy(v_bnd, bnd_cd);

    /* 보유 확인 */
    EXEC SQL SELECT HOLD_QTY, BUY_PRICE INTO :v_hold_qty, :v_buy_price
        FROM TB_BND_BAL
        WHERE ACCT_NO = :v_acct AND BND_CD = :v_bnd;

    if (v_hold_qty < face_amt) {
        return FAIL;
    }

    /* 경과이자 계산 */
    bn_coupon_in_t coupon_in;
    bn_coupon_out_t coupon_out;
    strcpy(coupon_in.bnd_cd, v_bnd);
    coupon_in.face_amt = face_amt;
    BN_ACCRUED_01(&coupon_in, &coupon_out);

    double sell_amt = face_amt * (sell_price / 100.0) + coupon_out.accrued_int;
    double profit = sell_amt - (face_amt * (v_buy_price / 100.0));

    /* 양도세 계산 */
    double tax = 0;
    if (profit > 0) {
        CM_TAX_01(profit, &tax);
    }

    /* 잔고 차감 */
    EXEC SQL UPDATE TB_BND_BAL
        SET HOLD_QTY = HOLD_QTY - :face_amt
        WHERE ACCT_NO = :v_acct AND BND_CD = :v_bnd;

    /* 대금 입금 */
    EXEC SQL UPDATE TB_ACCT_BAL
        SET CASH_BAL = CASH_BAL + :sell_amt - :tax
        WHERE ACCT_NO = :v_acct;

    CM_LOG_01("BN_SELL_01", v_acct, "채권매도");
    return SUCCESS;
}
""",
    "BN_INT_05.pc": """\
/* 채권 이자 지급 처리 - 쿠폰 이표 이자 계산, 이자소득세 원천징수, 이자금 입금 */
#include "proframe.h"
#include "bn_int_str.h"

EXEC SQL INCLUDE SQLCA;

int BN_INT_05(bn_int_in_t *in, bn_int_out_t *out) {
    EXEC SQL BEGIN DECLARE SECTION;
    char    v_acct[11];
    char    v_bnd[13];
    double  v_coupon_rate;
    int     v_freq;
    double  v_hold_qty;
    EXEC SQL END DECLARE SECTION;

    strcpy(v_acct, in->acct_no);
    strcpy(v_bnd, in->bnd_cd);

    /* 쿠폰율 조회 */
    EXEC SQL SELECT COUPON_RATE, COUPON_FREQ INTO :v_coupon_rate, :v_freq
        FROM TB_BND_ISSUE
        WHERE BND_CD = :v_bnd;

    /* 보유수량 */
    EXEC SQL SELECT HOLD_QTY INTO :v_hold_qty
        FROM TB_BND_BAL
        WHERE ACCT_NO = :v_acct AND BND_CD = :v_bnd;

    /* 이자 계산: 액면 × 쿠폰율 / 지급횟수 */
    out->gross_int = v_hold_qty * (v_coupon_rate / v_freq);

    /* 이자소득세 */
    CM_TAX_01(out->gross_int, &out->tax_amt);
    out->net_int = out->gross_int - out->tax_amt;

    /* 이자 입금 */
    CM_TRANSFER_01("BOND_INT_ACCT", v_acct, out->net_int);

    CM_LOG_01("BN_INT_05", v_acct, "채권이자");
    return SUCCESS;
}
""",
    "BN_MATURE_01.pc": """\
/* 채권 만기 상환 처리 - 액면 상환금 및 마지막 이표 지급, 세금 계산, 잔고 삭제 */
#include "proframe.h"
#include "bn_mature_str.h"

EXEC SQL INCLUDE SQLCA;

int BN_MATURE_01(bn_mature_in_t *in, bn_mature_out_t *out) {
    EXEC SQL BEGIN DECLARE SECTION;
    char    v_acct[11];
    char    v_bnd[13];
    double  v_hold_qty;
    double  v_coupon_rate;
    int     v_freq;
    EXEC SQL END DECLARE SECTION;

    strcpy(v_acct, in->acct_no);
    strcpy(v_bnd, in->bnd_cd);

    EXEC SQL SELECT HOLD_QTY INTO :v_hold_qty
        FROM TB_BND_BAL
        WHERE ACCT_NO = :v_acct AND BND_CD = :v_bnd;

    EXEC SQL SELECT COUPON_RATE, COUPON_FREQ INTO :v_coupon_rate, :v_freq
        FROM TB_BND_ISSUE WHERE BND_CD = :v_bnd;

    /* 액면 상환금 */
    out->face_amt = v_hold_qty;

    /* 마지막 이표 */
    out->last_coupon = v_hold_qty * (v_coupon_rate / v_freq);

    /* 세금 */
    CM_TAX_01(out->last_coupon, &out->tax_amt);

    out->net_amt = out->face_amt + out->last_coupon - out->tax_amt;

    /* 잔고 삭제 */
    EXEC SQL DELETE FROM TB_BND_BAL
        WHERE ACCT_NO = :v_acct AND BND_CD = :v_bnd;

    /* 상환금 입금 */
    CM_TRANSFER_01("BOND_MATURE_ACCT", v_acct, out->net_amt);

    CM_LOG_01("BN_MATURE_01", v_acct, "만기상환");
    return SUCCESS;
}
""",
    "BN_COUPON_01.pc": """\
/* 이표 쿠폰 금액 계산 처리 - 채권 이표기간 쿠폰 금액 및 경과이자 산출 */
#include "proframe.h"
#include "bn_coupon_str.h"

EXEC SQL INCLUDE SQLCA;

int BN_COUPON_01(bn_coupon_in_t *in, bn_coupon_out_t *out) {
    EXEC SQL BEGIN DECLARE SECTION;
    char    v_bnd[13];
    double  v_coupon_rate;
    int     v_freq;
    char    v_issue_dt[9];
    EXEC SQL END DECLARE SECTION;

    strcpy(v_bnd, in->bnd_cd);

    EXEC SQL SELECT COUPON_RATE, COUPON_FREQ, ISSUE_DT
        INTO :v_coupon_rate, :v_freq, :v_issue_dt
        FROM TB_BND_ISSUE WHERE BND_CD = :v_bnd;

    /* 이표 기간 일수 */
    out->accrued_days = CM_DATE_CHK(in->from_dt, in->to_dt);

    /* 이표 금액 = 액면 × 쿠폰율 / 횟수 */
    out->coupon_amt = in->face_amt * (v_coupon_rate / v_freq);

    /* 경과이자 = 액면 × 쿠폰율 × (경과일 / 365) */
    out->accrued_int = in->face_amt * v_coupon_rate * out->accrued_days / 365.0;

    return SUCCESS;
}
""",
    "BN_YIELD_01.pc": """\
/* 채권 수익률 계산 처리 - 매수단가 잔존기간 기반 단순 수익률 산출 */
#include "proframe.h"

EXEC SQL INCLUDE SQLCA;

int BN_YIELD_01(const char *bnd_cd, double price, double *yield) {
    EXEC SQL BEGIN DECLARE SECTION;
    char    v_bnd[13];
    double  v_coupon_rate;
    char    v_mature_dt[9];
    char    v_today[9];
    EXEC SQL END DECLARE SECTION;

    strcpy(v_bnd, bnd_cd);

    EXEC SQL SELECT COUPON_RATE, MATURE_DT INTO :v_coupon_rate, :v_mature_dt
        FROM TB_BND_ISSUE WHERE BND_CD = :v_bnd;

    EXEC SQL SELECT TO_CHAR(SYSDATE,'YYYYMMDD') INTO :v_today FROM DUAL;

    int remain_days = CM_DATE_CHK(v_today, v_mature_dt);

    /* 단순 수익률 = (쿠폰 + (100-매수가)) / 매수가 × (365/잔존일) */
    double annual_coupon = v_coupon_rate * 100;
    double capital_gain = 100.0 - price;
    *yield = (annual_coupon + capital_gain * 365.0 / remain_days) / price;

    return SUCCESS;
}
""",
    "BN_VALUATION_01.pc": """\
/* 채권 시가평가 처리 - 시장금리 기반 현재가치 할인 평가, 보유 채권 평가액 산출 */
#include "proframe.h"

EXEC SQL INCLUDE SQLCA;

int BN_VALUATION_01(const char *bnd_cd, const char *base_dt, double *eval_price) {
    EXEC SQL BEGIN DECLARE SECTION;
    char    v_bnd[13];
    char    v_dt[9];
    double  v_market_yield;
    double  v_coupon_rate;
    char    v_mature_dt[9];
    EXEC SQL END DECLARE SECTION;

    strcpy(v_bnd, bnd_cd);
    strcpy(v_dt, base_dt);

    EXEC SQL SELECT COUPON_RATE, MATURE_DT INTO :v_coupon_rate, :v_mature_dt
        FROM TB_BND_ISSUE WHERE BND_CD = :v_bnd;

    /* 시장금리 조회 */
    CM_RATE_01("BOND_YIELD", v_dt, &v_market_yield);

    /* 잔존 기간 */
    int remain_days = CM_DATE_CHK(v_dt, v_mature_dt);
    double years = remain_days / 365.0;

    /* 현재가치 할인 (단순 계산) */
    double yield_used;
    BN_YIELD_01(v_bnd, 100.0, &yield_used);

    /* PV = C/(1+r) + C/(1+r)^2 + ... + (C+F)/(1+r)^n */
    *eval_price = 100.0 * v_coupon_rate / v_market_yield *
                  (1 - 1.0 / pow(1 + v_market_yield, years)) +
                  100.0 / pow(1 + v_market_yield, years);

    return SUCCESS;
}
""",
    "BN_ACCRUED_01.pc": """\
/* 경과이자 계산 처리 - 직전 이표일부터 현재까지 경과일수 기반 경과이자 산출 */
#include "proframe.h"
#include "bn_coupon_str.h"

EXEC SQL INCLUDE SQLCA;

int BN_ACCRUED_01(bn_coupon_in_t *in, bn_coupon_out_t *out) {
    EXEC SQL BEGIN DECLARE SECTION;
    char    v_bnd[13];
    double  v_coupon_rate;
    int     v_freq;
    char    v_last_coupon_dt[9];
    char    v_today[9];
    EXEC SQL END DECLARE SECTION;

    strcpy(v_bnd, in->bnd_cd);

    EXEC SQL SELECT COUPON_RATE, COUPON_FREQ INTO :v_coupon_rate, :v_freq
        FROM TB_BND_ISSUE WHERE BND_CD = :v_bnd;

    EXEC SQL SELECT TO_CHAR(SYSDATE,'YYYYMMDD') INTO :v_today FROM DUAL;

    /* 직전 이표일로부터 경과일 계산 */
    out->accrued_days = CM_DATE_CHK(v_last_coupon_dt, v_today);

    /* 경과이자 = 액면 × 쿠폰율 × (경과일 / 365) */
    out->accrued_int = in->face_amt * v_coupon_rate * out->accrued_days / 365.0;

    return SUCCESS;
}
""",

    # ========== Fund (FD) ==========
    "FD_SUBSCRIBE_01.pc": """\
/* 펀드 가입 설정 처리 - 기준가 조회, 수수료 차감, 좌수 배정, 잔고 등록 */
#include "proframe.h"
#include "fd_sub_str.h"

EXEC SQL INCLUDE SQLCA;

int FD_SUBSCRIBE_01(fd_sub_in_t *in, fd_sub_out_t *out) {
    EXEC SQL BEGIN DECLARE SECTION;
    char    v_acct[11];
    char    v_fund[13];
    double  v_nav;
    double  v_avail;
    EXEC SQL END DECLARE SECTION;

    strcpy(v_acct, in->acct_no);
    strcpy(v_fund, in->fund_cd);

    /* 기준가 조회 */
    EXEC SQL SELECT NAV INTO :v_nav
        FROM TB_FND_NAV
        WHERE FUND_CD = :v_fund
        AND BASE_DT = (SELECT MAX(BASE_DT) FROM TB_FND_NAV WHERE FUND_CD = :v_fund);
    out->nav = v_nav;

    /* 가입 수수료 */
    CM_FEE_CALC("FUND_SUB", in->invest_amt, &out->fee_amt);
    out->net_invest = in->invest_amt - out->fee_amt;

    /* 배정 좌수 */
    out->alloc_qty = out->net_invest / v_nav * 1000;  /* 1000좌 단위 */

    /* 잔액 확인 */
    EXEC SQL SELECT AVAIL_AMT INTO :v_avail
        FROM TB_ACCT_BAL WHERE ACCT_NO = :v_acct;

    if (v_avail < in->invest_amt) {
        strcpy(out->err_cd, "E701");
        strcpy(out->err_msg, "투자가능금액 부족");
        return FAIL;
    }

    /* 펀드 잔고 등록 */
    EXEC SQL INSERT INTO TB_FND_BAL
        (ACCT_NO, FUND_CD, HOLD_QTY, BUY_AMT, BUY_DT)
        VALUES (:v_acct, :v_fund, :out->alloc_qty, :out->net_invest,
                TO_CHAR(SYSDATE,'YYYYMMDD'));

    /* 대금 차감 */
    EXEC SQL UPDATE TB_ACCT_BAL
        SET CASH_BAL = CASH_BAL - :in->invest_amt,
            AVAIL_AMT = AVAIL_AMT - :in->invest_amt
        WHERE ACCT_NO = :v_acct;

    /* KSD 설정 통보 */
    IF_KSD_01(NULL, NULL);

    CM_LOG_01("FD_SUBSCRIBE_01", v_acct, "펀드가입");
    return SUCCESS;
}
""",
    "FD_REDEEM_01.pc": """\
/* 펀드 환매 처리 - 보유좌수 확인, 기준가 적용, 환매수수료 계산, 과세, KSD 통보 */
#include "proframe.h"
#include "fd_redeem_str.h"

EXEC SQL INCLUDE SQLCA;

int FD_REDEEM_01(fd_redeem_in_t *in, fd_redeem_out_t *out) {
    EXEC SQL BEGIN DECLARE SECTION;
    char    v_acct[11];
    char    v_fund[13];
    double  v_hold_qty;
    double  v_buy_amt;
    char    v_buy_dt[9];
    EXEC SQL END DECLARE SECTION;

    strcpy(v_acct, in->acct_no);
    strcpy(v_fund, in->fund_cd);

    /* 보유좌수 확인 */
    EXEC SQL SELECT HOLD_QTY, BUY_AMT, BUY_DT
        INTO :v_hold_qty, :v_buy_amt, :v_buy_dt
        FROM TB_FND_BAL
        WHERE ACCT_NO = :v_acct AND FUND_CD = :v_fund;

    double redeem_qty = in->redeem_qty;
    if (strcmp(in->redeem_tp, "01") == 0) {
        redeem_qty = v_hold_qty;  /* 전액 환매 */
    }

    if (v_hold_qty < redeem_qty) {
        strcpy(out->err_cd, "E801");
        strcpy(out->err_msg, "환매가능좌수 부족");
        return FAIL;
    }

    /* 기준가 조회 */
    FD_NAV_01(v_fund, &out->nav);

    /* 환매 금액 */
    out->gross_amt = redeem_qty * out->nav / 1000;

    /* 환매 수수료 */
    rd_fee_in_t fee_in;
    rd_fee_out_t fee_out;
    strcpy(fee_in.fund_cd, v_fund);
    strcpy(fee_in.buy_dt, v_buy_dt);
    fee_in.sell_amt = out->gross_amt;
    RD_FEE_03(&fee_in, &fee_out);
    out->fee_amt = fee_out.fee_amt;

    /* 환매 과세 */
    double profit = out->gross_amt - (v_buy_amt * redeem_qty / v_hold_qty);
    if (profit > 0) {
        CM_TAX_01(profit, &out->tax_amt);
    }

    out->net_amt = out->gross_amt - out->fee_amt - out->tax_amt;

    /* 잔고 차감 */
    EXEC SQL UPDATE TB_FND_BAL
        SET HOLD_QTY = HOLD_QTY - :redeem_qty
        WHERE ACCT_NO = :v_acct AND FUND_CD = :v_fund;

    /* KSD 환매 통보 */
    IF_KSD_01(NULL, NULL);

    CM_LOG_01("FD_REDEEM_01", v_acct, "펀드환매");
    return SUCCESS;
}
""",
    "FD_PAY_01.pc": """\
/* 분배금 지급 처리 - 펀드 분배금 단가 조회, 보유좌수 기준 지급액 산출, 과세, KSD 연동 */
#include "proframe.h"
#include "fd_pay_str.h"

EXEC SQL INCLUDE SQLCA;

int FD_PAY_01(fd_pay_in_t *in, fd_pay_out_t *out) {
    EXEC SQL BEGIN DECLARE SECTION;
    char    fund_cd[13];
    double  dist_per_unit;
    long    hold_qty;
    char    pay_dt[9];
    EXEC SQL END DECLARE SECTION;

    strcpy(fund_cd, in->fund_cd);
    strcpy(pay_dt, in->pay_dt);

    /* 분배금 단가 조회 */
    EXEC SQL SELECT DIST_AMT INTO :dist_per_unit
        FROM TB_FUND_DIST
        WHERE FUND_CD = :fund_cd
        AND DIST_DT = :pay_dt
        AND DIST_TP = 'CASH';

    /* 보유좌수 조회 */
    EXEC SQL SELECT HOLD_QTY INTO :hold_qty
        FROM TB_FND_BAL
        WHERE ACCT_NO = :in->acct_no AND FUND_CD = :fund_cd;

    /* 보유좌수 기준 지급액 산출 */
    out->gross_amt = hold_qty * dist_per_unit;

    /* 세금 계산 */
    FD_TAX_02(out->gross_amt, in->acct_type, &out->tax_amt);

    out->net_amt = out->gross_amt - out->tax_amt;

    /* KSD SAFE+ 연동 데이터 생성 */
    FD_KSD_IF_01(in, out);

    /* 원장 반영 */
    EXEC SQL INSERT INTO TB_TX_HIST
        (TX_NO, TX_DT, SVC_NM, ACCT_NO, TX_TP, TX_AMT, TX_DESC)
        VALUES (SQ_TX_NO.NEXTVAL, :pay_dt, 'FD_PAY_01',
                :in->acct_no, 'DIST_PAY', :out->net_amt, '분배금지급');

    return SUCCESS;
}
""",
    "FD_TAX_02.pc": """\
/* 분배금 과세 처리 - 펀드 분배금 세율 조회 및 세액 산출, 비과세 계좌 면제 */
#include "proframe.h"

EXEC SQL INCLUDE SQLCA;

int FD_TAX_02(double gross_amt, const char *acct_type, double *tax_amt) {
    EXEC SQL BEGIN DECLARE SECTION;
    char    v_type[3];
    double  v_tax_rate;
    EXEC SQL END DECLARE SECTION;

    strcpy(v_type, acct_type);

    /* 비과세 계좌 */
    if (strcmp(v_type, "03") == 0) {
        *tax_amt = 0;
        return SUCCESS;
    }

    /* 세율 조회 */
    EXEC SQL SELECT TAX_RATE INTO :v_tax_rate
        FROM TB_TAX_MST
        WHERE TAX_TYPE = 'FUND_DIST' AND USE_YN = 'Y';

    if (SQLCA.sqlcode != 0) {
        CM_TAX_01(gross_amt, tax_amt);  /* 기본 세율 적용 */
        return SUCCESS;
    }

    *tax_amt = gross_amt * v_tax_rate;
    return SUCCESS;
}
""",
    "FD_KSD_IF_01.pc": """\
/* KSD SAFE+ 인터페이스 전문 생성 처리 - 예탁원 설정 환매 분배금 전문 등록 및 전송 */
#include "proframe.h"
#include "if_ksd_str.h"

EXEC SQL INCLUDE SQLCA;

int FD_KSD_IF_01(void *pay_in, void *pay_out) {
    EXEC SQL BEGIN DECLARE SECTION;
    char    v_fund[13];
    char    v_acct[11];
    double  v_amt;
    EXEC SQL END DECLARE SECTION;

    /* KSD 인터페이스 전문 등록 */
    EXEC SQL INSERT INTO TB_KSD_IF
        (IF_NO, IF_DT, IF_TP, FUND_CD, ACCT_NO, AMT, SEND_ST)
        VALUES (SQ_KSD_IF.NEXTVAL, TO_CHAR(SYSDATE,'YYYYMMDD'),
                'DIST_PAY', :v_fund, :v_acct, :v_amt, '00');

    /* 전송 처리 */
    IF_KSD_01(NULL, NULL);

    return SUCCESS;
}
""",
    "FD_NAV_01.pc": """\
/* 펀드 기준가 조회 산출 처리 - 최신 기준가 NAV 조회, 총자산 총좌수 기반 산출 */
#include "proframe.h"

EXEC SQL INCLUDE SQLCA;

int FD_NAV_01(const char *fund_cd, double *nav) {
    EXEC SQL BEGIN DECLARE SECTION;
    char    v_fund[13];
    double  v_nav;
    double  v_tot_asset;
    double  v_tot_units;
    EXEC SQL END DECLARE SECTION;

    strcpy(v_fund, fund_cd);

    /* 최신 기준가 조회 */
    EXEC SQL SELECT NAV, TOT_ASSET, TOT_UNITS INTO :v_nav, :v_tot_asset, :v_tot_units
        FROM TB_FND_NAV
        WHERE FUND_CD = :v_fund
        AND BASE_DT = (SELECT MAX(BASE_DT) FROM TB_FND_NAV WHERE FUND_CD = :v_fund);

    if (SQLCA.sqlcode != 0) {
        *nav = 1000.0;  /* 기본 기준가 */
        return FAIL;
    }

    *nav = v_nav;
    return SUCCESS;
}
""",
    "FD_SWITCH_01.pc": """\
/* 펀드 전환 처리 - 기존 펀드 환매 후 신규 펀드 재가입, 전환 수수료 적용 */
#include "proframe.h"
#include "fd_redeem_str.h"
#include "fd_sub_str.h"

EXEC SQL INCLUDE SQLCA;

int FD_SWITCH_01(const char *acct_no, const char *from_fund,
                 const char *to_fund, double switch_qty) {
    /* 1단계: 기존 펀드 환매 */
    fd_redeem_in_t rd_in;
    fd_redeem_out_t rd_out;
    strcpy(rd_in.acct_no, acct_no);
    strcpy(rd_in.fund_cd, from_fund);
    rd_in.redeem_qty = switch_qty;
    strcpy(rd_in.redeem_tp, "02");  /* 일부 환매 */

    if (FD_REDEEM_01(&rd_in, &rd_out) != SUCCESS) {
        return FAIL;
    }

    /* 2단계: 환매금으로 신규 펀드 가입 */
    fd_sub_in_t sub_in;
    fd_sub_out_t sub_out;
    strcpy(sub_in.acct_no, acct_no);
    strcpy(sub_in.fund_cd, to_fund);
    sub_in.invest_amt = rd_out.net_amt;

    if (FD_SUBSCRIBE_01(&sub_in, &sub_out) != SUCCESS) {
        return FAIL;
    }

    CM_LOG_01("FD_SWITCH_01", acct_no, "펀드전환");
    return SUCCESS;
}
""",
    "FD_REPORT_01.pc": """\
/* 펀드 운용 보고서 생성 처리 - 기준가 추이, 투자자수, 운용 현황 리포트 산출 */
#include "proframe.h"
#include "jg_bal_str.h"

EXEC SQL INCLUDE SQLCA;

int FD_REPORT_01(const char *fund_cd, const char *base_dt, void *report) {
    EXEC SQL BEGIN DECLARE SECTION;
    char    v_fund[13];
    char    v_dt[9];
    double  v_nav;
    double  v_prev_nav;
    double  v_tot_asset;
    int     v_investor_cnt;
    EXEC SQL END DECLARE SECTION;

    strcpy(v_fund, fund_cd);
    strcpy(v_dt, base_dt);

    /* 기준가 추이 */
    double nav;
    FD_NAV_01(v_fund, &nav);

    EXEC SQL SELECT NAV INTO :v_prev_nav
        FROM TB_FND_NAV
        WHERE FUND_CD = :v_fund
        AND BASE_DT = (SELECT MAX(BASE_DT) FROM TB_FND_NAV
                        WHERE FUND_CD = :v_fund AND BASE_DT < :v_dt);

    /* 투자자 수 */
    EXEC SQL SELECT COUNT(DISTINCT ACCT_NO) INTO :v_investor_cnt
        FROM TB_FND_BAL
        WHERE FUND_CD = :v_fund AND HOLD_QTY > 0;

    return SUCCESS;
}
""",

    # ========== Redeem (RD) ==========
    "RD_FEE_03.pc": """\
/* 수익증권 환매 수수료 계산 처리 - 보유기간별 후취 수수료율 적용, 수수료 금액 및 세금 산출 */
#include "proframe.h"
#include "rd_fee_str.h"

EXEC SQL INCLUDE SQLCA;

int RD_FEE_03(rd_fee_in_t *in, rd_fee_out_t *out) {
    EXEC SQL BEGIN DECLARE SECTION;
    char    fund_cd[13];
    double  fee_rate;
    int     hold_days;
    EXEC SQL END DECLARE SECTION;

    strcpy(fund_cd, in->fund_cd);

    /* 보유일수 계산 */
    hold_days = CM_DATE_CHK(in->buy_dt, in->sell_dt);
    out->hold_days = hold_days;

    /* 보유기간별 수수료율 조회 */
    EXEC SQL SELECT FEE_RATE INTO :fee_rate
        FROM TB_FEE_RATE
        WHERE FUND_CD = :fund_cd
        AND :hold_days BETWEEN FR_DAYS AND TO_DAYS
        AND USE_YN = 'Y';

    if (SQLCA.sqlcode != 0) {
        fee_rate = 0;  /* 수수료 면제 구간 */
    }

    out->fee_rate = fee_rate;
    out->fee_amt = in->sell_amt * fee_rate;

    /* 수수료에 대한 세금 */
    CM_TAX_01(out->fee_amt, &out->tax_amt);

    out->net_amt = in->sell_amt - out->fee_amt - out->tax_amt;

    return SUCCESS;
}
""",
    "RD_PROC_01.pc": """\
/* 수익증권 환매 처리 메인 - 보유좌수 확인, 기준가 적용, 수수료 계산 호출, 잔고 차감 */
#include "proframe.h"
#include "rd_proc_str.h"

EXEC SQL INCLUDE SQLCA;

int RD_PROC_01(rd_proc_in_t *in, rd_proc_out_t *out) {
    EXEC SQL BEGIN DECLARE SECTION;
    char    v_acct[11];
    char    v_fund[13];
    double  v_hold_qty;
    double  v_nav;
    char    v_buy_dt[9];
    EXEC SQL END DECLARE SECTION;

    strcpy(v_acct, in->acct_no);
    strcpy(v_fund, in->fund_cd);

    /* 보유좌수 확인 */
    EXEC SQL SELECT HOLD_QTY, BUY_DT INTO :v_hold_qty, :v_buy_dt
        FROM TB_FND_BAL
        WHERE ACCT_NO = :v_acct AND FUND_CD = :v_fund;

    if (v_hold_qty < in->sell_qty) {
        strcpy(out->err_cd, "E901");
        strcpy(out->err_msg, "환매가능좌수 부족");
        return FAIL;
    }

    /* 기준가 조회 */
    FD_NAV_01(v_fund, &v_nav);
    out->sell_amt = in->sell_qty * v_nav / 1000;

    /* 수수료 계산 호출 */
    rd_fee_in_t fee_in;
    rd_fee_out_t fee_out;
    strcpy(fee_in.fund_cd, v_fund);
    strcpy(fee_in.buy_dt, v_buy_dt);
    fee_in.sell_amt = out->sell_amt;
    RD_FEE_03(&fee_in, &fee_out);

    out->fee_amt = fee_out.fee_amt;
    out->tax_amt = fee_out.tax_amt;
    out->net_amt = fee_out.net_amt;

    /* 잔고 차감 */
    EXEC SQL UPDATE TB_FND_BAL
        SET HOLD_QTY = HOLD_QTY - :in->sell_qty
        WHERE ACCT_NO = :v_acct AND FUND_CD = :v_fund;

    CM_LOG_01("RD_PROC_01", v_acct, "수익증권환매");
    return SUCCESS;
}
""",
    "RD_PARTIAL_01.pc": """\
/* 부분 환매 처리 - 보유좌수 일부 비율 환매, 잔고 조회 후 환매 처리 위임 */
#include "proframe.h"
#include "rd_proc_str.h"

EXEC SQL INCLUDE SQLCA;

int RD_PARTIAL_01(const char *acct_no, const char *fund_cd,
                  double partial_rate) {
    EXEC SQL BEGIN DECLARE SECTION;
    char    v_acct[11];
    char    v_fund[13];
    double  v_hold_qty;
    EXEC SQL END DECLARE SECTION;

    strcpy(v_acct, acct_no);
    strcpy(v_fund, fund_cd);

    /* 보유좌수 확인 */
    EXEC SQL SELECT HOLD_QTY INTO :v_hold_qty
        FROM TB_FND_BAL
        WHERE ACCT_NO = :v_acct AND FUND_CD = :v_fund;

    long partial_qty = (long)(v_hold_qty * partial_rate);

    /* 잔고 조회 */
    jg_bal_in_t bal_in;
    jg_bal_out_t bal_out;
    strcpy(bal_in.acct_no, v_acct);
    JG_BAL_02(&bal_in, &bal_out);

    /* 환매 처리 위임 */
    rd_proc_in_t proc_in;
    rd_proc_out_t proc_out;
    strcpy(proc_in.acct_no, v_acct);
    strcpy(proc_in.fund_cd, v_fund);
    proc_in.sell_qty = partial_qty;
    RD_PROC_01(&proc_in, &proc_out);

    CM_LOG_01("RD_PARTIAL_01", v_acct, "부분환매");
    return SUCCESS;
}
""",
    "RD_PENALTY_01.pc": """\
/* 조기환매 패널티 계산 처리 - 30일/90일 미만 보유 시 조기환매 위약금 산출 */
#include "proframe.h"

EXEC SQL INCLUDE SQLCA;

int RD_PENALTY_01(const char *fund_cd, const char *buy_dt,
                  double amt, double *penalty) {
    EXEC SQL BEGIN DECLARE SECTION;
    char    v_fund[13];
    EXEC SQL END DECLARE SECTION;

    strcpy(v_fund, fund_cd);

    /* 보유일 계산 */
    char today[9];
    EXEC SQL SELECT TO_CHAR(SYSDATE,'YYYYMMDD') INTO :today FROM DUAL;
    int hold_days = CM_DATE_CHK(buy_dt, today);

    /* 30일 미만 조기환매 패널티 */
    if (hold_days < 30) {
        *penalty = amt * 0.02;  /* 2% 패널티 */
    } else if (hold_days < 90) {
        *penalty = amt * 0.01;  /* 1% 패널티 */
    } else {
        *penalty = 0;
    }

    return SUCCESS;
}
""",
    "RD_SETTLE_01.pc": """\
/* 환매 결제 처리 - 환매대금 계좌 입금, KSD 결제 통보 */
#include "proframe.h"

EXEC SQL INCLUDE SQLCA;

int RD_SETTLE_01(const char *acct_no, const char *fund_cd, double net_amt) {
    EXEC SQL BEGIN DECLARE SECTION;
    char    v_acct[11];
    char    v_fund[13];
    double  v_amt;
    EXEC SQL END DECLARE SECTION;

    strcpy(v_acct, acct_no);
    strcpy(v_fund, fund_cd);
    v_amt = net_amt;

    /* 환매대금 입금 */
    CM_TRANSFER_01("FUND_REDEEM_ACCT", v_acct, v_amt);

    /* KSD 결제 통보 */
    IF_KSD_01(NULL, NULL);

    CM_LOG_01("RD_SETTLE_01", v_acct, "환매결제");
    return SUCCESS;
}
""",

    # ========== Dividend (DV) ==========
    "DV_PAY_01.pc": """\
/* 배당금 지급 처리 - 배당금 단가 조회, 보유수량 기준 배당금 산출, 원천징수 세금 계산, 입금 */
#include "proframe.h"
#include "dv_pay_str.h"

EXEC SQL INCLUDE SQLCA;

int DV_PAY_01(dv_pay_in_t *in, dv_pay_out_t *out) {
    EXEC SQL BEGIN DECLARE SECTION;
    char    v_acct[11];
    char    v_stk[7];
    char    v_div_dt[9];
    double  v_div_amt;
    double  v_tax_rate;
    EXEC SQL END DECLARE SECTION;

    strcpy(v_acct, in->acct_no);
    strcpy(v_stk, in->stk_cd);
    strcpy(v_div_dt, in->div_dt);

    /* 배당금 단가 조회 */
    EXEC SQL SELECT DIV_AMT, TAX_RATE INTO :v_div_amt, :v_tax_rate
        FROM TB_DIV_MST
        WHERE STK_CD = :v_stk AND DIV_DT = :v_div_dt;

    /* 총 배당금 */
    out->gross_amt = in->hold_qty * v_div_amt;

    /* 원천징수 세액 */
    CM_TAX_01(out->gross_amt, &out->tax_amt);

    out->net_amt = out->gross_amt - out->tax_amt;

    /* 배당금 입금 */
    CM_TRANSFER_01("DIV_PAY_ACCT", v_acct, out->net_amt);

    CM_LOG_01("DV_PAY_01", v_acct, "배당금지급");
    return SUCCESS;
}
""",
    "DV_CALC_01.pc": """\
/* 배당금 산정 처리 - 배당락일 기준 보유자별 배당금 총액 산출 */
#include "proframe.h"

EXEC SQL INCLUDE SQLCA;

int DV_CALC_01(const char *stk_cd, const char *record_dt,
               double *total_div) {
    EXEC SQL BEGIN DECLARE SECTION;
    char    v_stk[7];
    char    v_dt[9];
    double  v_div_amt;
    double  v_total_qty;
    EXEC SQL END DECLARE SECTION;

    strcpy(v_stk, stk_cd);
    strcpy(v_dt, record_dt);

    EXEC SQL SELECT DIV_AMT INTO :v_div_amt
        FROM TB_DIV_MST
        WHERE STK_CD = :v_stk AND RECORD_DT = :v_dt;

    /* 전체 보유자 수량 합계 */
    EXEC SQL SELECT NVL(SUM(HOLD_QTY),0) INTO :v_total_qty
        FROM TB_STK_BAL WHERE STK_CD = :v_stk AND HOLD_QTY > 0;

    int hold_days = CM_DATE_CHK(v_dt, v_dt);  /* 기준일 영업일 확인 */

    *total_div = v_total_qty * v_div_amt;
    return SUCCESS;
}
""",
    "DV_WITHHOLD_01.pc": """\
/* 배당소득 원천징수 세금 계산 처리 - 비과세 계좌 면제, 일반 계좌 원천징수 세액 산출 */
#include "proframe.h"

EXEC SQL INCLUDE SQLCA;

int DV_WITHHOLD_01(const char *acct_no, double gross_div,
                   double *withhold_tax) {
    EXEC SQL BEGIN DECLARE SECTION;
    char    v_acct[11];
    char    v_acct_tp[3];
    EXEC SQL END DECLARE SECTION;

    strcpy(v_acct, acct_no);

    /* 계좌 유형 조회 (비과세 여부) */
    EXEC SQL SELECT ACCT_TP INTO :v_acct_tp
        FROM TB_ACCT_MST WHERE ACCT_NO = :v_acct;

    if (strcmp(v_acct_tp, "03") == 0) {
        *withhold_tax = 0;  /* 비과세 계좌 */
        return SUCCESS;
    }

    /* 일반 원천징수 */
    CM_TAX_01(gross_div, withhold_tax);
    return SUCCESS;
}
""",
    "DV_REINVEST_01.pc": """\
/* 배당금 재투자 처리 - 배당금으로 동일 종목 시장가 매수 주문 자동 실행 */
#include "proframe.h"
#include "st_buy_str.h"

EXEC SQL INCLUDE SQLCA;

int DV_REINVEST_01(const char *acct_no, const char *stk_cd,
                   double div_amt) {
    EXEC SQL BEGIN DECLARE SECTION;
    char    v_stk[7];
    double  v_price;
    EXEC SQL END DECLARE SECTION;

    strcpy(v_stk, stk_cd);

    /* 현재가 조회 */
    double cur_price, prev_close;
    ST_PRICE_01(v_stk, &cur_price, &prev_close);

    /* 재투자 수량 (단주 절사) */
    long reinvest_qty = (long)(div_amt / cur_price);
    if (reinvest_qty <= 0) {
        return SUCCESS;  /* 재투자 불가 (금액 부족) */
    }

    /* 매수 주문 */
    st_buy_in_t buy_in;
    st_buy_out_t buy_out;
    strcpy(buy_in.acct_no, acct_no);
    strcpy(buy_in.stk_cd, stk_cd);
    buy_in.price = cur_price;
    buy_in.qty = reinvest_qty;
    strcpy(buy_in.ord_type, "01");  /* 시장가 */

    ST_BUY_01(&buy_in, &buy_out);

    CM_LOG_01("DV_REINVEST_01", acct_no, "배당재투자");
    return SUCCESS;
}
""",
    "DV_REPORT_01.pc": """\
/* 배당 보고서 생성 처리 - 연간 배당금 지급 현황 및 세금 집계 리포트 */
#include "proframe.h"

EXEC SQL INCLUDE SQLCA;

int DV_REPORT_01(const char *base_year, void *report) {
    EXEC SQL BEGIN DECLARE SECTION;
    char    v_year[5];
    double  v_total_div;
    int     v_div_cnt;
    double  v_total_tax;
    EXEC SQL END DECLARE SECTION;

    strcpy(v_year, base_year);

    EXEC SQL SELECT COUNT(*), NVL(SUM(DIV_AMT),0)
        INTO :v_div_cnt, :v_total_div
        FROM TB_DIV_MST
        WHERE DIV_DT LIKE :v_year || '%';

    EXEC SQL SELECT NVL(SUM(TX_AMT),0) INTO :v_total_tax
        FROM TB_TX_HIST
        WHERE TX_TP = 'DIV_PAY' AND TX_DT LIKE :v_year || '%';

    return SUCCESS;
}
""",

    # ========== Balance (JG) ==========
    "JG_BAL_02.pc": """\
/* 계좌 잔고 통합 조회 처리 - 주식 채권 펀드 현금 전체 자산 평가액 조회 */
#include "proframe.h"
#include "jg_bal_str.h"

EXEC SQL INCLUDE SQLCA;

int JG_BAL_02(jg_bal_in_t *in, jg_bal_out_t *out) {
    EXEC SQL BEGIN DECLARE SECTION;
    char    v_acct[11];
    double  v_stk_eval;
    double  v_bnd_eval;
    double  v_fnd_eval;
    double  v_cash;
    int     v_cnt;
    EXEC SQL END DECLARE SECTION;

    strcpy(v_acct, in->acct_no);

    /* 주식 평가액 */
    EXEC SQL SELECT NVL(SUM(EVAL_AMT),0), COUNT(*)
        INTO :v_stk_eval, :v_cnt
        FROM TB_STK_BAL WHERE ACCT_NO = :v_acct AND HOLD_QTY > 0;
    out->stk_eval = v_stk_eval;
    out->item_cnt = v_cnt;

    /* 채권 평가액 */
    EXEC SQL SELECT NVL(SUM(EVAL_AMT),0) INTO :v_bnd_eval
        FROM TB_BND_BAL WHERE ACCT_NO = :v_acct AND HOLD_QTY > 0;
    out->bnd_eval = v_bnd_eval;

    /* 펀드 평가액 */
    EXEC SQL SELECT NVL(SUM(EVAL_AMT),0) INTO :v_fnd_eval
        FROM TB_FND_BAL WHERE ACCT_NO = :v_acct AND HOLD_QTY > 0;
    out->fnd_eval = v_fnd_eval;

    /* 현금 */
    EXEC SQL SELECT CASH_BAL INTO :v_cash
        FROM TB_ACCT_BAL WHERE ACCT_NO = :v_acct;
    out->cash_bal = v_cash;

    out->total_asset = v_stk_eval + v_bnd_eval + v_fnd_eval + v_cash;
    return SUCCESS;
}
""",
    "JG_POS_01.pc": """\
/* 포지션 상세 조회 처리 - 자산유형별 보유 종목 수 및 상세 포지션 조회 */
#include "proframe.h"

EXEC SQL INCLUDE SQLCA;

int JG_POS_01(const char *acct_no, const char *asset_tp, void *positions) {
    EXEC SQL BEGIN DECLARE SECTION;
    char    v_acct[11];
    int     v_cnt;
    EXEC SQL END DECLARE SECTION;

    strcpy(v_acct, acct_no);

    if (strcmp(asset_tp, "STK") == 0) {
        EXEC SQL SELECT COUNT(*) INTO :v_cnt
            FROM TB_STK_BAL WHERE ACCT_NO = :v_acct AND HOLD_QTY > 0;
    } else if (strcmp(asset_tp, "BND") == 0) {
        EXEC SQL SELECT COUNT(*) INTO :v_cnt
            FROM TB_BND_BAL WHERE ACCT_NO = :v_acct AND HOLD_QTY > 0;
    } else if (strcmp(asset_tp, "FND") == 0) {
        EXEC SQL SELECT COUNT(*) INTO :v_cnt
            FROM TB_FND_BAL WHERE ACCT_NO = :v_acct AND HOLD_QTY > 0;
    }

    return v_cnt;
}
""",
    "JG_PNL_01.pc": """\
/* 손익 계산 처리 - 매입금액 대비 평가금액 손익 금액 및 수익률 산출 */
#include "proframe.h"

EXEC SQL INCLUDE SQLCA;

int JG_PNL_01(const char *acct_no, double *pnl_amt, double *pnl_rate) {
    EXEC SQL BEGIN DECLARE SECTION;
    char    v_acct[11];
    double  v_buy_total;
    double  v_eval_total;
    EXEC SQL END DECLARE SECTION;

    strcpy(v_acct, acct_no);

    /* 주식 매입/평가 */
    EXEC SQL SELECT NVL(SUM(BUY_AMT),0), NVL(SUM(EVAL_AMT),0)
        INTO :v_buy_total, :v_eval_total
        FROM TB_STK_BAL WHERE ACCT_NO = :v_acct AND HOLD_QTY > 0;

    /* 시세 갱신 (최신가 반영) */
    /* 각 종목별 현재가 조회 */
    double cur_price, prev_close;
    ST_PRICE_01("", &cur_price, &prev_close);

    /* 채권 시가평가 */
    BN_VALUATION_01("", "", NULL);

    *pnl_amt = v_eval_total - v_buy_total;
    *pnl_rate = (v_buy_total > 0) ? (*pnl_amt / v_buy_total * 100) : 0;

    return SUCCESS;
}
""",
    "JG_ASSET_01.pc": """\
/* 종합 자산 평가 처리 - 주식 채권 펀드 현금 포지션별 시가 평가 및 총자산 손익 산출 */
#include "proframe.h"
#include "jg_asset_str.h"

EXEC SQL INCLUDE SQLCA;

int JG_ASSET_01(jg_asset_in_t *in, jg_asset_out_t *out) {
    EXEC SQL BEGIN DECLARE SECTION;
    char    v_acct[11];
    EXEC SQL END DECLARE SECTION;

    strcpy(v_acct, in->acct_no);

    /* 포지션별 조회 */
    JG_POS_01(v_acct, "STK", NULL);
    JG_POS_01(v_acct, "BND", NULL);
    JG_POS_01(v_acct, "FND", NULL);

    /* 주식 시가 평가 */
    EXEC SQL SELECT NVL(SUM(HOLD_QTY * p.CUR_PRICE),0)
        INTO :out->stk_eval
        FROM TB_STK_BAL b, TB_STK_PRICE p
        WHERE b.ACCT_NO = :v_acct AND b.STK_CD = p.STK_CD AND b.HOLD_QTY > 0;

    /* 채권 시가 평가 */
    EXEC SQL SELECT NVL(SUM(EVAL_AMT),0) INTO :out->bnd_eval
        FROM TB_BND_BAL WHERE ACCT_NO = :v_acct;

    /* 펀드 기준가 평가 */
    EXEC SQL SELECT NVL(SUM(b.HOLD_QTY * n.NAV / 1000),0)
        INTO :out->fnd_eval
        FROM TB_FND_BAL b, TB_FND_NAV n
        WHERE b.ACCT_NO = :v_acct AND b.FUND_CD = n.FUND_CD
        AND n.BASE_DT = (SELECT MAX(BASE_DT) FROM TB_FND_NAV WHERE FUND_CD = b.FUND_CD);

    /* 현금 */
    EXEC SQL SELECT CASH_BAL INTO :out->cash_bal
        FROM TB_ACCT_BAL WHERE ACCT_NO = :v_acct;

    out->total_asset = out->stk_eval + out->bnd_eval + out->fnd_eval + out->cash_bal;

    /* 손익 계산 */
    double pnl_amt, pnl_rate;
    JG_PNL_01(v_acct, &pnl_amt, &pnl_rate);
    out->pnl_amt = pnl_amt;
    out->pnl_rate = pnl_rate;

    return SUCCESS;
}
""",
    "JG_RECONCILE_01.pc": """\
/* 잔고 대사 처리 - KSD 예탁원 수탁잔고와 사내 잔고 비교 검증, 불일치 알림 */
#include "proframe.h"

EXEC SQL INCLUDE SQLCA;

int JG_RECONCILE_01(const char *base_dt) {
    EXEC SQL BEGIN DECLARE SECTION;
    char    v_dt[9];
    int     v_diff_cnt;
    EXEC SQL END DECLARE SECTION;

    strcpy(v_dt, base_dt);

    /* KSD 수탁 잔고 vs 사내 잔고 비교 */
    EXEC SQL SELECT COUNT(*) INTO :v_diff_cnt
        FROM TB_KSD_IF k, TB_STK_BAL s
        WHERE k.ACCT_NO = s.ACCT_NO
        AND k.IF_DT = :v_dt
        AND k.QTY != s.HOLD_QTY;

    if (v_diff_cnt > 0) {
        /* 불일치 건 알림 */
        IF_KSD_01(NULL, NULL);
        CM_LOG_01("JG_RECONCILE_01", "BATCH", "잔고불일치발견");
    }

    CM_LOG_01("JG_RECONCILE_01", "BATCH", "잔고대사완료");
    return v_diff_cnt;
}
""",

    # ========== Risk Management (RM) ==========
    "RM_EXPOSURE_01.pc": """\
/* 익스포저 산출 처리 - 포지션 기반 총 익스포저 계산, 한도 대비 사용률 및 리스크 레벨 판정 */
#include "proframe.h"
#include "rm_exposure_str.h"

EXEC SQL INCLUDE SQLCA;

int RM_EXPOSURE_01(rm_exposure_in_t *in, rm_exposure_out_t *out) {
    EXEC SQL BEGIN DECLARE SECTION;
    char    v_acct[11];
    double  v_long_amt;
    double  v_short_amt;
    EXEC SQL END DECLARE SECTION;

    strcpy(v_acct, in->acct_no);

    /* 매수 포지션 (Long) */
    EXEC SQL SELECT NVL(SUM(EVAL_AMT),0) INTO :v_long_amt
        FROM TB_STK_BAL WHERE ACCT_NO = :v_acct AND HOLD_QTY > 0;

    /* 포지션 상세 */
    JG_POS_01(v_acct, "STK", NULL);

    out->gross_exposure = v_long_amt;
    out->net_exposure = v_long_amt - v_short_amt;

    /* 한도 대비 사용률 */
    EXEC SQL SELECT LIMIT_AMT INTO :out->limit_amt
        FROM TB_LIMIT_MST
        WHERE LIMIT_TP = 'EXPOSURE' AND LIMIT_CD = :v_acct;

    out->usage_rate = (out->limit_amt > 0) ?
        (out->gross_exposure / out->limit_amt * 100) : 0;

    /* 리스크 레벨 판정 */
    if (out->usage_rate >= 90)       strcpy(out->risk_level, "HI");
    else if (out->usage_rate >= 70)  strcpy(out->risk_level, "MD");
    else                             strcpy(out->risk_level, "LO");

    return SUCCESS;
}
""",
    "RM_VAR_01.pc": """\
/* VaR 리스크 계산 처리 - 포트폴리오 위험가치 산출, 역사적 변동성 기반 신뢰구간별 최대손실액 */
#include "proframe.h"
#include "rm_var_str.h"

EXEC SQL INCLUDE SQLCA;

int RM_VAR_01(rm_var_in_t *in, rm_var_out_t *out) {
    EXEC SQL BEGIN DECLARE SECTION;
    char    v_acct[11];
    double  v_portfolio_val;
    double  v_volatility;
    EXEC SQL END DECLARE SECTION;

    strcpy(v_acct, in->acct_no);

    /* 포트폴리오 가치 */
    JG_POS_01(v_acct, "STK", NULL);

    EXEC SQL SELECT NVL(SUM(EVAL_AMT),0) INTO :v_portfolio_val
        FROM TB_STK_BAL WHERE ACCT_NO = :v_acct;
    out->portfolio_val = v_portfolio_val;

    /* 역사적 변동성 (20일 기준) */
    EXEC SQL SELECT NVL(STDDEV(CHG_RATE),0.02) INTO :v_volatility
        FROM (
            SELECT CHG_RATE FROM TB_STK_PRICE_HIST
            WHERE STK_CD IN (SELECT STK_CD FROM TB_STK_BAL WHERE ACCT_NO = :v_acct)
            ORDER BY BASE_DT DESC
            FETCH FIRST 20 ROWS ONLY
        );

    /* VaR = Portfolio × Volatility × Z-score × sqrt(holding period) */
    double z_score;
    if (in->conf_level == 99)      z_score = 2.326;
    else if (in->conf_level == 95) z_score = 1.645;
    else                           z_score = 1.282;

    out->var_amt = v_portfolio_val * v_volatility * z_score *
                   sqrt((double)in->hold_period);
    out->var_rate = (v_portfolio_val > 0) ?
        (out->var_amt / v_portfolio_val * 100) : 0;

    /* CVaR (Expected Shortfall) ≈ VaR × 1.25 */
    out->cvar_amt = out->var_amt * 1.25;

    return SUCCESS;
}
""",
    "RM_STRESS_01.pc": """\
/* 스트레스 테스트 처리 - 시장 급락 시나리오 극단적 손실 추정, VaR 대비 경고 알림 */
#include "proframe.h"
#include "rm_var_str.h"

EXEC SQL INCLUDE SQLCA;

int RM_STRESS_01(const char *acct_no, double shock_rate, double *stress_loss) {
    /* 정상 VaR 산출 */
    rm_var_in_t var_in;
    rm_var_out_t var_out;
    strcpy(var_in.acct_no, acct_no);
    strcpy(var_in.method, "HIST");
    var_in.conf_level = 99;
    var_in.hold_period = 10;  /* 10일 */

    RM_VAR_01(&var_in, &var_out);

    /* 스트레스 시나리오: 지수 shock_rate% 급락 시 */
    *stress_loss = var_out.portfolio_val * (shock_rate / 100.0);

    /* 극단적 손실이 VaR의 3배 초과 시 경고 */
    if (*stress_loss > var_out.var_amt * 3) {
        CM_NOTIFY_01("RISK_MGR", "STRESS", "극단적 손실 경고");
    }

    return SUCCESS;
}
""",
    "RM_CREDIT_01.pc": """\
/* 신용리스크 평가 처리 - 대출잔액 대비 담보가치 비율 산출, 신용 위험도 평가 */
#include "proframe.h"

EXEC SQL INCLUDE SQLCA;

int RM_CREDIT_01(const char *acct_no, double *credit_score) {
    EXEC SQL BEGIN DECLARE SECTION;
    char    v_acct[11];
    double  v_loan_bal;
    double  v_coll_val;
    int     v_overdue_cnt;
    EXEC SQL END DECLARE SECTION;

    strcpy(v_acct, acct_no);

    /* 대출 잔액 */
    EXEC SQL SELECT NVL(SUM(LOAN_BAL),0) INTO :v_loan_bal
        FROM TB_LOAN_MST
        WHERE ACCT_NO = :v_acct AND LOAN_ST IN ('01','02');

    /* 담보 가치 */
    JG_POS_01(v_acct, "STK", NULL);
    EXEC SQL SELECT NVL(SUM(EVAL_AMT),0) INTO :v_coll_val
        FROM TB_STK_BAL WHERE ACCT_NO = :v_acct;

    /* 담보비율 = 담보가치 / 대출잔액 */
    if (v_loan_bal > 0) {
        *credit_score = v_coll_val / v_loan_bal * 100;
    } else {
        *credit_score = 999;  /* 대출 없음 */
    }

    return SUCCESS;
}
""",
    "RM_LIMIT_01.pc": """\
/* 리스크 한도 관리 배치 처리 - 전 계좌 한도 사용률 점검, 경고 초과 시 알림 및 익스포저 재산출 */
#include "proframe.h"

EXEC SQL INCLUDE SQLCA;

int RM_LIMIT_01(const char *base_dt) {
    EXEC SQL BEGIN DECLARE SECTION;
    char    v_dt[9];
    char    v_acct[11];
    double  v_usage;
    double  v_warn;
    EXEC SQL END DECLARE SECTION;

    strcpy(v_dt, base_dt);

    /* 모든 한도 항목 순회 */
    EXEC SQL DECLARE c_limit CURSOR FOR
        SELECT LIMIT_CD, USED_AMT / LIMIT_AMT * 100, WARN_RATE
        FROM TB_LIMIT_MST
        WHERE USE_YN = 'Y' AND LIMIT_AMT > 0;

    EXEC SQL OPEN c_limit;

    while (1) {
        EXEC SQL FETCH c_limit INTO :v_acct, :v_usage, :v_warn;
        if (SQLCA.sqlcode != 0) break;

        if (v_usage >= v_warn) {
            /* 경고 한도 초과 → 알림 */
            CM_NOTIFY_01("RISK_MGR", "LIMIT_WARN", "한도경고");

            /* 익스포저 재산출 */
            rm_exposure_in_t exp_in;
            rm_exposure_out_t exp_out;
            strcpy(exp_in.acct_no, v_acct);
            RM_EXPOSURE_01(&exp_in, &exp_out);
        }
    }

    EXEC SQL CLOSE c_limit;
    return SUCCESS;
}
""",

    # ========== Interface (IF) ==========
    "IF_KRX_01.pc": """\
/* 거래소 KRX 주문 인터페이스 처리 - FIX 프로토콜 주문 전문 조립 및 전송 */
#include "proframe.h"
#include "if_krx_str.h"

EXEC SQL INCLUDE SQLCA;

int IF_KRX_01(if_krx_in_t *in, if_krx_out_t *out) {
    EXEC SQL BEGIN DECLARE SECTION;
    char    v_msg[512];
    char    v_resp[512];
    EXEC SQL END DECLARE SECTION;

    /* 전문 조립 (FIX Protocol) */
    /* 35=D (New Order), 54=1(Buy)/2(Sell), 55=STK_CD, 44=Price, 38=Qty */

    /* 전문 전송 및 응답 수신 */
    EXEC SQL INSERT INTO TB_TX_HIST
        (TX_NO, TX_DT, TX_TM, SVC_NM, TX_TP, TX_DESC)
        VALUES (SQ_TX_NO.NEXTVAL, TO_CHAR(SYSDATE,'YYYYMMDD'),
                TO_CHAR(SYSDATE,'HH24MISS'), 'IF_KRX_01', 'KRX_SEND',
                'KRX 주문전송');

    CM_LOG_01("IF_KRX_01", "", "KRX전문전송");
    return SUCCESS;
}
""",
    "IF_KSD_01.pc": """\
/* 예탁원 KSD SAFE+ 인터페이스 처리 - 설정 환매 결제 전문 전송 및 상태 갱신 */
#include "proframe.h"
#include "if_ksd_str.h"

EXEC SQL INCLUDE SQLCA;

int IF_KSD_01(if_ksd_in_t *in, if_ksd_out_t *out) {
    EXEC SQL BEGIN DECLARE SECTION;
    char    v_msg[512];
    EXEC SQL END DECLARE SECTION;

    /* KSD SAFE+ 전문 전송 */
    EXEC SQL UPDATE TB_KSD_IF
        SET SEND_ST = '01'
        WHERE SEND_ST = '00'
        AND IF_DT = TO_CHAR(SYSDATE,'YYYYMMDD');

    CM_LOG_01("IF_KSD_01", "", "KSD전문전송");
    return SUCCESS;
}
""",
    "IF_BANK_01.pc": """\
/* 은행 인터페이스 처리 - 실시간 계좌 이체 전문 생성, 계좌번호 암호화 전송 */
#include "proframe.h"

EXEC SQL INCLUDE SQLCA;

int IF_BANK_01(const char *from_bank, const char *to_bank,
               const char *acct_no, double amt) {
    EXEC SQL BEGIN DECLARE SECTION;
    char    v_acct[11];
    char    v_enc_acct[65];
    EXEC SQL END DECLARE SECTION;

    strcpy(v_acct, acct_no);

    /* 계좌번호 암호화 */
    CM_CRYPTO_01(v_acct, v_enc_acct, "ENC");

    /* 은행 연동 전문 생성 */
    EXEC SQL INSERT INTO TB_TX_HIST
        (TX_NO, TX_DT, TX_TM, SVC_NM, ACCT_NO, TX_TP, TX_AMT, TX_DESC)
        VALUES (SQ_TX_NO.NEXTVAL, TO_CHAR(SYSDATE,'YYYYMMDD'),
                TO_CHAR(SYSDATE,'HH24MISS'), 'IF_BANK_01',
                :v_acct, 'BANK_XFER', :amt, '은행이체');

    CM_LOG_01("IF_BANK_01", v_acct, "은행이체");
    return SUCCESS;
}
""",
    "IF_TAX_01.pc": """\
/* 국세청 신고 인터페이스 처리 - 연간 세금 집계 및 국세청 전문 생성 전송 */
#include "proframe.h"

EXEC SQL INCLUDE SQLCA;

int IF_TAX_01(const char *report_tp, const char *base_year) {
    EXEC SQL BEGIN DECLARE SECTION;
    char    v_tp[5];
    char    v_year[5];
    double  v_total_tax;
    int     v_cnt;
    EXEC SQL END DECLARE SECTION;

    strcpy(v_tp, report_tp);
    strcpy(v_year, base_year);

    /* 연간 세금 집계 */
    EXEC SQL SELECT COUNT(*), NVL(SUM(TX_AMT),0)
        INTO :v_cnt, :v_total_tax
        FROM TB_TX_HIST
        WHERE TX_TP LIKE 'TAX%'
        AND TX_DT LIKE :v_year || '%';

    /* 국세청 전문 생성 */
    EXEC SQL INSERT INTO TB_TX_HIST
        (TX_NO, TX_DT, SVC_NM, TX_TP, TX_AMT, TX_DESC)
        VALUES (SQ_TX_NO.NEXTVAL, TO_CHAR(SYSDATE,'YYYYMMDD'),
                'IF_TAX_01', 'NTS_REPORT', :v_total_tax, '국세청신고');

    CM_LOG_01("IF_TAX_01", "BATCH", "국세청신고");
    return SUCCESS;
}
""",
    "IF_SWIFT_01.pc": """\
/* SWIFT 해외 송금 인터페이스 처리 - 환율 조회, 송금 한도 확인, 전문 암호화 전송 */
#include "proframe.h"

EXEC SQL INCLUDE SQLCA;

int IF_SWIFT_01(const char *acct_no, const char *swift_cd,
                double amt, const char *cur_cd) {
    EXEC SQL BEGIN DECLARE SECTION;
    char    v_acct[11];
    char    v_swift[12];
    double  v_fx_rate;
    double  v_krw_amt;
    EXEC SQL END DECLARE SECTION;

    strcpy(v_acct, acct_no);
    strcpy(v_swift, swift_cd);

    /* 환율 조회 */
    CM_RATE_01("FX", "", &v_fx_rate);
    v_krw_amt = amt * v_fx_rate;

    /* 송금 한도 확인 */
    if (CM_LIMIT_CHK("SWIFT", v_acct, v_krw_amt) != SUCCESS) {
        return FAIL;
    }

    /* SWIFT 전문 암호화 */
    char enc_msg[256];
    CM_CRYPTO_01(v_swift, enc_msg, "ENC");

    /* 전문 전송 기록 */
    EXEC SQL INSERT INTO TB_TX_HIST
        (TX_NO, TX_DT, TX_TM, SVC_NM, ACCT_NO, TX_TP, TX_AMT, TX_DESC)
        VALUES (SQ_TX_NO.NEXTVAL, TO_CHAR(SYSDATE,'YYYYMMDD'),
                TO_CHAR(SYSDATE,'HH24MISS'), 'IF_SWIFT_01',
                :v_acct, 'SWIFT', :v_krw_amt, 'SWIFT해외송금');

    CM_LOG_01("IF_SWIFT_01", v_acct, "SWIFT송금");
    return SUCCESS;
}
""",

    # ========== Loan (LN) ==========
    "LN_CREDIT_01.pc": """\
/* 신용 대출 실행 처리 - 대출 한도 체크, 금리 조회, 대출 원장 등록, 대출금 입금 */
#include "proframe.h"
#include "ln_credit_str.h"

EXEC SQL INCLUDE SQLCA;

int LN_CREDIT_01(ln_credit_in_t *in, ln_credit_out_t *out) {
    EXEC SQL BEGIN DECLARE SECTION;
    char    v_acct[11];
    double  v_int_rate;
    char    v_due_dt[9];
    EXEC SQL END DECLARE SECTION;

    strcpy(v_acct, in->acct_no);

    /* 대출 한도 체크 */
    if (CM_LIMIT_CHK("LOAN", v_acct, in->loan_amt) != SUCCESS) {
        strcpy(out->err_cd, "EA01");
        strcpy(out->err_msg, "대출한도 초과");
        return FAIL;
    }

    /* 금리 조회 */
    CM_RATE_01("LOAN_BASE", "", &v_int_rate);
    v_int_rate += 0.015;  /* 가산금리 1.5% */
    out->int_rate = v_int_rate;

    /* 만기일 계산 */
    EXEC SQL SELECT TO_CHAR(SYSDATE + :in->loan_days, 'YYYYMMDD')
        INTO :v_due_dt FROM DUAL;
    strcpy(out->due_dt, v_due_dt);

    /* 대출 원장 등록 */
    EXEC SQL INSERT INTO TB_LOAN_MST
        (LOAN_NO, ACCT_NO, LOAN_TP, LOAN_AMT, LOAN_BAL, INT_RATE,
         LOAN_DT, DUE_DT, LOAN_ST, COLL_TP)
        VALUES (SQ_LOAN.NEXTVAL, :v_acct, :in->loan_tp,
                :in->loan_amt, :in->loan_amt, :v_int_rate,
                TO_CHAR(SYSDATE,'YYYYMMDD'), :v_due_dt, '01', :in->coll_tp);

    /* 대출금 입금 */
    EXEC SQL UPDATE TB_ACCT_BAL
        SET CASH_BAL = CASH_BAL + :in->loan_amt,
            LOAN_AMT = LOAN_AMT + :in->loan_amt
        WHERE ACCT_NO = :v_acct;

    out->approved_amt = in->loan_amt;

    CM_LOG_01("LN_CREDIT_01", v_acct, "신용대출실행");
    return SUCCESS;
}
""",
    "LN_MARGIN_01.pc": """\
/* 담보 대출 처리 - 주식 담보 가치 평가, 담보비율 산정, 대출 실행 */
#include "proframe.h"

EXEC SQL INCLUDE SQLCA;

int LN_MARGIN_01(const char *acct_no, double req_amt) {
    EXEC SQL BEGIN DECLARE SECTION;
    char    v_acct[11];
    double  v_coll_val;
    double  v_max_loan;
    EXEC SQL END DECLARE SECTION;

    strcpy(v_acct, acct_no);

    /* 담보 가치 평가 */
    jg_asset_in_t asset_in;
    jg_asset_out_t asset_out;
    strcpy(asset_in.acct_no, v_acct);
    JG_ASSET_01(&asset_in, &asset_out);

    v_coll_val = asset_out.stk_eval;
    v_max_loan = v_coll_val * 0.5;  /* 담보비율 50% */

    if (req_amt > v_max_loan) {
        return FAIL;  /* 담보 부족 */
    }

    /* 대출 실행 */
    ln_credit_in_t ln_in;
    ln_credit_out_t ln_out;
    strcpy(ln_in.acct_no, v_acct);
    strcpy(ln_in.loan_tp, "MRGN");
    ln_in.loan_amt = req_amt;
    strcpy(ln_in.coll_tp, "STK");
    LN_CREDIT_01(&ln_in, &ln_out);

    CM_LOG_01("LN_MARGIN_01", v_acct, "담보대출");
    return SUCCESS;
}
""",
    "LN_INTEREST_01.pc": """\
/* 대출 이자 징수 배치 처리 - 대출 잔액 기준 일할 이자 계산 및 이자 출금 */
#include "proframe.h"

EXEC SQL INCLUDE SQLCA;

int LN_INTEREST_01(const char *base_dt) {
    EXEC SQL BEGIN DECLARE SECTION;
    char    v_dt[9];
    long    v_loan_no;
    char    v_acct[11];
    double  v_loan_bal;
    double  v_int_rate;
    double  v_daily_int;
    EXEC SQL END DECLARE SECTION;

    strcpy(v_dt, base_dt);

    EXEC SQL DECLARE c_loan CURSOR FOR
        SELECT LOAN_NO, ACCT_NO, LOAN_BAL, INT_RATE
        FROM TB_LOAN_MST
        WHERE LOAN_ST = '01' AND LOAN_BAL > 0;

    EXEC SQL OPEN c_loan;

    while (1) {
        EXEC SQL FETCH c_loan
            INTO :v_loan_no, :v_acct, :v_loan_bal, :v_int_rate;
        if (SQLCA.sqlcode != 0) break;

        /* 일할 이자 = 잔액 × 이율 / 365 */
        /* 영업일만 계산 */
        int biz_day = CM_DATE_CHK(v_dt, v_dt);
        v_daily_int = v_loan_bal * v_int_rate / 365.0;

        /* 이자 출금 */
        CM_TRANSFER_01(v_acct, "LOAN_INT_ACCT", v_daily_int);
    }

    EXEC SQL CLOSE c_loan;
    return SUCCESS;
}
""",
    "LN_REPAY_01.pc": """\
/* 대출 상환 처리 - 전액 일부 이자만 상환, 미납이자 계산, 잔액 갱신, 상환금 출금 */
#include "proframe.h"
#include "ln_repay_str.h"

EXEC SQL INCLUDE SQLCA;

int LN_REPAY_01(ln_repay_in_t *in, ln_repay_out_t *out) {
    EXEC SQL BEGIN DECLARE SECTION;
    long    v_loan_no;
    char    v_acct[11];
    double  v_loan_bal;
    double  v_int_rate;
    char    v_loan_dt[9];
    EXEC SQL END DECLARE SECTION;

    v_loan_no = in->loan_no;
    strcpy(v_acct, in->acct_no);

    EXEC SQL SELECT LOAN_BAL, INT_RATE, LOAN_DT
        INTO :v_loan_bal, :v_int_rate, :v_loan_dt
        FROM TB_LOAN_MST
        WHERE LOAN_NO = :v_loan_no AND ACCT_NO = :v_acct;

    /* 미납 이자 계산 */
    char today[9];
    EXEC SQL SELECT TO_CHAR(SYSDATE,'YYYYMMDD') INTO :today FROM DUAL;
    int days = CM_DATE_CHK(v_loan_dt, today);
    out->interest = v_loan_bal * v_int_rate * days / 365.0;

    if (strcmp(in->repay_tp, "01") == 0) {
        /* 전액 상환 */
        out->principal = v_loan_bal;
    } else if (strcmp(in->repay_tp, "03") == 0) {
        /* 이자만 */
        out->principal = 0;
    } else {
        /* 일부 상환 */
        out->principal = in->repay_amt;
    }

    out->total_repay = out->principal + out->interest;
    out->remain_bal = v_loan_bal - out->principal;

    /* 상환금 출금 */
    CM_TRANSFER_01(v_acct, "LOAN_REPAY_ACCT", out->total_repay);

    /* 대출 원장 갱신 */
    EXEC SQL UPDATE TB_LOAN_MST
        SET LOAN_BAL = :out->remain_bal,
            LOAN_ST = CASE WHEN :out->remain_bal = 0 THEN '09' ELSE LOAN_ST END
        WHERE LOAN_NO = :v_loan_no;

    CM_LOG_01("LN_REPAY_01", v_acct, "대출상환");
    return SUCCESS;
}
""",
    "LN_FORCED_01.pc": """\
/* 반대매매 강제매도 처리 - 담보비율 미달 시 보유 주식 강제 시장가 매도 및 고객 알림 */
#include "proframe.h"
#include "st_sell_str.h"

EXEC SQL INCLUDE SQLCA;

int LN_FORCED_01(const char *acct_no) {
    EXEC SQL BEGIN DECLARE SECTION;
    char    v_acct[11];
    double  v_loan_bal;
    double  v_coll_val;
    char    v_stk_cd[7];
    long    v_hold_qty;
    double  v_cur_price;
    EXEC SQL END DECLARE SECTION;

    strcpy(v_acct, acct_no);

    /* 대출 잔액 */
    EXEC SQL SELECT NVL(SUM(LOAN_BAL),0) INTO :v_loan_bal
        FROM TB_LOAN_MST
        WHERE ACCT_NO = :v_acct AND LOAN_ST = '01';

    /* 담보 가치 */
    EXEC SQL SELECT NVL(SUM(EVAL_AMT),0) INTO :v_coll_val
        FROM TB_STK_BAL WHERE ACCT_NO = :v_acct;

    /* 담보비율 140% 미만 시 반대매매 */
    if (v_loan_bal > 0 && (v_coll_val / v_loan_bal * 100) < 140) {
        /* 보유 종목 중 시가총액 큰 순서로 매도 */
        EXEC SQL DECLARE c_forced CURSOR FOR
            SELECT STK_CD, HOLD_QTY FROM TB_STK_BAL
            WHERE ACCT_NO = :v_acct AND HOLD_QTY > 0
            ORDER BY EVAL_AMT DESC;

        EXEC SQL OPEN c_forced;

        while (v_coll_val / v_loan_bal * 100 < 140) {
            EXEC SQL FETCH c_forced INTO :v_stk_cd, :v_hold_qty;
            if (SQLCA.sqlcode != 0) break;

            /* 시장가 매도 */
            st_sell_in_t sell_in;
            st_sell_out_t sell_out;
            strcpy(sell_in.acct_no, v_acct);
            strcpy(sell_in.stk_cd, v_stk_cd);
            sell_in.qty = v_hold_qty;
            sell_in.price = 0;  /* 시장가 */
            ST_SELL_01(&sell_in, &sell_out);

            v_coll_val -= sell_out.est_proceeds;
        }

        EXEC SQL CLOSE c_forced;

        /* 고객 알림 */
        CM_NOTIFY_01(v_acct, "FORCED_SELL", "반대매매 실행 안내");
    }

    CM_LOG_01("LN_FORCED_01", v_acct, "반대매매");
    return SUCCESS;
}
""",
}


# ============================================================
# 4. GENERATION LOGIC
# ============================================================

def generate():
    """모든 파일을 data/large_codebase/에 생성."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # 기존 파일 삭제
    for f in OUTPUT_DIR.iterdir():
        if f.is_file():
            f.unlink()

    # DDL 파일
    for name, content in TABLES.items():
        (OUTPUT_DIR / name).write_text(content, encoding="utf-8")
    print(f"  DDL files: {len(TABLES)}")

    # Header 파일
    for name, content in HEADERS.items():
        (OUTPUT_DIR / name).write_text(content, encoding="utf-8")
    print(f"  Header files: {len(HEADERS)}")

    # Pro*C 파일
    for name, content in FUNCTIONS.items():
        (OUTPUT_DIR / name).write_text(content, encoding="utf-8")
    print(f"  Pro*C files: {len(FUNCTIONS)}")

    total = len(TABLES) + len(HEADERS) + len(FUNCTIONS)
    print(f"\n  Total: {total} files in {OUTPUT_DIR}")


if __name__ == "__main__":
    print("=" * 60)
    print("  Generating large-scale Pro*C codebase")
    print("=" * 60)
    generate()
    print("  Done!")
