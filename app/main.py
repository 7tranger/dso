import os
import uuid
from typing import Optional

from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

app = FastAPI(title="SecDev Course App", version="0.2.0")


MAX_UPLOAD_BYTES = 1_000_000  # ~1MB
ALLOWED_MIME = {"image/png", "image/jpeg"}
UPLOAD_DIR = os.path.join(os.getcwd(), "uploads")


def ensure_upload_dir() -> None:
    if not os.path.exists(UPLOAD_DIR):
        os.makedirs(UPLOAD_DIR, exist_ok=True)
    if os.path.islink(UPLOAD_DIR):
        raise RuntimeError("Upload directory must not be a symlink")


def get_extension_for_mime(mime: str) -> str:
    if mime == "image/png":
        return ".png"
    if mime == "image/jpeg":
        return ".jpg"
    return ".bin"


def detect_magic_prefix(data: bytes) -> Optional[str]:
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if data.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    return None



class CorrelationIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):  # type: ignore[override]
        corr_id = request.headers.get("X-Correlation-Id") or uuid.uuid4().hex
        request.state.correlation_id = corr_id
        response = await call_next(request)
        response.headers["X-Correlation-Id"] = corr_id
        return response


app.add_middleware(CorrelationIdMiddleware)


def validate_and_format_name(name: str) -> str:
    if not name:
        raise ApiError("validation_error", "name cannot be empty", 422)

    cleaned = name.strip()

    if len(cleaned) < 1:
        raise ApiError("validation_error", "name too short", 422)

    if len(cleaned) > 100:
        raise ApiError("validation_error", "name too long", 422)

    return cleaned


class ApiError(Exception):
    def __init__(self, code: str, message: str, status: int = 400):
        self.code = code
        self.message = message
        self.status = status


def problem_response(
    request: Request, status: int, title: str, detail: str, type_: str = "about:blank"
) -> JSONResponse:
    body = {
        "type": type_,
        "title": title,
        "status": status,
        "detail": detail,
        "correlation_id": getattr(request.state, "correlation_id", None),
    }
    return JSONResponse(
        status_code=status, content=body, media_type="application/problem+json"
    )


@app.exception_handler(ApiError)
async def api_error_handler(request: Request, exc: ApiError):
    title = "Validation error" if exc.status == 422 else "Application error"
    type_url = f"/problems/{exc.code}"
    return problem_response(
        request, status=exc.status, title=title, detail=exc.message, type_=type_url
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    detail = exc.detail if isinstance(exc.detail, str) else "HTTP error"
    return problem_response(
        request,
        status=exc.status_code,
        title="HTTP error",
        detail=detail,
        type_="/problems/http_error",
    )


@app.get("/health")
def health():
    return {"status": "ok"}


# Example minimal entity (for tests/demo)
_DB = {"items": []}


@app.post("/items")
def create_item(name: str):
    formatted_name = validate_and_format_name(name)
    item = {"id": len(_DB["items"]) + 1, "name": formatted_name}
    _DB["items"].append(item)
    return item


@app.get("/items/{item_id}")
def get_item(item_id: int):
    for it in _DB["items"]:
        if it["id"] == item_id:
            return it
    raise ApiError(code="not_found", message="item not found", status=404)


@app.post("/upload")
async def upload_file(request: Request, file: UploadFile = File(...)):
    ensure_upload_dir()

    if file.content_type not in ALLOWED_MIME:
        raise ApiError(code="invalid_mime", message="Unsupported MIME type", status=415)

    total = 0
    chunks = []
    while True:
        data = await file.read(64 * 1024)
        if not data:
            break
        total += len(data)
        if total > MAX_UPLOAD_BYTES:
            return problem_response(
                request,
                status=413,
                title="Payload Too Large",
                detail="File exceeds size limit",
                type_="/problems/payload_too_large",
            )
        chunks.append(data)

    content = b"".join(chunks)
    magic_mime = detect_magic_prefix(content[:16])
    if magic_mime is None or magic_mime != file.content_type:
        raise ApiError(
            code="invalid_signature",
            message="File signature does not match MIME",
            status=422,
        )

    ext = get_extension_for_mime(file.content_type)
    safe_name = f"{uuid.uuid4().hex}{ext}"
    dest_path = os.path.join(UPLOAD_DIR, safe_name)
    if os.path.exists(dest_path) and os.path.islink(dest_path):
        raise ApiError(
            code="unsafe_path", message="Refusing to write to symlink", status=400
        )

    with open(dest_path, "wb") as f:
        f.write(content)

    return {
        "stored_filename": safe_name,
        "size": len(content),
        "content_type": file.content_type,
    }
