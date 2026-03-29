/* 이표 계산 전문 구조체 */
typedef struct {
    char bnd_cd[13];
    char from_dt[9];
    char to_dt[9];
    double face_amt;
} bn_coupon_in_t;

typedef struct {
    double coupon_amt;
    int  accrued_days;
    double accrued_int;
    char err_cd[5];
    char err_msg[101];
} bn_coupon_out_t;
