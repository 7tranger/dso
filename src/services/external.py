import os
from functools import lru_cache
from typing import Any, Dict

from fastapi import HTTPException, status

import src.services.http_client


@lru_cache(maxsize=1)
def get_score_service() -> src.services.http_client.ExternalScoreService:
    base_url = os.getenv("SCORE_API_BASE", "https://example.com")
    client = src.services.http_client.SafeHttpClient(base_url=base_url)
    return src.services.http_client.ExternalScoreService(client)


def fetch_score_or_raise(payload: Dict[str, Any]) -> float:
    service = get_score_service()
    try:
        return service.fetch_score(payload)
    except src.services.http_client.ExternalServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={
                "code": "EXTERNAL_SERVICE_UNAVAILABLE",
                "message": "External scoring service unavailable",
                "details": {},
            },
        ) from exc
