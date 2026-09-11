from __future__ import annotations

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastmcp import FastMCP
from fastapi.responses import Response, FileResponse

from api.middleware.scope_filter import ScopeFilterMiddleware
from api.middleware.infer_auth_key import RequireInferAuthKey
from starlette.middleware import Middleware
from core.configuration import get_conf
from core.environment import get_env
from api.health import router as health_router
from tools import REGISTER_TOOLS

def create_app() -> FastAPI:
    conf = get_conf()
    env = get_env()

    # set FastMCP server
    mcp = FastMCP(conf.name)


    mcp.add_middleware(ScopeFilterMiddleware(conf))

    # tool 등록
    for _tools in REGISTER_TOOLS:
        _tools(mcp)


    mcp_app = mcp.http_app(
        path="/mcp",
        middleware=[Middleware(RequireInferAuthKey)],
        stateless_http=True,  # default=False, stateless_http=True일 경우, SSE 통신 X, stateless_http=False일 경우, worker=1 replica=1로 지정해야 session terminated 에러가 발생하지 않음.
    )

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        yield

    @asynccontextmanager
    async def combined_lifespan(app: FastAPI):
        async with lifespan(app):
            async with mcp_app.lifespan(app):
                yield

    # set FastAPI server
    app = FastAPI(title="MCP Server API",  lifespan=combined_lifespan)

    app.include_router(health_router)
    app.mount("/", mcp_app)
    return app
