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
