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
