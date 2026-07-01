from fastapi import FastAPI

from app.logging_config import configure_logging
from app.middleware.auth import AuthContextMiddleware
from app.middleware.request_logging import RequestLoggingMiddleware
from app.routers import health

configure_logging()

app = FastAPI(title="approval-service")

app.add_middleware(AuthContextMiddleware)
app.add_middleware(RequestLoggingMiddleware)

app.include_router(health.router)
