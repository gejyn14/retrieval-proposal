/* 신용매수 전문 구조체 */
typedef struct {
    char acct_no[11];
    char stk_cd[7];
    double price;
    long qty;
    char credit_tp[3];
    int  credit_days;
} st_credit_in_t;

typedef struct {
    long ord_no;
    long loan_no;
    double loan_amt;
    double margin_amt;
    double int_rate;
    char err_cd[5];
    char err_msg[101];
} st_credit_out_t;
