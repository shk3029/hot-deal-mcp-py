# hot-deal-mcp-py

하나의 소스에서 `CARD_DATA_SOURCE=mock|mci` 환경변수로 목업 데이터와 실제 MCI를
선택합니다. 기본값은 실제 `mci`이며, 목업은 `CARD_DATA_SOURCE=mock`을 명시할 때만
사용합니다.

신한카드 상품 안내 MCP 서버. 공식 `mcp` SDK(FastMCP)로 Tool 을 정의하고,
streamable-HTTP ASGI 앱을 **FastAPI** 에 마운트해 `/mcp` 로 제공합니다.

툴은 사내 스타일(`register_*_tools(mcp)` + `@mcp.tool(tags=..., meta=...)`)로 작성돼
있고, 카드 데이터는 선택된 클라이언트의 `call_with_itf_id("EGN00001", ...)` 로
조회합니다. 각 툴 결과 모델
**최상위에 `widget` / `copy_text` (카카오툴즈 응답)** 이 실려 카카오 쪽에서 바로 렌더됩니다.

## MCP Tool (4종)

| Tool | tool_code | 설명 |
| --- | --- | --- |
| `getCreditCardRecommendationsWithSelector` | TL-COMM-004 | `industry` · `annualFee` · `cardType` · `sort`로 신한카드 추천. 업종이나 연회비가 불명확하면 선택 위젯 반환 |
| `getCreditCardDetail` | TL-COMM-005 | `cardName` enum으로 카드 한 장 상세. 못 찾으면 카드명 되묻기 위젯 |
| `getPopularCreditCards` | TL-COMM-006 | 파라미터 없이 인기 TOP5 |
| `getFinancialLifeKnowledgeArticles` | TL-COMM-007 | 금융생활지식 콘텐츠 (`category`: `트렌드` / `금융` / `카드연구소`, 생략 시 `트렌드`) |

`getFinancialLifeKnowledgeArticles` 는 콘텐츠 목록이 코드에 내장돼 있어 MCI 호출이 없습니다. 나머지 3종은
`EGN00001` 을 호출합니다.

## 목업 데이터

- 소스: [`mci/mock_data.json`](mci/mock_data.json) (신한카드 검색 데이터 81건)
- [`mci/mock.py`](mci/mock.py) `MockBackend` 가 `data` 딕셔너리(`CRD_BNF`/`MSG`/`TAG_VL`
  + `AFE_*`/`SIZ`/`QEE`)로 필터·정렬해 `{"GRID1": [...], "TO_CT": n}` 반환
- `getCreditCardDetail` 의 `cardName` 은 지원 카드명 81종 enum과 정확히 일치
- `getPopularCreditCards` 는 고정 TOP5 (Deep Oil / Mr.Life / Air One / Point Plan / SOL트래블 체크)
- 설정 파일 불필요. 그냥 `./run.sh`

## 실행

외부망 또는 로컬 목업 실행:

```bash
CARD_DATA_SOURCE=mock ./run.sh
CARD_DATA_SOURCE=mock PORT=8081 ./run.sh
```

내부망 실제 MCI 실행:

```bash
SVC_CONFIG_DIR=/project/work/flow/config/dev \
./run.sh
```

`SVC_CONFIG_DIR`은 `mci_interfaces.yaml` 파일이 들어 있는 디렉터리입니다.
`CARD_DATA_SOURCE`를 생략하면 `mci`이며, 필요하면 `CARD_DATA_SOURCE=mci`를 명시해도
동일합니다. `mock`/`mci` 이외의 값은 시작 오류로 처리합니다.

직접:

```bash
.venv/bin/python -m uvicorn main:app --host 0.0.0.0 --port 8080
# 또는 전역 uv가 설치된 경우
uv run uvicorn main:app --host 0.0.0.0 --port 8080
uv run python server.py        # FastAPI 없이 FastMCP 단독 구동
```

## 구동 스모크 테스트

```bash
CARD_DATA_SOURCE=mci SVC_CONFIG_DIR=/path/to/config ./run.sh       # 터미널 1
.venv/bin/python scripts/smoke_test.py                              # 터미널 2
```

## 카카오툴즈 / ngrok

```bash
./run.sh              # 터미널 1
ngrok http 8080       # 터미널 2
```

카카오툴즈 등록 주소: `https://YOUR-NGROK-DOMAIN.ngrok-free.app/mcp`

## 구조

```
main.py                  FastAPI 진입점 (+ /mcp 마운트, /health)
server.py                FastMCP 인스턴스 + 툴 등록
mci/
  card_client.py         CARD_DATA_SOURCE 기반 mock/mci 클라이언트 팩토리
  mock_client.py         MockMciClient — 팩토리가 mock 모드에서 지연 로딩
  mock.py                MockBackend — mock_data.json → GRID1 응답
  mock_data.json         신한카드 검색 데이터 81건
  mci_client.py          실제 MCI 클라이언트 (CARD_DATA_SOURCE=mci에서만 로딩)
schemas/
  card_finder_tools_schemas.py   Card / CardDetail / CardsResult / CardDetailResult
  finance_tips_schemas.py        ContentItem / ContentResult
domain/                  Industry / AnnualFeeBand / CardSortOrder / CreditCardName
kakao/                   카카오툴즈 응답 빌더 (툴별 분리)
  common.py              응답 래퍼 / 셀렉터 버튼 / onClickAction 공용 조각
  card_finder.py         업종 셀렉터 + 카드 추천 목록
  card_search.py         카드명 되묻기 + 카드 상세
  popular_card.py        인기 TOP5 목록
  finance_tips.py        금융생활지식 목록
tools/
  __init__.py            REGISTER_TOOLS — 등록 함수 화이트리스트
  common.py              @mcp.tool 래퍼(tags→meta) + with_kakao 헬퍼
  card_finder_tools.py   getCreditCardRecommendationsWithSelector
  card_search_tools.py   getCreditCardDetail
  popular_card_tools.py  getPopularCreditCards
  finance_tips_tools.py  getFinancialLifeKnowledgeArticles
  finance_tips/          CATEGORY_MAP + 콘텐츠 enum
```

### 툴 켜고 끄기

`tools/__init__.py` 의 `REGISTER_TOOLS` 리스트에 있는 등록 함수만 서버에서 실행됩니다.
빼면 해당 툴은 `tools/list` 에도 노출되지 않습니다.

### GRID1 → 카카오 위젯 매핑

툴은 `EGN00001` 응답의 `GRID1` 배열을 `Card` / `CardDetail` (`schemas/`) 로 파싱한 뒤,
같은 데이터로 `kakao/` 빌더를 호출해 `widget` / `copy_text` 를 채웁니다. 기대하는 GRID1
필드: `CRD_PD_NM`, `CRD_PD_AFE`, `CRD_PD_IMG_URL`, `CRD_PD_URL`, `CRD_PD_BNF_CD`(콤마
구분 업종코드), `CRD_PD_BNF_NM1~3` / `CRD_PD_BNF_DL1~3`, `TAG_BST_VL` 등, 그리고 총건수
`TO_CT`. (이 브랜치에선 `MockBackend` 가 `mock_data.json` 으로 이 형태를 만들어 냅니다.)
