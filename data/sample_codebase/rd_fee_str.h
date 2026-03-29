/* 환매 수수료 전문 구조체 */
typedef struct {
    char fund_cd[12];
    char buy_dt[9];
    char sell_dt[9];
    double sell_amt;
    long sell_qty;
} rd_fee_in_t;

typedef struct {
    double fee_amt;
    double tax_amt;
    double net_amt;
    char err_cd[5];
    char err_msg[100];
} rd_fee_out_t;
