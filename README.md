# hot-deal-mcp-py  ·  `feature/mock` 브랜치

> **이 브랜치는 MCI 백엔드 없이 목업 데이터로 동작합니다.** 카카오툴즈에 바로 붙여
> 테스트하기 위한 것. 실제 MCI 연동은 `feature/mci-fetch-tools` 브랜치를 쓰세요.
> 두 브랜치 차이는 `mci/mock_client.py`·`mci/mock.py`·`mci/mock_data.json` 과
> 툴 3종의 import 한 줄뿐입니다.

신한카드 상품 안내 MCP 서버. 공식 `mcp` SDK(FastMCP)로 Tool 을 정의하고,
streamable-HTTP ASGI 앱을 **FastAPI** 에 마운트해 `/mcp` 로 제공합니다.

툴은 사내 스타일(`register_*_tools(mcp)` + `@mcp.tool(tags=..., meta=...)`)로 작성돼
있고, 카드 데이터는 `MciClient().call_with_itf_id("EGN00001", ...)` 로 조회합니다
(이 브랜치에서는 `mci/mock_data.json` 을 읽는 `MockMciClient`). 각 툴 결과 모델
**최상위에 `widget` / `copy_text` (카카오툴즈 응답)** 이 실려 카카오 쪽에서 바로 렌더됩니다.

## MCP Tool (4종)

| Tool | tool_code | 설명 |
| --- | --- | --- |
| `fetch_card_finder` | TL-COMM-004 | `benefitDetail`(업종) · 연회비 범위 · 정렬로 신한카드 추천. `benefitDetail` 이 비었거나 해석 불가면 업종 선택 위젯 반환 |
| `fetch_card_search` | TL-COMM-005 | `keyword`(카드명)로 카드 한 장 상세. 못 찾으면 카드명 되묻기 위젯 |
| `fetch_popular_card` | TL-COMM-006 | 인기 TOP5 |
| `fetch_finance_tips` | TL-COMM-007 | 금융생활지식 콘텐츠 (`category`: `trend` / `finance` / `card_tips`) |

`fetch_finance_tips` 는 콘텐츠 목록이 코드에 내장돼 있어 MCI 호출이 없습니다. 나머지 3종은
`EGN00001` 을 호출합니다.

## 목업 데이터

- 소스: [`mci/mock_data.json`](mci/mock_data.json) (신한카드 검색 데이터 81건)
- [`mci/mock.py`](mci/mock.py) `MockBackend` 가 `data` 딕셔너리(`CRD_BNF`/`MSG`/`TAG_VL`
  + `AFE_*`/`SIZ`/`QEE`)로 필터·정렬해 `{"GRID1": [...], "TO_CT": n}` 반환
- `fetch_card_search` 의 `keyword` 는 정확일치 우선, 없으면 카드명 부분일치
- `fetch_popular_card` 는 고정 TOP5 (Deep Oil / Mr.Life / Air One / Point Plan / SOL트래블 체크)
- 설정 파일 불필요. 그냥 `./run.sh`

## 실행

```bash
./run.sh                       # http://localhost:8080/mcp
PORT=8081 ./run.sh
```

직접:

```bash
uv run uvicorn main:app --host 0.0.0.0 --port 8080
uv run python server.py        # FastAPI 없이 FastMCP 단독 구동
```

## 구동 스모크 테스트

```bash
SVC_CONFIG_DIR=/path/to/config uv run uvicorn main:app --port 8080   # 터미널 1
uv run python scripts/smoke_test.py                                   # 터미널 2
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
  mock_client.py         MockMciClient — MciClient 드롭인 목업 (툴이 import)
  mock.py                MockBackend — mock_data.json → GRID1 응답
  mock_data.json         신한카드 검색 데이터 81건
  mci_client.py          (실제 MCI 클라이언트 — 이 브랜치에선 미사용, 병합용으로 보관)
schemas/
  card_finder_tools_schemas.py   Card / CardDetail / CardsResult / CardDetailResult
  finance_tips_schemas.py        ContentItem / ContentResult
domain/industry.py       Industry (업종코드 · 셀렉터/위젯 표시명)
kakao/                   카카오툴즈 응답 빌더 (툴별 분리)
  common.py              응답 래퍼 / 셀렉터 버튼 / onClickAction 공용 조각
  card_finder.py         업종 셀렉터 + 카드 추천 목록
  card_search.py         카드명 되묻기 + 카드 상세
  popular_card.py        인기 TOP5 목록
  finance_tips.py        금융생활지식 목록
tools/
  __init__.py            REGISTER_TOOLS — 등록 함수 화이트리스트
  common.py              @mcp.tool 래퍼(tags→meta) + with_kakao 헬퍼
  card_finder_tools.py   fetch_card_finder
  card_search_tools.py   fetch_card_search
  popular_card_tools.py  fetch_popular_card
  finance_tips_tools.py  fetch_finance_tips
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
