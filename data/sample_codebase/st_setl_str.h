/* 결제(수도) 전문 구조체 */
typedef struct {
    char acct_no[11];
    char setl_dt[9];
    char stk_cd[7];
} st_setl_in_t;

typedef struct {
    long setl_qty;
    double setl_amt;
    char err_cd[5];
    char err_msg[100];
} st_setl_out_t;
