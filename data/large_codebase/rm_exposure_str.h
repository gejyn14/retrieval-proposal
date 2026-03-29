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
