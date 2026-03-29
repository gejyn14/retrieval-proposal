/* 채권 만기 상환 전문 구조체 */
typedef struct {
    char acct_no[11];
    char bnd_cd[13];
} bn_mature_in_t;

typedef struct {
    double face_amt;
    double last_coupon;
    double tax_amt;
    double net_amt;
    char err_cd[5];
    char err_msg[101];
} bn_mature_out_t;
