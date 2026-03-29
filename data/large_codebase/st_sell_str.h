/* 주식 매도 전문 구조체 */
typedef struct {
    char acct_no[11];
    char stk_cd[7];
    double price;
    long qty;
    char ord_type[3];
} st_sell_in_t;

typedef struct {
    long ord_no;
    double est_proceeds;
    double est_tax;
    char err_cd[5];
    char err_msg[101];
} st_sell_out_t;
