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
