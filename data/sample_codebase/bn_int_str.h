/* 채권 이자 전문 구조체 */
typedef struct {
    char bond_cd[12];
    char lst_pay_dt[9];
    char calc_dt[9];
    double face_amt;
} bn_int_in_t;

typedef struct {
    double int_amt;
    double tax_amt;
    double net_int;
    char err_cd[5];
} bn_int_out_t;
