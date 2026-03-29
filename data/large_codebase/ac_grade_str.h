/* 고객 등급 산정 전문 구조체 */
typedef struct {
    char cust_no[11];
    char base_dt[9];
} ac_grade_in_t;

typedef struct {
    char prev_grade[3];
    char new_grade[3];
    double total_asset;
    int  tx_count;
    char err_cd[5];
    char err_msg[101];
} ac_grade_out_t;
