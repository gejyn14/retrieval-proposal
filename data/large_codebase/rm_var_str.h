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
