/* 채권 매수 전문 구조체 */
typedef struct {
    char acct_no[11];
    char bnd_cd[13];
    double face_amt;
    double price;
    char buy_tp[3];
} bn_buy_in_t;

typedef struct {
    double buy_amt;
    double accrued_int;
    double total_amt;
    char err_cd[5];
    char err_msg[101];
} bn_buy_out_t;
