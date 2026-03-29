/* 분배금 지급 전문 구조체 */
typedef struct {
    char acct_no[11];
    char fund_cd[12];
    char pay_dt[9];
    char acct_type[2];    /* 01:일반 02:연금 03:ISA */
    char dist_type[1];    /* C:현금 R:재투자 */
} fd_pay_in_t;

typedef struct {
    double gross_amt;
    double tax_amt;
    double net_amt;
    char ksd_ref_no[20];
    char err_cd[5];
    char err_msg[100];
} fd_pay_out_t;
