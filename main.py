import logging

import logger_config  # noqa: F401  — configures logging on import
from app.api.health import router as health_router
from app.api.routes import routers as v1_routers
from core.exception_handlers import register_exception_handlers
from fastapi import FastAPI
from config import settings
from container import Container
from core.rate_limit import limiter
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from starlette.middleware.cors import CORSMiddleware

logger = logging.getLogger("client-ai")


class AppCreator:
    _instance = None

    def __init__(self):
        self.app = FastAPI(
            title=settings.project_name,
            openapi_url=f"{settings.api}/openapi.json",
            version="0.0.1",
        )
        self.app.state.limiter = limiter

        register_exception_handlers(self.app)
        self.app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

        self.container = Container()
        self.db = self.container.db()

        if settings.cors_origins:
            self.app.add_middleware(
                CORSMiddleware,
                allow_origins=[str(origin) for origin in settings.cors_origins],
                allow_credentials=True,
                allow_methods=["*"],
                allow_headers=["*"],
            )

        @self.app.get("/")
        def status():
            return f"API: {settings.project_name} is working"

        self.app.include_router(health_router)
        self.app.include_router(v1_routers, prefix=settings.prefix)
        logger.info("Application started: %s", settings.project_name)

    @classmethod
    def reset_for_tests(cls) -> None:
        """Clear singleton instance (pytest only)."""
        cls._instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance


app_creator = AppCreator()
app = app_creator.app
db = app_creator.db
container = app_creator.container
