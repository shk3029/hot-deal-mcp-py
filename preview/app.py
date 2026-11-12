from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

# 로컬 프리뷰는 내부 MCI 설정 없이 바로 실행되도록 mock을 기본값으로 사용한다.
# CARD_DATA_SOURCE=mci를 명시하면 동일 코드로 실제 MCI 응답을 확인할 수 있다.
os.environ.setdefault("CARD_DATA_SOURCE", "mock")

from server import mcp  # noqa: E402  (환경변수 설정 후 Tool을 등록해야 한다.)


ROOT = Path(__file__).resolve().parent


class ToolCallRequest(BaseModel):
    name: str
    arguments: dict[str, Any] = Field(default_factory=dict)


app = FastAPI(title="shinhan-card-mcp widget preview")

@app.get("/mock-events/{event_id}/thumbnail.svg")
def mock_event_thumbnail(event_id: str):
    from html import escape
    from fastapi.responses import Response

    # 목업 썸네일: 이벤트 id로 색을 고정하고 첫 글자를 표시한다.
    palette = ["#2a6ef5", "#1f9d74", "#e0663b", "#8a5cf5", "#d3415d", "#0e8fb0"]
    color = palette[sum(map(ord, event_id)) % len(palette)]
    initial = escape(event_id[:1].upper() or "E")
    svg = (f"<svg xmlns='http://www.w3.org/2000/svg' width='144' height='144' viewBox='0 0 144 144'>"
           f"<rect width='144' height='144' rx='16' fill='{color}'/>"
           f"<text x='72' y='86' font-size='48' font-family='sans-serif' font-weight='700' "
           f"fill='#fff' text-anchor='middle'>{initial}</text></svg>")
    return Response(svg, media_type="image/svg+xml")


@app.get("/mock-events")
@app.get("/mock-events/{event_id}")
def mock_event_landing(event_id: str | None = None):
    from html import escape
    from fastapi.responses import HTMLResponse
    from mci.event_client import create_event_client, today_kst
    from kakao.events import mock_events_url

    if os.getenv("EVENT_DATA_SOURCE") != "mock":
        raise HTTPException(status_code=503, detail="이벤트 목업 모드가 아닙니다.")
    today = today_kst()
    events = sorted([e for e in create_event_client().list_events()
        if e.start_date <= today <= e.end_date], key=lambda e: (e.published_date, e.id), reverse=True)
    if event_id is not None:
        events = [e for e in events if e.id == event_id]
        if not events:
            raise HTTPException(status_code=404, detail="목업 이벤트를 찾을 수 없습니다.")
    parts = ["<!doctype html><html lang='ko'><meta charset='utf-8'>",
        "<meta name='viewport' content='width=device-width,initial-scale=1'>",
        "<title>목업 이벤트</title><body><main>",
        "<h1>이벤트 목업 미리보기</h1><p>가상 데이터입니다. 실제 혜택·응모·개인별 참여 자격을 제공하지 않습니다.</p>"]
    for e in events:
        parts.append(f"<article><h2>{escape(e.title)}</h2><p>{escape(e.description)}</p>"
            f"<p>{escape(e.event_type)} · {e.start_date} ~ {e.end_date}</p>"
            f'<a href="{escape(mock_events_url(e.id), quote=True)}">자세히 보기 (목업)</a></article>')
    parts.append(f'<p><a href="{escape(mock_events_url(), quote=True)}">전체 목업 이벤트</a></p></main></body></html>')
    return HTMLResponse("".join(parts))



@app.get("/api/health")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "server": "shinhan-card-mcp",
        "dataSource": os.getenv("CARD_DATA_SOURCE", "mock"),
    }


@app.get("/api/tools")
async def list_tools() -> dict[str, list[dict[str, Any]]]:
    tools = await mcp.list_tools()
    return {
        "tools": [
            {
                "name": tool.name,
                "title": tool.title or tool.annotations.title or tool.name,
                "description": tool.description or "",
                "inputSchema": tool.parameters,
            }
            for tool in tools
        ]
    }


@app.post("/api/tools/call")
async def call_tool(request: ToolCallRequest) -> dict[str, Any]:
    try:
        tool = await mcp.get_tool(request.name)
        result = await tool.run(request.arguments)
    except Exception as exception:
        raise HTTPException(status_code=400, detail=str(exception)) from exception

    text_content = next(
        (
            content.text
            for content in result.content
            if getattr(content, "type", None) == "text"
        ),
        None,
    )
    if not isinstance(text_content, str):
        raise HTTPException(status_code=500, detail="Tool이 text 응답을 반환하지 않았습니다.")

    try:
        payload = json.loads(text_content)
    except json.JSONDecodeError as exception:
        raise HTTPException(
            status_code=500,
            detail="Tool text가 유효한 widget JSON이 아닙니다.",
        ) from exception

    return {
        "tool": request.name,
        "arguments": request.arguments,
        "payload": payload,
    }


app.mount("/", StaticFiles(directory=ROOT / "static", html=True), name="preview")
