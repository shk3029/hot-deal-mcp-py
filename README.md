# hot-deal-mcp-py

하나의 소스에서 `CARD_DATA_SOURCE=mock|mci` 환경변수로 목업 데이터와 실제 MCI를
선택합니다. 기본값은 실제 `mci`이며, 목업은 `CARD_DATA_SOURCE=mock`을 명시할 때만
사용합니다.

신한카드 상품 안내 MCP 서버. `fastmcp==3.2.4`로 Tool 을 정의하고,
streamable-HTTP ASGI 앱을 **FastAPI** 에 마운트해 `/mcp` 로 제공합니다.

툴은 사내 스타일(`register_*_tools(mcp)` + `@mcp.tool(tags=..., meta=...)`)로 작성돼
있고, 카드 데이터는 선택된 클라이언트의 `call_with_itf_id("EGN00001", ...)` 로
조회합니다. 각 툴 결과 모델
**최상위에 `widget` / `copy_text` (카카오툴즈 응답)** 이 실려 카카오 쪽에서 바로 렌더됩니다.

## MCP Tool (5종)

| Tool | tool_code | 설명 |
| --- | --- | --- |
| `getCreditCardRecommendationsWithSelector` | TL-COMM-004 | `industry` · `annualFee` · `cardType` · `sort`로 신한카드 추천. 업종이나 연회비가 불명확하면 선택 위젯 반환 |
| `getCreditCardDetail` | TL-COMM-005 | `cardName` enum으로 카드 한 장 상세. 못 찾으면 카드명 되묻기 위젯 |
| `getPopularCreditCards` | TL-COMM-006 | 파라미터 없이 인기 TOP5 |
| `getBrandEvents` | 미발급 (목업 개발용) | 선택 입력 `event_type`·`brand`로 진행 중 이벤트 조회. `EVENT_DATA_SOURCE=mock` 필수 |
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
  common.py              카카오 위젯 JSON 직렬화 + 툴 감사 로그
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


## 이벤트 툴 (기획서 반영 · 목업)

```bash
CARD_DATA_SOURCE=mock EVENT_DATA_SOURCE=mock ./run-all.sh
```

`getBrandEvents`는 기존 툴 이름을 유지하며, 이제 두 입력을 모두 생략할 수 있습니다.

| 입력 예시 | 응답 |
| --- | --- |
| `{}` | 진행 중 전체 최신 5건 |
| `{"event_type":"여행숙박"}` | 해당 분류 최신 5건 |
| `{"brand":"SOL LINK 체크카드"}` | 쇼핑문화에 속한 1건, 카드형 |
| `{"brand":"스타벅스"}` | 쇼핑문화·카드결제의 2건, 목록형 |
| `{"brand":"스타벅스","event_type":"여행숙박"}` | brand 우선, event_type 무시 |
| `{"brand":"슈퍼SOL"}` | 여러 결과 중 최신 5건 |
| `{"brand":"CU"}` | 목업 매칭 0건 → 전체 최신 5건 + 안내 |

- `event_type`: 쇼핑문화(51), 앱테크(52), 여행숙박(53), 카드결제(54), 청소년(55).
  입력은 한글 enum이며 숫자는 홈페이지 코드 매핑입니다. 청소년은 학교납입금·사립유치원
  자동납부 성격입니다. 학원비를 임의로 청소년에 매핑하지 않도록 설명합니다.
- brand는 사진의 40+59개 중 한샘 중복을 제거한 98개입니다. 작은 글씨인 윌리·런츠·칼이파이
  등의 정식 표기는 원문 확인이 필요합니다. API 브랜드 매핑으로 확정한 목록이 아닙니다.
- 두 필터는 선택 입력입니다. 조건 없는 요청·이번 달·참여 가능한 이벤트 요청은 일반 진행 중
  목록으로 응답하고, 개인별 자격 판정은 하지 않습니다. 자연어 원문을 서버로 받지 않습니다.
- 유효 brand가 있으면 카테고리에 관계없이 조회합니다. 지원하지 않는 값/검색 0건은 안내와 함께
  전체 최신 5건으로 대체합니다. 전체도 0건이면 명시적으로 빈 결과를 안내합니다.
- 매칭 여부를 먼저 판단한 다음 최신 등록일 내림차순(동률은 id 역순)으로 최대 5건을 반환합니다.
  현재 기간 판정은 한국 날짜 기준입니다. 최신 정렬은 내부 목업의 published_date 기준이며,
  실제 등록일 필드와 MCI 계약은 연동 시 확정해야 합니다.
- 1건은 Card, 2~5건은 ListView. 각 행은 왼쪽 썸네일, 오른쪽 요약(텍스트1)·제목(텍스트2),
  맨 오른쪽 상세 이동 `>` 버튼으로 구성되고, 목록 맨 마지막에 더 많은 이벤트 보기 버튼이 있습니다.
  썸네일은 `Event.thumbnail_url`이 없으면 프리뷰의 `/mock-events/{id}/thumbnail.svg` 목업을 씁니다.
- 상세/전체 이동은 프리뷰의 `/mock-events/{id}`, `/mock-events`로 연결됩니다.
  기본 URL은 http://127.0.0.1:8765 입니다. 포트가 다르거나 외부 기기에서 테스트할 때는
  `EVENT_MOCK_BASE_URL`에 접근 가능한 프리뷰 주소를 지정하세요. localhost 링크는 카카오
  사용자 기기에서 접근할 수 없으므로 외부 검증 시 반드시 변경해야 합니다.
- 목업은 기획 시나리오용 17건이며 실제 159건을 복제한 것이 아닙니다. 실제 혜택·응모는 없고,
  모든 화면에서 가상 데이터임을 표시합니다. 전체 페이지도 진행 중 목업만 보여줍니다.
- EVENT_DATA_SOURCE=mock을 명시해야 동작합니다. 미설정/mci/오타는 오류로 반환하며,
  장애를 빈 결과로 취급하거나 자동으로 목업으로 전환하지 않습니다.
- 실제 연동 전에 MCI 규격/이벤트별 브랜드 매핑/상세 URL/전체 URL/사내 tool_code를 확정하고,
  목업 전용 모델·설명·랜딩을 실제 데이터에 맞게 변경해야 합니다. 신규 툴·파라미터 변경은
  카카오에 사전 공유해야 합니다. 설명 길이는 각각 1,024자 이내로 관리합니다.

```bash
CARD_DATA_SOURCE=mock .venv/bin/python -m pytest python_tests/test_event_tools.py -q
```

이벤트 테스트는 스키마·0/1/다건·브랜드 우선·최신순·기간·오류·HTTP 호출·목업 상세 링크와
기존 툴 4종 호출을 확인합니다. LLM의 자연어→enum 추출 정확도는 실제 카카오 발화 테스트가
필요합니다. 기존 전체 테스트는 main._headers_for_log 누락으로 수집 단계에서 실패하며,
이 문제는 이벤트 변경 전부터 존재합니다.
