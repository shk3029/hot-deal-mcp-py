from __future__ import annotations

import logging
import uvicorn
import os

# uvicorn main:app 으로 띄울 때도 툴 요청 감사 로그(mcp.tool.audit, INFO)가 터미널에 나오도록 한다.
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
)

from api.app import create_app  # noqa: E402
from setup_otel import setup_otel

# from core.environment import get_env


app = create_app()

if os.getenv("ENVIRONMENT", "dev") in ["dev", "prod"]:
    setup_otel(app, "MCKA")
else:
    setup_otel(app, "MCKA-STAGING")

if __name__ == "__main__":
    log_config = uvicorn.config.LOGGING_CONFIG.copy()
    log_config["loggers"]["py.warning"] = {
        "level": "ERROR",
        "handlers": [],
        "propagate": False,
    }
    # env = get_env()
    uvicorn.run("main:app", host="0.0.0.0", port=8000, log_config=log_config)