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
