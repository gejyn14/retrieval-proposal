/* 주식 매수 전문 구조체 */
typedef struct {
    char acct_no[11];
    char stk_cd[7];
    double price;
    long qty;
    char ord_type[3];   /* 00:지정가 01:시장가 */
    char credit_tp[3];  /* 00:보통 01:신용 */
} st_buy_in_t;

typedef struct {
    long ord_no;
    double margin_amt;
    double order_amt;
    char err_cd[5];
    char err_msg[101];
} st_buy_out_t;
