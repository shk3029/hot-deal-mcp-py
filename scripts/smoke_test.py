"""hot-deal-mcp-py 구동 스모크 테스트 - MCP 핸드셰이크 + 툴 4종 호출.

사용법:  uv run uvicorn app.main:app --port 8080   # 다른 터미널에서 서버 기동
        uv run python scripts/smoke_test.py       # (PORT 환경변수로 포트 변경 가능)
"""
import json
import os
import urllib.request

URL = f"http://localhost:{os.getenv('PORT', '8080')}/mcp"
HEADERS = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream"}


def rpc(method, params=None, rid=1):
    body = {"jsonrpc": "2.0", "id": rid, "method": method}
    if params is not None:
        body["params"] = params
    req = urllib.request.Request(URL, data=json.dumps(body).encode(), headers=HEADERS, method="POST")
    raw = urllib.request.urlopen(req).read().decode()
    for line in raw.splitlines():
        if line.startswith("data:"):
            raw = line[5:].strip()
            break
    return json.loads(raw)


def call_tool(name, args):
    res = rpc("tools/call", {"name": name, "arguments": args}, rid=99)
    if "error" in res:
        return {"__error__": res["error"]}
    content = res["result"]["content"][0]
    payload = json.loads(content["text"]) if content["type"] == "text" else content
    return {"isError": res["result"].get("isError", False), "payload": payload}


def summarize_widget(w):
    if w is None:
        return "widget=None"
    t = w.get("type")
    kids = w.get("children", [])
    return f"widget.type={t}, children={len(kids)}"


print("=" * 70)
init = rpc("initialize", {"protocolVersion": "2025-06-18", "capabilities": {},
                          "clientInfo": {"name": "smoke", "version": "1"}})
si = init["result"]["serverInfo"]
print(f"initialize OK  → serverInfo = {si['name']} {si['version']}")

tools = rpc("tools/list", rid=2)["result"]["tools"]
print(f"tools/list OK  → {[t['name'] for t in tools]}")

cases = [
    ("getCreditCardRecommendationsWithSelector", {}),
    ("getCreditCardRecommendationsWithSelector", {"industry": 5, "annualFee": "0~1만원대"}),
    ("getCreditCardRecommendationsWithSelector", {"industry": 24, "annualFee": "제한없음", "cardType": 1}),
    ("getCreditCardRecommendationsWithSelector", {"industry": 9, "sort": "연회비순"}),
    ("getCreditCardDetail", {"cardName": "신한카드 Mr.Life"}),
    ("getCreditCardDetail", {"cardName": "없는카드"}),
    ("getPopularCreditCards", {}),
    ("getFinancialLifeKnowledgeArticles", {"category": "카드연구소"}),
    ("getFinancialLifeKnowledgeArticles", {}),
]

for name, args in cases:
    print("-" * 70)
    print(f"tools/call {name}  args={args}")
    r = call_tool(name, args)
    if "__error__" in r:
        print("  ERROR:", r["__error__"])
        continue
    p = r["payload"]
    print(f"  isError={r['isError']}  {summarize_widget(p.get('widget'))}")
    ct = p.get("copy_text", "")
    first = ct.splitlines()[0] if ct else ""
    print(f"  copy_text[0]: {first}")

print("-" * 70)
print("전체 copy_text 예시 (getPopularCreditCards):")
print(call_tool("getPopularCreditCards", {})["payload"]["copy_text"])
