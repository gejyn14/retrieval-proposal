/* 주식 결제 전문 구조체 */
typedef struct {
    char setl_dt[9];
    char acct_no[11];
    long exec_no;
} st_setl_in_t;

typedef struct {
    double setl_amt;
    long setl_qty;
    char setl_st[3];
    char err_cd[5];
    char err_msg[101];
} st_setl_out_t;
