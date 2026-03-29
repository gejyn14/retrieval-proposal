/* 계좌 개설 전문 구조체 */
typedef struct {
    char cust_no[11];
    char ci_no[65];
    char acct_type[3];
    char brnch_cd[5];
    char id_type[3];
    char id_no[21];
} ac_open_in_t;

typedef struct {
    char acct_no[11];
    int  kyc_result;
    char err_cd[5];
    char err_msg[101];
} ac_open_out_t;
