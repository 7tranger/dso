import uuid

from fastapi import FastAPI, HTTPException, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from src.adapters.db import init_db
from src.app.api import router as api_router

app = FastAPI(
    title="Idea Kanban API",
    version="0.1.0",
    docs_url="/docs",
    redoc_url=None,
    openapi_url="/openapi.json",
)


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):  # type: ignore[override]
        corr_id = request.headers.get("X-Correlation-Id") or uuid.uuid4().hex
        request.state.correlation_id = corr_id
        response = await call_next(request)
        response.headers["X-Correlation-Id"] = corr_id
        return response


app.add_middleware(CorrelationIdMiddleware)


@app.on_event("startup")
def on_startup() -> None:
    """Initialize database on application startup."""
    init_db()


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    if isinstance(exc.detail, dict) and "code" in exc.detail:
        return JSONResponse(status_code=exc.status_code, content=exc.detail)

    if request.url.path.startswith("/api/v1"):
        message = exc.detail if isinstance(exc.detail, str) else "HTTP error"
        code = "HTTP_ERROR"
        if exc.status_code == 401 and message == "Not authenticated":
            code = "UNAUTHORIZED"
        payload = {"code": code, "message": message, "details": {}}
        return JSONResponse(status_code=exc.status_code, content=payload)

    message = exc.detail if isinstance(exc.detail, str) else "HTTP error"
    payload = {"code": "HTTP_ERROR", "message": message, "details": {}}
    return JSONResponse(status_code=exc.status_code, content=payload)


@app.exception_handler(RequestValidationError)
async def request_validation_exception_handler(
    request: Request, exc: RequestValidationError
):
    payload = {
        "code": "VALIDATION_ERROR",
        "message": "Request validation failed",
        "details": {"errors": exc.errors()},
    }
    return JSONResponse(status_code=422, content=jsonable_encoder(payload))


@app.get("/health")
def health():
    return {"status": "ok"}


app.include_router(api_router)
