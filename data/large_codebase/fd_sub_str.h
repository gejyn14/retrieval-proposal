/* 펀드 가입(설정) 전문 구조체 */
typedef struct {
    char acct_no[11];
    char fund_cd[13];
    double invest_amt;
    char reinvest_yn[2];
} fd_sub_in_t;

typedef struct {
    double nav;
    double alloc_qty;
    double fee_amt;
    double net_invest;
    char err_cd[5];
    char err_msg[101];
} fd_sub_out_t;
