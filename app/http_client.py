import httpx


def get_http_client(
    timeout_connect: float = 2.0,
    timeout_read: float = 3.0,
    timeout_write: float = 3.0,
    timeout_pool: float = 2.0,
) -> httpx.Client:
    timeout = httpx.Timeout(
        connect=timeout_connect,
        read=timeout_read,
        write=timeout_write,
        pool=timeout_pool,
    )
    limits = httpx.Limits(max_keepalive_connections=10, max_connections=50)
    return httpx.Client(timeout=timeout, limits=limits)
