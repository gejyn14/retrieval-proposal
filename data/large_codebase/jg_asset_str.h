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
