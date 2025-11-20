import threading
import time
from typing import Any, Dict, Optional

import httpx


class ExternalServiceError(Exception):
    """Raised when an external HTTP call fails after retries."""


class SafeHttpClient:
    def __init__(
        self,
        *,
        base_url: str,
        timeout: float = 3.0,
        retries: int = 2,
        backoff_seconds: float = 0.2,
        max_in_flight: int = 5,
        transport: Optional[httpx.BaseTransport] = None,
    ) -> None:
        self._client = httpx.Client(
            base_url=base_url,
            timeout=httpx.Timeout(timeout),
            limits=httpx.Limits(max_connections=10, max_keepalive_connections=5),
            transport=transport,
        )
        self._retries = max(1, retries)
        self._backoff = backoff_seconds
        self._semaphore = threading.BoundedSemaphore(max_in_flight)

    def request(self, method: str, url: str, **kwargs: Any) -> httpx.Response:
        last_exc: Exception | None = None
        for attempt in range(self._retries):
            try:
                with self._semaphore:
                    response = self._client.request(method, url, **kwargs)
                response.raise_for_status()
                return response
            except (httpx.TimeoutException, httpx.HTTPStatusError) as exc:
                last_exc = exc
                if attempt == self._retries - 1:
                    raise ExternalServiceError("External service unavailable") from exc
                time.sleep(self._backoff * (attempt + 1))
        raise ExternalServiceError("External service unavailable") from last_exc

    def post(self, url: str, **kwargs: Any) -> httpx.Response:
        return self.request("POST", url, **kwargs)


class ExternalScoreService:
    def __init__(self, client: SafeHttpClient) -> None:
        self._client = client

    def fetch_score(self, payload: Dict[str, Any]) -> float:
        response = self._client.post("/score", json=payload)
        data = response.json()
        score = data.get("score")
        if score is None:
            raise ExternalServiceError("Malformed response from scoring service")
        return float(score)
