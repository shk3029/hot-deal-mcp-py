# Java → Python 포팅 노트

`../hot-deal-mcp` (Spring Boot 3.5 / Spring AI MCP, Java 21) 를 이 프로젝트
(FastAPI + 공식 `mcp` SDK, Python 3.11) 로 옮기면서 바뀐 점을 정리한다.

> **포팅 기준 커밋**: `9e5be06 feat: 금융생활지식 툴 추가` 시점의 Java `main` 상태
> (체크/신용/정렬 필터 + 금융생활지식 툴 포함).

---

## 1. 한눈에 보기

| 영역 | Java (`hot-deal-mcp`) | Python (`hot-deal-mcp-py`) |
| --- | --- | --- |
| 런타임 | Spring Boot + `spring-ai-starter-mcp-server-webmvc` | FastAPI + `mcp[cli]` (FastMCP) |
| MCP 전송 | `protocol: STREAMABLE` (WebMVC) | FastMCP streamable-HTTP ASGI 앱을 FastAPI에 `mount` |
| 세션 | 기본(스테이트풀) | `stateless_http=True`, `json_response=True` |
| 엔드포인트 | `POST /mcp`, `GET /actuator/health` | `POST /mcp`, `GET /health` |
| DI | `@Configuration` / `@Service` / `@Repository` 빈 | `app/mcp_server.py` 모듈 레벨 조립 |
| 툴 정의 | `@McpTool` 애노테이션 + 수동 `SyncToolSpecification` | `@mcp.tool()` 데코레이터 |
| JSON | Jackson `ObjectMapper` | `json.dumps(..., ensure_ascii=False, separators=(",",":"))` |
| 카드 데이터 | `ClassPathResource("data.json")` | `app/data/data.json` (원본 그대로 복사) |
| 빌드/실행 | Gradle `bootJar`, `run.sh` (java -jar) | `uv`, `run.sh` (uvicorn) |
| 테스트 | JUnit 5 + AssertJ + Mockito | pytest + `monkeypatch` |

**MCP 계약(툴 이름·파라미터명·스키마·응답 형식)은 그대로 유지**했다. PlayMCP 쪽에서 보면
동일하게 동작한다.

---

## 2. 그대로 유지한 것

- **툴 4종의 이름**: `getCreditCardRecommendationsWithSelector`, `getCreditCardDetail`,
  `getPopularCreditCards`, `getFinancialLifeKnowledgeArticles`
- **파라미터명**: `industry`, `annualFee`, `cardType`, `sort`, `cardName`, `category`
  (파이썬 관례를 깨고 camelCase 유지 — `# noqa: N803`)
- **파라미터 설명 / 툴 description 문구** (영문·국문 그대로 — 바이트 단위로 동일함을 테스트로 확인)
- **툴 `title`**: `소비 업종별 카드 안내 (선택 위젯)` / `신한카드 상품 상세 조회` /
  `신한카드 인기 TOP5` / `금융생활지식 콘텐츠`
- **`ToolAnnotations`**: `readOnlyHint=True`, `destructiveHint=False`,
  `idempotentHint=True`, `openWorldHint=False`
- **응답 형식**: `{"widget": <오브젝트|null>, "copy_text": <문자열>}` 를 text content 로 반환
- **위젯 컴포넌트 트리**: `Card`/`Col`/`Row`/`Text`/`Badge`/`Image`/`Button`/`ListView`/
  `ListViewItem`/`Divider`/`Caption` 의 타입·속성·자식 순서
- **`copy_text` 마크다운 문구**
- **서버 식별자**: name `shinhan-credit-card-guide`, version `0.0.1`,
  instructions `신한카드 상품 추천과 카드 상세 정보를 PlayMCP 위젯 형식으로 제공합니다.`
- **카드 데이터 파싱 규칙**: `pagetitle`/`pageid`/`pvafeat`/`cardType`/`svtcd` 필수 검증,
  `svtpnm{1..3}` + `svtptt{1..3}` → `"이름 · 설명"` 혜택 문자열, 상대경로 → 절대 URL
  (`https://www.shinhancard.com`, `https://cdn.www.shinhancard.com`)

---

## 3. 구조 매핑

| Java | Python |
| --- | --- |
| `HotDealMcpApplication` | `app/main.py` (FastAPI 진입점, `/mcp` 마운트 + `/health`) |
| `McpToolConfig` | `app/tools/card_finer_tools.py` → `get_credit_card_recommendations_with_selector` |
| `CreditCardDetailToolConfig` | `app/tools/card_search_tools.py` → `get_credit_card_detail` |
| `PopularCreditCardToolConfig` | `app/tools/popular_card_tools.py` → `get_popular_credit_cards` |
| `FinancialKnowledgeToolConfig` | `app/tools/finance_tips_tools.py` → `get_financial_life_knowledge_articles` |
| `service/Industry` | `app/domain/industry.py` |
| `service/AnnualFeeBand` | `app/domain/annual_fee_band.py` |
| `service/CardSortOrder` | `app/domain/card_sort_order.py` |
| `service/CreditCardName` (enum 81종) | `app/domain/credit_card_name.py` (`list[str]` + 헬퍼) |
| `service/FinancialKnowledgeCategory` | `app/domain/financial_knowledge.py` |
| `service/CreditCardDataRepository` | `app/services/card_repository.py` |
| `service/CreditCardGuideService` | `app/services/card_guide_service.py` |
| `service/PopularCreditCardService` | `app/services/popular_card_service.py` |
| `service/FinancialKnowledgeService` | `app/services/financial_knowledge_service.py` |
| `widget/PlayMcpWidgetFactory` | `app/widgets/` (툴별 모듈 + `common.py`) |
| `widget/PlayMcpWidgetResponse` (record) | `dict` `{"widget", "copy_text"}` (`app/widgets/common.py :: response()` 헬퍼) |
| `config/CacheConfig` | **삭제** (§6) |
| `config/McpRequestHeaderLoggingFilter` | **삭제** (§6) |
| `src/main/resources/application.yaml` | 환경변수(`PORT`, `HOST`, `LOG_LEVEL`) + 코드 상수 |
| `src/main/resources/data.json` | `app/data/data.json` (동일) |

---

## 4. 구현 방식이 바뀐 부분

### 4.1 툴 등록 & 스키마

- Java `McpToolConfig`/`FinancialKnowledgeToolConfig` 는 `@McpTool` 애노테이션이
  메서드 시그니처에서 스키마를 생성. → Python 은 `@mcp.tool()` + 타입힌트 +
  `Annotated[T, Field(description=...)]`.
- Java `CreditCardDetailToolConfig` 는 `McpSchema.JsonSchema` 를 **수동으로** 만들어
  `enum` 81개와 `required=["cardName"]` 를 넣음. → Python 은
  `Annotated[str, Field(description=..., json_schema_extra={"enum": CREDIT_CARD_NAMES})]`.
  기본값이 없으므로 `required` 에 자동 포함된다. 결과 스키마는 동일.
- `enum` 값과 파라미터 설명 문자열이 **`credit_card_name.CREDIT_CARD_NAMES` 리스트
  하나**만 바라보도록 한 것(single source of truth)은 Java `CreditCardName.displayNames()`
  와 같은 취지. `cardName` 설명 = `접두사 + ", ".join(81개)` 로 Java
  `parameterDescription()` 과 바이트 단위 동일.

#### inputSchema 바이트 단위 일치

Pydantic 이 만드는 스키마 래퍼는 Java(Spring AI `JsonSchemaGenerator` / 수동
`McpSchema.JsonSchema`) 와 형태가 달라서, 등록 직후 `_match_spring_ai_schema()`
(`app/mcp_server.py`) 로 **각 툴의 `inputSchema` 를 Java 출력과 바이트 단위로 동일하게
재작성**한다. 기준값은 Java `hot-deal-mcp` 실서버(fresh `bootJar`)의 `tools/list`
응답이고, `python_tests/fixtures/java_tools_list.json` 으로 고정해 회귀 검증한다
(`test_java_parity.py`).

| 항목 | Pydantic 기본 | Java = 재작성 후 |
| --- | --- | --- |
| 루트 키 순서 | `properties`, `type`, `title` | `type` → `properties` → `required` → *(상세만)* `additionalProperties` |
| `required` | 비면 키 자체가 없음 | 비어도 항상 `"required": []` |
| Optional 파라미터 | `{"anyOf":[{"type":"integer"},{"type":"null"}],"default":null}` | `{"type":"integer", ...}` + `required` 에서 제외 |
| 정수 파라미터 | `{"type":"integer"}` | `{"type":"integer","format":"int32", ...}` |
| 프로퍼티 키 순서 | 제각각 | `type` → *(정수면)* `format` → `description` → *(있으면)* `enum` |
| 프로퍼티/루트 `title` | Pydantic 자동 추가 | 없음 |
| `additionalProperties:false` | 없음 | `getCreditCardDetail` (수동 스키마) 에만 |

결과 (`getCreditCardRecommendationsWithSelector`, Java 와 동일):

```json
{
  "type": "object",
  "properties": {
    "industry":  {"type": "integer", "format": "int32", "description": "..."},
    "annualFee": {"type": "string", "description": "..."},
    "cardType":  {"type": "integer", "format": "int32", "description": "..."},
    "sort":      {"type": "string", "description": "..."}
  },
  "required": []
}
```

#### 툴 title / annotations

- `title` 은 Java 처럼 **`annotations.title` 에** 넣는다. 애노테이션 기반 3개 툴은
  최상위 `title` 도 함께 세팅(Java 동일), 수동 스키마인 `getCreditCardDetail` 은
  최상위 `title` 을 비운다(Java 동일).
- `annotations` = `title` + `readOnlyHint:true` + `destructiveHint:false` +
  `idempotentHint:true` + `openWorldHint:false` — Java 와 동일.

> 유일하게 재현하지 않은 것: Java `getCreditCardDetail` 의 `annotations.returnDirect:false`.
> MCP 스펙에 없는 Spring AI 전용 필드로 `mcp.types.ToolAnnotations` 에 존재하지 않는다.
> LLM/PlayMCP 동작에는 영향이 없다.

### 4.2 에러 무해화(sanitize)

| | Java | Python |
| --- | --- | --- |
| 추천/금융/인기 툴 | `throw new IllegalStateException(MSG)` → 애노테이션 어댑터가 `isError=true` text 로 변환 | `raise RuntimeError(MSG)` → FastMCP 가 `isError=true` text 로 변환 |
| 상세 툴 | `CallToolResult.builder().isError(true).addTextContent(MSG)` 를 직접 생성 | `raise RuntimeError(MSG)` (와이어 결과 동일) |

내부 예외 원인(cause)은 **로그에만** 남기고 사용자 메시지엔 노출하지 않는 원칙 유지.
에러 메시지 문구도 그대로:
- `### 카드 정보를 불러오지 못했습니다.\n\n잠시 후 다시 시도해 주세요.`
- `### 인기 카드 정보를 불러오지 못했습니다.\n\n잠시 후 다시 시도해 주세요.`
- `### 금융생활지식을 불러오지 못했습니다.\n\n잠시 후 다시 시도해 주세요.`

### 4.3 clarification / 파싱 실패 흐름

Java `IllegalArgumentException` 로 신호하던 것을 Python `ValueError` 로 통일.

- 업종 코드 없음/미지원 → `industry_selector()` 위젯 (정상 응답)
- 연회비 파싱 실패 → `annual_fee_selector()` 위젯 (정상 응답)
- 정렬 파싱 실패 → 무해화 에러 (Java 와 동일하게 바깥 `try` 로 전파)
- 카드명 공백/미지원 → `card_name_clarification()` 위젯 (정상 응답)

### 4.4 정렬 비교자

Java `Comparator.comparing(...).reversed().thenComparingInt(...).thenComparing(...)` →
Python 은 **안정 정렬을 덜 중요한 키부터 겹쳐** 동일 결과를 낸다
(`app/services/card_repository.py::_sort_in_place`).

| 정렬 | 우선순위 |
| --- | --- |
| `출시일순` (`RELEASE_DATE`) | `page_id` 내림차순 → `annual_fee` 오름차순 → `title` 오름차순 |
| `연회비순` (`ANNUAL_FEE`) | `annual_fee` 오름차순 → `page_id` 내림차순 → `title` 오름차순 |

### 4.5 자잘한 치환

| Java | Python |
| --- | --- |
| `String.format("%,d원", fee)` | `f"{fee:,}원"` |
| `Collections.shuffle(list)` (혜택 배지 2개 랜덤) | `random.shuffle(list)` — 동작·비결정성 동일 |
| `String.format("%02d", i)` | `f"{i:02d}"` |
| `Map.of(...)` / `LinkedHashMap` | dict 리터럴 (삽입 순서 보존) |
| Jackson enum `@JsonValue`/`@JsonCreator` | 없음 — 표시명 문자열을 그대로 사용 |
| Caffeine `@Cacheable` | 없음 — `data.json` 은 기동 시 1회 메모리 로드 |
| SLF4J `log.info(...)` | `logging.getLogger(__name__).info(...)` |

### 4.6 FastAPI 마운트

`mcp.streamable_http_app()` 하위 앱의 lifespan 은 부모가 자동 실행하지 않으므로
`app/main.py` 의 lifespan 에서 `mcp.session_manager.run()` 을 직접 구동한다.
`streamable_http_path="/mcp"` 인 앱을 루트(`/`)에 마운트해 최종 경로가 정확히
`/mcp` 가 되도록 했다(트레일링 슬래시 리다이렉트 회피).

### 4.7 서버 version

FastMCP 생성자에는 `version` 인자가 없어서 `initialize` 응답의
`serverInfo.version` 이 SDK 버전으로 나온다. `mcp._mcp_server.version = "0.0.1"` 로
Java `application.yaml` 의 선언 값에 맞췄다.

---

## 5. 설정

`application.yaml` 의 항목별 처리:

| yaml | 처리 |
| --- | --- |
| `spring.ai.mcp.server.name/version/instructions` | `FastMCP(name=..., instructions=...)` + `version` 패치 |
| `spring.ai.mcp.server.protocol: STREAMABLE` | `mcp.run(transport="streamable-http")` / ASGI 마운트 |
| `spring.cache.*` (Caffeine) | 삭제 |
| `server.port: ${PORT:8080}` | 환경변수 `PORT` (기본 8080), `HOST` (기본 `0.0.0.0`) |
| `management.endpoints...` (actuator) | `GET /health` 하나로 축소 (metrics/prometheus 없음) |
| `logging.level / pattern` | `logging.basicConfig(level=$LOG_LEVEL, format="%(asctime)s - %(levelname)s - %(message)s")` |

---

## 6. 포팅하지 않은 것 (의도적)

| 항목 | 이유 |
| --- | --- |
| `Dockerfile`, `docker-compose.yml`, `deploy.sh` | 요청 범위에서 제외 |
| `McpRequestHeaderLoggingFilter` (+ 그 테스트) | 요청 범위에서 제외. 필요 시 FastAPI 미들웨어로 추가 가능 |
| `CacheConfig` (Caffeine) | 현재 툴에 `@Cacheable` 사용처가 없음. 데이터는 기동 시 1회 로드 |
| Actuator metrics/info/prometheus | `/health` 로 대체 |
| Gradle wrapper / `build.gradle` | `pyproject.toml` (uv) 로 대체 |

---

## 7. 테스트 매핑

Java 30여 개 → Python **64개**. AssertJ 체이닝을 여러 `assert` 로 풀고, Java 실서버
`tools/list` 와의 바이트 단위 일치 검증(`test_java_parity.py`)을 추가하면서 개수가 늘었다.

| Java 테스트 클래스 | Python 파일 | 비고 |
| --- | --- | --- |
| `service/IndustryTest` | `test_industry.py` | + `widget_display_name` / `from_code` 예외 케이스 추가 |
| `service/CardSortOrderTest` | `test_card_sort_order.py` | 1:1 |
| `service/FinancialKnowledgeCategoryTest` | `test_financial_knowledge_category.py` | 1:1 |
| `service/CreditCardDataRepositoryTest` | `test_card_repository.py` | 1:1 (81종 정확 매칭, 퍼지 매칭 금지, 필터·정렬) |
| *(Java에 없음)* | `test_annual_fee_band.py` | `from_string` / `matches` 경계값 신규 |
| `config/McpToolConfigTest` | `test_recommendation_tool.py` | `Mockito.mock` → `monkeypatch` |
| `config/CreditCardDetailToolConfigTest` | `test_card_detail_tool.py` | 아래 주의 참고 |
| `config/PopularCreditCardToolConfigTest` | `test_popular_card_tool.py` | 1:1 |
| `config/FinancialKnowledgeToolConfigTest` | `test_financial_knowledge_tool.py` | 1:1 |
| `config/McpRequestHeaderLoggingFilterTest` | *(삭제)* | 필터 미포팅 |
| `HotDealMcpApplicationTests` (`contextLoads`) | `test_mcp_server.py` | 툴 4종 등록·스키마·`ToolAnnotations`·`/health`·`/mcp` 마운트로 확장 |
| *(신규)* | `test_java_parity.py` | Java 실서버 `tools/list` 캡처(`fixtures/java_tools_list.json`)와 description·inputSchema·annotations·title 바이트 단위 비교 |

**주의 — `CreditCardDetailToolConfigTest` 에서 바뀐 케이스**

- `missingCardNameReturnsClarificationWidget` (빈 인자 맵 호출) → MCP 레벨에서 `cardName`
  이 `required` 라 이 경로가 안 생김. `test_blank_card_name_returns_clarification_widget`
  (`""` 직접 호출) + `test_unknown_card_name_returns_clarification_widget` 로 대체.
- `enumUsesDisplayNameForJsonInputAndOutput` (Jackson enum 직렬화) → enum 타입이 없어
  N/A. `parameter_description()` 가 81개를 모두 포함하는지 검증하는 테스트로 대체.
- `schemaUsesEnumDisplayNamesAsSingleSourceOfTruth` → `test_card_detail_tool.py` +
  `test_mcp_server.py::test_card_detail_schema_uses_card_name_enum_as_single_source_of_truth`
  로 분리.

실행:

```bash
uv run pytest
```

---

## 8. 동작 검증 (수동)

```bash
uv run uvicorn app.main:app --port 8899 &

# initialize
curl -s -X POST localhost:8899/mcp \
  -H 'Content-Type: application/json' -H 'Accept: application/json, text/event-stream' \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"c","version":"1"}}}'
# → serverInfo: {"name":"shinhan-credit-card-guide","version":"0.0.1"}

# tools/call
curl -s -X POST localhost:8899/mcp \
  -H 'Content-Type: application/json' -H 'Accept: application/json, text/event-stream' \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"getPopularCreditCards","arguments":{}}}'
# → content[0].text = {"widget":{...},"copy_text":"### 🔥 인기 TOP5 ..."}
```

---

## 9. PlayMCP(카카오툴즈) 응답 규약 — "결과값을 카카오에 맞게 맞추는 부분"

### 9.1 전체 흐름

```
도메인 결과 (CardGuide / CardDetail / PopularCard / Article ...)
        │
        ▼  app/widgets/<툴>_widgets.py        ← ① PlayMCP 위젯 트리(dict) 로 변환
   {"widget": <ChatKit 컴포넌트>, "copy_text": <마크다운 fallback>}
        │
        ▼  app/tools/common.py :: json_widget()  ← ② JSON 문자열로 직렬화
   '{"widget":{...},"copy_text":"..."}'
        │
        ▼  @mcp.tool 함수가 이 문자열을 return  ← ③ FastMCP 가 text content 로 감쌈
   {"content":[{"type":"text","text":"{\"widget\":...}"}],"isError":false}
        │
        ▼  PlayMCP                             ← ④ text 를 JSON 파싱해서 위젯 렌더 +
                                                  copy_text 를 복사/음성/폴백 텍스트로 사용
```

핵심: **MCP 표준 툴 결과는 그냥 "텍스트 한 덩어리"**다. PlayMCP 는 그 텍스트가
`{"widget", "copy_text"}` JSON 이라고 약속하고, `widget` 을 자체 ChatKit 렌더러로
그린다. 그래서 서버가 하는 "카카오에 맞추는 일" = **이 JSON 을 규격대로 만들어
text content 로 돌려주는 것** 두 가지뿐이다.

### 9.2 ① 위젯 트리 생성 — `app/widgets/`

Java `widget/PlayMcpWidgetFactory.java` 와 1:1. 툴별 모듈로 쪼갰고 공용 조각은
`common.py`. 함수별 대응:

| 함수 | 모듈 | 반환 위젯 | 쓰는 툴 |
| --- | --- | --- | --- |
| `industry_selector()` / `annual_fee_selector()` | `card_finer_widgets` | `Card` + 버튼 행들 (조건 재질문) | 추천 |
| `credit_card_guide_list(guides, industry, band)` | `card_finer_widgets` | `Card > Col(카드 행들) + "더 많은 카드 보기" 버튼` | 추천 |
| `credit_card_detail(detail)` | `card_search_widgets` | `Card > 헤더 Row + Divider + 혜택 Row들 + "자세히 보기" 버튼` | 상세 |
| `card_name_clarification()` | `card_search_widgets` | `Card > Text` (카드명 되묻기) | 상세 |
| `popular_credit_card_list(cards)` | `popular_card_widgets` | `Card > Text/Caption + Col(랭킹 행들) + 차트 버튼` | 인기 |
| `financial_knowledge_list(category, articles)` | `finance_tips_widgets` | `ListView > ListViewItem 들 + "다른 카테고리 보기" 버튼` | 금융생활지식 |

**PlayMCP ChatKit 컴포넌트**(여기서 쓰는 것만): `Card`, `Col`, `Row`, `Text`,
`Caption`, `Badge`, `Image`, `Button`, `Divider`, `ListView`, `ListViewItem`.
속성도 Java 와 동일 — `size`/`weight`/`maxLines`/`textAlign`/`gap`/`padding{x,y}`/
`flex`/`width`/`align`/`variant`/`pill`/`block`/`uniform`/`fit`/`radius` 등.

**`onClickAction` 2종** (`common.send_user_message_action`, `common.open_url_action`):

```python
# 버튼/타일을 누르면 그 텍스트가 사용자 발화로 다시 들어감 → 모델이 이어서 툴 호출
{"payload": {"target": {"type": "sendUserMessage", "properties": {"text": "신한카드 Deep Oil 혜택 알려줘"}}}}

# 외부 링크 열기 (PC/모바일 URL 동일값)
{"payload": {"target": {"url": "https://...", "pcUrl": "https://..."}}}
```

- 업종/연회비 선택 버튼 → `sendUserMessage` (라벨 그대로 재발화)
- 추천 카드 타일의 `>` 버튼 → `sendUserMessage("<카드명> 혜택 알려줘")` (상세 툴 유도)
- "다른 카테고리 보기" → `sendUserMessage("<다음카테고리> 금융생활지식 보여줘")`
- "더 많은 카드 보기" / "자세히 보기" / 아티클 행 → `openUrl`

### 9.3 최상위 응답 형식 — `{"widget", "copy_text"}`

Java `record PlayMcpWidgetResponse(Object widget, @JsonProperty("copy_text") String copyText)`
→ Python `app/widgets/common.py :: response()`:

```python
def response(widget, copy_text):
    return {"widget": widget, "copy_text": copy_text}
```

- **`widget`**: ChatKit 컴포넌트 트리. clarification 계열은 `null` 가능
  (`{"widget": null, "copy_text": "..."}`).
- **`copy_text`**: 위젯을 못 그리는 환경(복사하기, TTS, 로그, 폴백)용 마크다운.
  Java 의 `StringBuilder` 로 만들던 문구를 그대로 옮김.
- **`status`** 는 **넣지 않는다** — PlayMCP 가 자동으로 붙인다 (Java 주석과 동일).

### 9.4 ② 직렬화 & ③ 반환 — `app/tools/common.py`

```python
def json_widget(payload: dict) -> str:
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
```

- `ensure_ascii=False`: 한글을 `\uXXXX` 로 깨지 않고 그대로 (Jackson 기본과 동일)
- `separators=(",", ":")`: 공백 없는 압축 JSON

각 `@mcp.tool` 함수는 **이 문자열을 그대로 `return`** 한다. 반환 타입이 `-> str`
이므로 FastMCP 는 `structuredContent` 없이 `content: [{"type":"text","text": <그 문자열>}]`
하나로 감싼다. → Java 상세 툴의
`CallToolResult.addTextContent(objectMapper.writeValueAsString(response))` 와 동일한 와이어 결과.

에러일 때만 `raise RuntimeError(무해화_메시지)` → FastMCP 가 `isError: true` + 그 메시지
text 로 변환 (§4.2).

### 9.5 실제 응답 예시 (`getPopularCreditCards`)

```json
{
  "content": [
    {
      "type": "text",
      "text": "{\"widget\":{\"type\":\"Card\",\"children\":[{\"type\":\"Text\",\"value\":\"🔥 인기 TOP5\",\"size\":\"lg\",\"weight\":\"semibold\"}, ... ]},\"copy_text\":\"### 🔥 인기 TOP5\\n\\n신한카드에서 발급량이 가장 많은 카드예요.\\n\\n1. **신한카드 Deep Oil** · 주유\\n ...\"}"
    }
  ],
  "isError": false
}
```

PlayMCP 는 `content[0].text` 를 JSON 파싱 → `widget` 렌더, `copy_text` 는 "복사"·폴백용.
