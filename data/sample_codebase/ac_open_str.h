/* 계좌 개설 전문 구조체 */
typedef struct {
    char cust_no[10];
    char ci_no[64];
    char acct_type[2];   /* 01:위탁 02:CMA 03:연금 */
    char brnch_cd[4];
} ac_open_in_t;

typedef struct {
    char acct_no[11];
    int  kyc_result;
    char err_cd[5];
    char err_msg[100];
} ac_open_out_t;
