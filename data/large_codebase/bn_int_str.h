/* 채권 이자 전문 구조체 */
typedef struct {
    char acct_no[11];
    char bnd_cd[13];
    char pay_dt[9];
} bn_int_in_t;

typedef struct {
    double gross_int;
    double tax_amt;
    double net_int;
    char err_cd[5];
    char err_msg[101];
} bn_int_out_t;
