/* 거래소(KRX) 인터페이스 전문 구조체 */
typedef struct {
    char msg_tp[5];
    char stk_cd[7];
    char ord_side[3];
    double price;
    long qty;
    long ord_no;
} if_krx_in_t;

typedef struct {
    char resp_cd[5];
    long krx_ord_no;
    char recv_tm[7];
    char err_cd[5];
    char err_msg[101];
} if_krx_out_t;
