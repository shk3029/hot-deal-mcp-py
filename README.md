# hot-deal-mcp-py

Java(Spring AI) `hot-deal-mcp` 서버를 파이썬으로 포팅한 것입니다. 공식 `mcp` SDK(FastMCP)로
Tool 을 정의하고, streamable-HTTP ASGI 앱을 **FastAPI** 에 마운트해 `/mcp` 로 제공합니다.

## MCP Tool (4종, Java 와 동일)

| Tool | 설명 |
| --- | --- |
| `getCreditCardRecommendationsWithSelector` | 업종 코드(1~24) · 연회비 구간 · 카드 종류 · 정렬 기준으로 신한카드 추천. 조건이 불충분하면 선택 위젯 반환 |
| `getCreditCardDetail` | 지정한 카드 한 장의 혜택/연회비 상세 위젯 |
| `getPopularCreditCards` | 인기 TOP5 (파라미터 없음) |
| `getFinancialLifeKnowledgeArticles` | 금융생활지식 콘텐츠 (트렌드 / 금융 / 카드연구소) |

Tool 응답은 모두 `{"widget": ..., "copy_text": ...}` JSON 문자열입니다(PlayMCP 형식).
카드 데이터는 `app/data/data.json` (Java `src/main/resources/data.json` 과 동일)에서 로드합니다.

## 실행

```bash
./run.sh                 # http://localhost:8080/mcp
PORT=8081 ./run.sh
```

또는 직접:

```bash
uv run uvicorn app.main:app --host 0.0.0.0 --port 8080
uv run python -m app.mcp_server      # FastAPI 없이 FastMCP 단독 구동
```

## 테스트

```bash
uv run pytest
```

## 구동 스모크 테스트

서버를 띄운 뒤 MCP 핸드셰이크 + 툴 4종을 실제 호출해 응답을 확인한다.

```bash
uv run uvicorn app.main:app --port 8080      # 터미널 1
uv run python scripts/smoke_test.py          # 터미널 2 (PORT 로 포트 변경 가능)
```

## PlayMCP / ngrok

```bash
ngrok http 8080
```

등록 주소: `https://YOUR-NGROK-DOMAIN.ngrok-free.app/mcp`

## 구조

```
app/
  main.py                     FastAPI 진입점 (+ /mcp 마운트, /health)
  mcp_server.py               FastMCP 인스턴스 + 툴 등록 + 스키마 정규화
  deps.py                     공유 서비스 싱글턴 (DI 컨테이너)
  tools/
    __init__.py               REGISTER_TOOLS — 등록 함수 화이트리스트
    common.py                 json_widget() 공통 헬퍼
    card_finer_tools.py       getCreditCardRecommendationsWithSelector
    card_search_tools.py      getCreditCardDetail
    finance_tips_tools.py     getFinancialLifeKnowledgeArticles
    popular_card_tools.py     getPopularCreditCards
  domain/                     Industry / AnnualFeeBand / CardSortOrder /
                              CreditCardName / FinancialKnowledgeCategory
  services/                   card_repository, card_guide_service,
                              popular_card_service, financial_knowledge_service
  widgets/                    PlayMcpWidgetFactory 포팅 (툴별로 분리)
    common.py                 응답 래퍼 / 셀렉터 버튼 / onClickAction 공용 조각
    card_finer_widgets.py     업종·연회비 셀렉터 + 카드 추천 목록
    card_search_widgets.py    카드명 되묻기 + 카드 상세
    finance_tips_widgets.py   금융생활지식 목록
    popular_card_widgets.py   인기 TOP5 목록
  data/data.json              신한카드 원본 데이터
python_tests/                 pytest (JUnit 테스트 포팅)
```

### 툴 켜고 끄기

`app/tools/__init__.py` 의 `REGISTER_TOOLS` 리스트에 있는 등록 함수만 서버에서 실행된다.
각 툴 모듈은 `register_<모듈>_tools(mcp)` 함수를 제공하고, 그 안에서 `@mcp.tool(...)` 로
실제 툴 함수를 등록한다. 특정 툴을 비활성화하려면 리스트에서 빼면 되고, `tools/list` 에도
노출되지 않는다.

```python
REGISTER_TOOLS = [
    register_card_finer_tools,
    register_card_search_tools,
    # register_finance_tips_tools,   # ← 주석 처리하면 이 툴만 꺼짐
    register_popular_card_tools,
]
```
