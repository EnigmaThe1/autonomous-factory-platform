"""Entry point: python -m af_core"""

import uvicorn

from af_core.config import settings

uvicorn.run(
    "af_core.api.app:app",
    host=settings.host,
    port=settings.port,
    log_level=settings.log_level,
    reload=settings.debug,
)
