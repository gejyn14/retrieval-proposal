/* 예탁원(KSD) 인터페이스 전문 구조체 */
typedef struct {
    char msg_tp[5];
    char fund_cd[13];
    char acct_no[11];
    double qty;
    double amt;
} if_ksd_in_t;

typedef struct {
    char resp_cd[5];
    long ksd_ref_no;
    char proc_dt[9];
    char err_cd[5];
    char err_msg[101];
} if_ksd_out_t;
