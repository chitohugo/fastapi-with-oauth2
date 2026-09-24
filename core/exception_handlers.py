import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from core.exceptions import BaseError

logger = logging.getLogger("client-ai")


def register_exception_handlers(app: FastAPI) -> None:
    """Register global handlers for domain errors."""

    @app.exception_handler(BaseError)
    async def handle_base_error(_request: Request, exc: BaseError) -> JSONResponse:
        logger.info("Domain error %s: %s", exc.code, exc.message)
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "code": exc.code,
                "description": exc.description,
                "message": exc.message,
            },
        )
