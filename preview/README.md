# 로컬 Widget Preview

Kakao Tools Preview에서 확인한 ChatKit 위젯의 주요 계산 스타일을 로컬에서 재현합니다.
운영 프리뷰의 CSS 전체를 복사하지 않고, 현재 신한카드 Tool이 사용하는 컴포넌트와 실제
화면에서 확인한 치수·간격·색상을 개발용 CSS로 정리했습니다.

## 실행

외부망 또는 로컬 목 데이터:

```bash
./run-preview.sh
```

내부망 MCI 데이터:

```bash
CARD_DATA_SOURCE=mci ./run-preview.sh
```

기존 `./run.sh`는 MCP HTTP 서버만 실행하며 프리뷰와 독립적입니다. 두 서버가 모두
필요하면 각각 다른 터미널에서 실행합니다.

한 터미널에서 MCP 서버와 프리뷰를 함께 실행하려면:

```bash
./run-all.sh
```

기본값은 MCP `mci`, 프리뷰 `mock`입니다. 둘 다 목 데이터로 실행하려면:

```bash
CARD_DATA_SOURCE=mock ./run-all.sh
```

서로 다른 데이터 소스가 필요하면 `MCP_DATA_SOURCE`와 `PREVIEW_DATA_SOURCE`를 각각
지정할 수 있습니다.

브라우저에서 `http://127.0.0.1:8765`를 엽니다.

## 지원 기능

- MCP `tools/list` 기준으로 등록된 4개 Tool과 입력 스키마 자동 조회
- 발화 분석 대신 Tool과 파라미터를 화면에서 직접 선택해 호출
- 카드 추천: 업종, 연회비, 카드 종류, 정렬 선택
- 카드 상세: 지원 카드명 선택
- 인기 카드: 파라미터 없이 호출
- 금융생활지식: 트렌드, 금융, 카드연구소 카테고리 선택
- 직접 반환한 `widget`/`copy_text` JSON 붙여넣기 및 실시간 렌더링
- JSON-RPC `tools/call` 응답의 `content[0].text` 자동 역직렬화
- 카드 추천 Tool을 로컬에서 직접 호출
- 업종 셀렉터 버튼 클릭 시 사용자 발화 표시 후 같은 추천 Tool 재호출
- 카드 행 상세 버튼 클릭 시 사용자 발화 표시 후 카드 상세 Tool 호출
- URL 버튼 클릭 시 새 탭 열기
- Card, Col, Row, Text, Caption, Image, Badge, Button, Divider, ListView,
  ListViewItem 렌더링

이 페이지는 개발 편의를 위한 근사 프리뷰입니다. 최종 UI 판정은 실제 연동 플랫폼의
Preview에서 확인해야 합니다.
