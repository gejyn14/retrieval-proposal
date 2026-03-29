/* 계좌 해지 전문 구조체 */
typedef struct {
    char acct_no[11];
    char close_rsn[5];
    char auth_key[33];
} ac_close_in_t;

typedef struct {
    double refund_amt;
    char close_dt[9];
    char err_cd[5];
    char err_msg[101];
} ac_close_out_t;
