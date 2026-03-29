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
