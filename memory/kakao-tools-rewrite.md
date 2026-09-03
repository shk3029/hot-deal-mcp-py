---
name: kakao-tools-rewrite
description: hot-deal-mcp-py was rewritten from the Spring-AI port style to the user's fetch_* / MciClient tool style; data comes only from the real MCI EGN00001 call
metadata:
  type: project
---

On 2026-09-03 the user directed a full rewrite of hot-deal-mcp-py away from the
Spring-AI parity port (commit f416149) into their in-house tool style.

**Shape (their code = the outer shell):** flat root packages `mci/`, `schemas/`,
`domain/`, `kakao/`, `tools/`; `app/` package dismantled. Tools are
`register_<x>_tools(mcp)` funcs with `@mcp.tool(...)` decorators, tool names
`fetch_card_finder` / `fetch_card_search` / `fetch_popular_card` /
`fetch_finance_tips`, tool_codes TL-COMM-004..007. Card data is fetched via
`MciClient().call_with_itf_id("EGN00001", data={...})` — all 3 card tools use the
same EGN00001 search interface. `fetch_finance_tips` makes no MCI call (content
enums in `tools/finance_tips/contents.py`).

**Business logic = kept from the old `app/`.** The old `app/widgets/*` is the
"카카오툴즈 응답" builder — ported to `kakao/`. Industry selector kept; annual-fee
selector dropped. Domain enums (Industry, AnnualFeeBand, CardSortOrder,
credit_card_name) moved to `domain/`.

**Branches:** `feature/mci-fetch-tools` = real MCI only. `feature/mock` (branched
off it, for KakaoTools testing) re-adds `mci/mock.py` + `mci/mock_data.json` +
`mci/mock_client.py` (`MockMciClient`, a drop-in for `MciClient`) and switches the
3 card tools' import to it — the only diff between the branches. `mci_client.py`
is unchanged on both.

**`feature/mci-fetch-tools` is MCI-only, no mock.** A mock backend was built
first, verified, then removed there on the user's instruction ("이제 mci로만").
`mci/mci_client.py` must stay verbatim as the user pasted it
(includes `include_sensitive: boolean` and `except e:` — untouched on purpose).
`MciClient()` reads `$SVC_CONFIG_DIR/mci_interfaces.yaml` at construction and the
server will not start without it. `mci_interfaces.yaml.example` is the template
(the real file is internal, not in the repo).

**Why:** the user's team developed the descriptions + Kakao response shaping
externally; the real MCI call is internal.

**Spring sync:** the Spring source is `../hot-deal-mcp` branch `feature/test`.
Python was ported at Spring `9e5be06`; commits through `ea3b088` (2026-09-02)
were later back-ported into the kakao/ builders + domain/industry.py: selector
label split (교통/항공/공항라운지 via `Industry.selector_display_name`), "추천 TOP5"
rename + rank styling, `CARD_SEARCH_URL` for the "더 많은 카드 보기" button,
finance-tips description prefix, CARD_LAB article URLs (ECO 1424, Simple Plan+
1421). `8d85882` was a pure refactor, already reflected by the kakao/ split.

**How to apply:** `python_tests/` was deleted — no parity tests. `@mcp.tool` on
the official `mcp` SDK (1.29.1) has no `tags=` param, so `tools/common.py:tool()`
folds scope tags into `meta`. Kakao response is `widget` + `copy_text` at the top
level of each `*Result` model (not a nested `kakao` object) so KakaoTools renders
it directly. `scripts/smoke_test.py` needs a live MCI backend to pass now.
