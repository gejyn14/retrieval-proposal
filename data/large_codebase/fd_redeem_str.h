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
