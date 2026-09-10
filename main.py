from __future__ import annotations

import uvicorn
import os

from api.app import create_app
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