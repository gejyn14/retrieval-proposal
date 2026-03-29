# Pro*C/ProFrame 코드 Retrieval 시스템 아키텍처

## 1. 개요

증권사 TMax ProFrame + Pro*C + Oracle + SVN 환경의 레거시 코드베이스를 대상으로, Claude Code(또는 유사 AI 코딩 도구)가 코드를 이해하고 작업할 수 있도록 MCP(Model Context Protocol) 서버를 제공한다.

### 핵심 설계 원칙

- **구조 기반 검색**: 벡터 유사도(RAG)가 아닌, 파싱된 코드 구조(호출 그래프, 테이블 의존, 구조체)를 활용
- **MCP = 지도, Repo = 실제 코드**: MCP는 구조 정보(함수 관계, 테이블, 설명)만 제공하고, 실제 코드는 repo에서 직접 Read
- **On-demand 조회**: 배치 컨텍스트 주입 없이, 필요할 때 MCP tool 호출로 최소 토큰 사용

### 왜 벡터 RAG가 아닌 구조 기반인가

| | 벡터 RAG (Chunk) | 구조 기반 (Structural) |
|---|---|---|
| 방식 | 코드를 텍스트 조각으로 잘라 임베딩 | 파싱된 함수/호출/테이블 관계를 그래프 탐색 |
| Recall | 40% | **98%** |
| Noise | 22% | **0.6%** |
| Pro*C 적합성 | `tax_amt`, `acct_no` 등 공통 패턴이 노이즈 유발 | 호출 그래프 따라가므로 규모에 무관 |
| ProFrame 활용 | 구조화된 설정 정보를 무시하고 텍스트로 취급 | 서비스 등록/FDL/EXECUTE_SERVICE를 그대로 활용 |

---

## 2. 전체 아키텍처

```
                      Claude Code
                     /      |     \
                    /       |      \
                   /        |       \
         svn-bridge   proc-retrieval   Read/Edit (내장)
         (SVN 이력)   (구조 정보)       (실제 코드)
              |             |               |
              v             v               v
         SVN Server    structural.db     .pc/.h/.sql 파일
                       (구조만, 경량)     (repo 원본)
```

**2개 MCP + Claude Code 내장 도구**

| 역할 | 담당 | 반환 |
|------|------|------|
| 함수 검색, 호출 관계, 영향도 | proc-retrieval (SQLite) | 구조 정보 + **파일 경로** |
| 실제 코드 읽기/수정 | Claude Code 내장 Read/Edit | 파일 내용 |
| 커밋 이력, diff, blame | svn-bridge (SVN CLI) | 이력 정보 |

MCP는 코드 자체를 반환하지 않는다. **"어디를 봐야 하는지"를 알려주고, Claude Code가 직접 읽는다.**

---

## 3. MCP #1: proc-retrieval

**역할**: 코드 구조 검색 및 분석. "이 코드베이스의 지도."
**인프라**: SQLite (읽기 전용, WAL 모드)
**파일**: `src/mcp_server/server.py`

### 3.1 SQLite에 저장하는 것 (구조만)

| 테이블 | 내용 | 코드 body 포함? |
|--------|------|:-:|
| `functions` | name, description, file_path, tables_used, includes | 검색용으로만 (반환 안 함) |
| `function_calls` | caller → callee 관계 | - |
| `sql_usage` | function → table + operation (SELECT/INSERT/UPDATE/DELETE) | - |
| `structs` | name, file_path, fields | - |
| `tables_ddl` | name, columns, primary_key, comment | - |
| `functions_fts` | FTS5 전문 검색 인덱스 (description + body) | 검색용 |

body는 키워드 검색을 위해 SQLite에 저장하되, **MCP 응답에는 포함하지 않는다.** 대신 파일 경로를 반환하고 Claude Code가 Read로 직접 읽는다.

### 3.2 MCP가 반환하는 것 vs Claude Code가 직접 읽는 것

```
개발자: "RD_FEE_03 수정하려는데 영향도 봐줘"

1. Claude Code → proc-retrieval.get_function("RD_FEE_03")
   반환:
     name: RD_FEE_03
     description: "수익증권 환매 수수료 계산 처리 - ..."
     file_path: RD_FEE_03.pc          ← 파일 경로
     call_graph: → CM_DATE_CHK, CM_TAX_01
     called_by: ← FD_REDEEM_01, RD_PROC_01
     tables: TB_FEE_RATE (SELECT)
     struct_files: [rd_fee_str.h]     ← 파일 경로
     dependency_files: [CM_DATE_CHK.pc, CM_TAX_01.pc]  ← 파일 경로

2. Claude Code가 필요한 파일만 읽기:
   Read("RD_FEE_03.pc")              ← 로컬에 있으면 직접 Read
   svn_cat("RD_FEE_03.pc")           ← 로컬에 없으면 SVN 서버에서 읽기
3. Claude Code → Read("rd_fee_str.h")    ← 필요시만
4. Claude Code → proc-retrieval.get_impact("RD_FEE_03")
```

**장점:**
- MCP 응답이 가벼움 (수백 토큰 vs 수천 토큰)
- 코드가 항상 최신 (repo에서 직접 읽으니까)
- SQLite 인덱싱이 빠름 (body 변경은 재인덱싱 불필요, 호출 관계 변경 시만)
- DB 크기 작음 (5000함수여도 수 MB)

### 3.3 검색 알고리즘 (search_code)

```
"환매 수수료 계산" 입력

1단계: 키워드 매칭
   → functions 테이블에서 description(×3) + body(×1) 점수 산출
   → 최고 점수 함수 선택: RD_FEE_03

2단계: 구조 정보 수집
   → 호출 그래프: RD_FEE_03 → CM_DATE_CHK, CM_TAX_01
   → 테이블: TB_FEE_RATE (SELECT)
   → 구조체: rd_fee_str.h
   → 파일 경로 목록 반환 (코드 자체는 안 보냄)
```

### 3.4 Tools (10개)

**코드 탐색**

| Tool | 시그니처 | 반환 |
|------|----------|------|
| `search_code` | `(query: str)` | 매칭 함수 + 호출 그래프 + 관련 파일 경로 목록 |
| `get_function` | `(name: str)` | 함수 메타데이터 + 호출 관계 + 의존 파일 경로 |
| `get_call_graph` | `(name: str, depth: int)` | 순방향 호출 트리 |
| `list_services` | `()` | 전체 함수 목록 (이름 + 설명) |
| `search_by_domain` | `(domain: str)` | 도메인별 함수/테이블/구조체 목록 |

**영향도 분석**

| Tool | 시그니처 | 반환 |
|------|----------|------|
| `get_impact` | `(name: str, depth: int)` | 역방향 재귀 → depth별 영향 서비스 목록 |
| `find_by_table` | `(table_name: str)` | DDL + 사용 함수 (CRUD별) |

**업무 흐름**

| Tool | 시그니처 | 반환 |
|------|----------|------|
| `get_business_flow` | `(entry_function: str, depth: int)` | 호출 트리 + 각 단계 SQL 연산 |

**디버깅**

| Tool | 시그니처 | 반환 |
|------|----------|------|
| `find_by_error_code` | `(error_code: str)` | 에러 설정 함수 + 메시지 + 파일 경로 |

### 3.5 각 Tool 동작 상세

**search_code** — "이 업무 어디서 처리하지?"
```
입력: "환매 수수료 계산"
반환: { matched: "RD_FEE_03", description, call_graph, tables, related_files: [...경로] }
Claude Code: 필요한 파일만 Read
```

**get_function** — "이 함수 상세 보여줘"
```
입력: "RD_FEE_03"
반환: { name, description, file_path, call_graph, tables, struct_files, dependency_files }
Claude Code: file_path로 Read하여 실제 코드 확인
```

**get_impact** — "이거 바꾸면 어디가 깨지나?"
```
입력: "CM_TAX_01" (함수) 또는 "TB_FEE_RATE" (테이블)
반환: depth별 영향 서비스 목록 (이름 + 설명)
  depth 1: BN_INT_05, DV_PAY_01, RD_FEE_03 등 9개 직접 호출자
  depth 2: FD_PAY_01, FD_SWITCH_01 등 7개 간접 호출자
```

**get_business_flow** — "이 프로세스 전체 흐름 보여줘"
```
입력: "FD_PAY_01"
반환:
  FD_PAY_01 — 분배금 지급
    [SELECT TB_FUND_DIST, SELECT TB_FND_BAL]
    FD_TAX_02 — 과세
      [SELECT TB_TAX_MST]
    FD_KSD_IF_01 — KSD 연동
      [INSERT TB_KSD_IF]
  Tables touched: TB_FUND_DIST, TB_FND_BAL, TB_TAX_MST, TB_KSD_IF
```
get_call_graph와 차이: SQL 연산이 각 단계에 포함되어 "무엇이 실행되는지" 보임.

**find_by_error_code** — "이 에러 어디서 나는 거야?"
```
입력: "E101"
반환: ST_BUY_01 (file_path) — "주문가능금액 부족"
Claude Code: Read("ST_BUY_01.pc")로 실제 에러 처리 코드 확인
```

---

## 4. MCP #2: svn-bridge

**역할**: Claude Code에 없는 SVN 이력 조회 기능 제공. 읽기 전용.
**인프라**: SVN CLI (`svn` 명령어), SVN working copy
**파일**: `src/mcp_svn/server.py`

### 4.1 Tools (5개)

| Tool | 시그니처 | 용도 |
|------|----------|------|
| `svn_cat` | `(path, revision)` | **SVN 서버에서 파일 내용 읽기 (로컬에 없는 파일도 가능)** |
| `svn_log` | `(path, limit, author, date_from, date_to)` | 커밋 이력 조회 |
| `svn_diff` | `(path, revision)` | 변경 내용 (unified diff) |
| `svn_blame` | `(path, line_start, line_end)` | 라인별 작성자/리비전 |
| `svn_status` | `(path)` | 현재 작업 변경 사항 |

`svn_cat`이 핵심인 이유: 다른 팀의 코드는 로컬에 checkout되어 있지 않을 수 있다. proc-retrieval이 파일 경로를 반환했을 때, 로컬에 없으면 `svn_cat`으로 SVN 서버에서 직접 읽는다.

```
Claude Code의 판단:
  1. Read("src/RD_FEE_03.pc")          ← 로컬에 있으면 바로 읽기
  2. 없으면 → svn_cat("src/RD_FEE_03.pc")  ← SVN 서버에서 읽기
```

### 4.2 보안
- 모든 경로는 `SVN_WORKING_COPY` 기준, path traversal 방지
- 쓰기 작업(commit, update) 미지원 — 개발자가 직접 수행

---

## 5. 인덱싱

별도 MCP 없이 스크립트로 실행:

```bash
python scripts/index_all.py        # 전체 재인덱싱 (81함수 기준 0.01초)
python scripts/index_all.py large   # large_codebase 인덱싱
```

### 5.1 인덱싱 대상

```
ProFrame 서비스 설정  →  서비스명, 설명
FDL 정의 파일        →  입출력 구조체
.pc 파일             →  함수 시그니처, EXEC SQL, EXECUTE_SERVICE 호출
.h 파일              →  typedef struct
.sql 파일            →  CREATE TABLE, 컬럼, PK, COMMENT
```

### 5.2 언제 재인덱싱하나

| 상황 | 재인덱싱 필요? |
|------|:-:|
| 함수 코드(body) 수정 | **예** — body를 검색 키워드 매칭에 사용하므로 |
| 새 함수 추가 / 함수 삭제 | 예 |
| 호출 관계 변경 (새 EXECUTE_SERVICE 추가 등) | 예 |
| 테이블 DDL 변경 | 예 |
| 함수 설명(description) 변경 | 예 — 검색 품질에 영향 |

body도 검색 키워드 매칭에 사용하므로, **코드 수정 시에도 재인덱싱 필요.** 다만 `index_all.py` 실행이 수 초면 완료되므로 별도 MCP가 필요 없음.

---

## 6. 데이터 흐름

### 6.1 일반 작업 흐름

```
개발자: "RD_FEE_03 수정하려는데 영향도 봐줘"

Claude Code:
  1. get_function("RD_FEE_03")          ← proc-retrieval
     → 구조 정보 + 파일 경로 목록

  2. Read("RD_FEE_03.pc")               ← Claude Code 내장
     → 실제 코드

  3. get_impact("RD_FEE_03")            ← proc-retrieval
     → 18개 영향 서비스

  4. 코드 수정                           ← Claude Code Edit

  5. svn_diff("RD_FEE_03.pc")           ← svn-bridge
     → 변경 내용 확인
```

### 6.2 크로스 MCP 흐름

```
개발자: "어제 수정된 것 중 영향도 큰 거 알려줘"

Claude Code:
  1. svn_log(date_from="2026-03-28")    ← svn-bridge
     → r4521: ST_BUY_01.pc, ST_MARGIN_01.pc 변경

  2. get_impact("ST_BUY_01")            ← proc-retrieval
     → 7개 영향

  3. get_impact("ST_MARGIN_01")         ← proc-retrieval
     → 3개 영향

  4. Claude 종합: "ST_BUY_01 변경이 영향도 큽니다"
```

---

## 7. 개발자 시나리오 → Tool 매핑

| 질문 | Tool 호출 |
|------|-----------|
| "이 함수 코드 보여줘" | `get_function` → 경로 확인 → `Read` |
| "이 업무 어디서 처리하지?" | `search_code("환매 수수료")` |
| "이 함수 수정하면 영향 어디?" | `get_impact("CM_TAX_01")` |
| "이 테이블 누가 쓰지?" | `find_by_table("TB_ACCT_MST")` |
| "이 에러 어디서 나는 거야?" | `find_by_error_code("E101")` → `Read` |
| "이 배치 전체 흐름 보여줘" | `get_business_flow("FD_PAY_01")` |
| "ST 도메인 전체 보여줘" | `search_by_domain("ST")` |
| "어제 누가 뭘 바꿨어?" | `svn_log(date_from="...")` |
| "이 파일 변경 내용 보여줘" | `svn_diff("ST_BUY_01.pc")` |
| "이 줄 누가 작성했어?" | `svn_blame("ST_BUY_01.pc")` |

---

## 8. 프로젝트 구조

```
retrieval/
├── .mcp.json                          # MCP 서버 등록 (proc-retrieval, svn-bridge)
├── scripts/
│   └── index_all.py                   # 인덱싱 스크립트 (구조 변경 시 실행)
├── src/
│   ├── parser/
│   │   ├── proc_parser.py             # .pc/.h/.sql 파싱
│   │   └── schema.py                  # 데이터 모델
│   ├── indexer/
│   │   ├── db.py                      # SQLite 스키마 (WAL 모드)
│   │   └── structural_indexer.py      # 파싱 결과 → SQLite
│   ├── retrieval/
│   │   ├── structural_retrieval.py    # FTS5 매칭 + 그래프 탐색
│   │   └── service.py                 # MCP/API 공통 서비스 레이어
│   ├── mcp_server/
│   │   └── server.py                  # proc-retrieval MCP (10개 tool)
│   └── mcp_svn/
│       └── server.py                  # svn-bridge MCP (4개 tool)
├── data/
│   └── structural.db                  # SQLite 인덱스 (구조 정보만, 경량)
└── web/
    └── index.html                     # 웹 UI
```

---

## 9. 실전 도입 체크리스트

- [ ] ProFrame 실제 .pc 파일로 파서 검증 (파싱 실패 케이스 수정)
- [ ] 서비스 설명(description) 품질 확인 (ProFrame 등록 정보 활용)
- [ ] SVN_WORKING_COPY 경로 설정
- [ ] EXECUTE_SERVICE 패턴 파서 추가
- [ ] 인덱싱 실행 및 검색 정확도 확인

### 추후 확장
- 컬럼 레벨 SQL 사용 추적 (`get_table_schema` 고도화)
- FDL 파서 (ProFrame 서비스 정의 → 구조체 자동 추출)
- 함수 설명 임베딩 (키워드 매칭 fallback → 동의어 처리)

---

## 10. 검증 결과

128파일(81함수) 테스트 코드베이스에서 10개 시나리오 평가:

| 전략 | Precision | Recall | Noise | Completeness |
|------|:---------:|:------:|:-----:|:------------:|
| Chunk (벡터 RAG) | 34.0% | 40.0% | 22.0% | 52.5% |
| **Structural (채택)** | **40.7%** | **98.0%** | **0.6%** | **97.5%** |
