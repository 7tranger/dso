import os
from functools import lru_cache
from typing import Any, Dict

from fastapi import HTTPException, status

from src.services.http_client import ExternalScoreService, ExternalServiceError, SafeHttpClient


@lru_cache(maxsize=1)
def get_score_service() -> ExternalScoreService:
    base_url = os.getenv("SCORE_API_BASE", "https://example.com")
    client = SafeHttpClient(base_url=base_url)
    return ExternalScoreService(client)


def fetch_score_or_raise(payload: Dict[str, Any]) -> float:
    service = get_score_service()
    try:
        return service.fetch_score(payload)
    except ExternalServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={
                "code": "EXTERNAL_SERVICE_UNAVAILABLE",
                "message": "External scoring service unavailable",
                "details": {},
            },
        ) from exc


