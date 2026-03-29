/* 대출 상환 전문 구조체 */
typedef struct {
    long loan_no;
    char acct_no[11];
    double repay_amt;
    char repay_tp[3];   /* 01:전액 02:일부 03:이자만 */
} ln_repay_in_t;

typedef struct {
    double principal;
    double interest;
    double total_repay;
    double remain_bal;
    char err_cd[5];
    char err_msg[101];
} ln_repay_out_t;
