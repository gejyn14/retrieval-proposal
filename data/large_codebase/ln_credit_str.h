/* 신용 대출 전문 구조체 */
typedef struct {
    char acct_no[11];
    char loan_tp[5];
    double loan_amt;
    int  loan_days;
    char coll_tp[5];
} ln_credit_in_t;

typedef struct {
    long loan_no;
    double approved_amt;
    double int_rate;
    char due_dt[9];
    char err_cd[5];
    char err_msg[101];
} ln_credit_out_t;
