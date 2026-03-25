"""Shared HTTP client singletons.

Provides named ``httpx.AsyncClient`` instances so that every module that needs
outbound HTTP reuses a pooled client instead of creating its own.  Call
:func:`close_all` during application shutdown to release all TCP connections.
"""

import logging

import httpx

logger = logging.getLogger(__name__)

_clients: dict[str, httpx.AsyncClient] = {}


def get_http_client(
    name: str = "default",
    *,
    timeout: float = 10.0,
    max_connections: int = 20,
    max_keepalive_connections: int = 10,
) -> httpx.AsyncClient:
    """Return (or lazily create) a named HTTP client singleton."""
    if name not in _clients:
        _clients[name] = httpx.AsyncClient(
            timeout=timeout,
            limits=httpx.Limits(
                max_connections=max_connections,
                max_keepalive_connections=max_keepalive_connections,
            ),
        )
        logger.debug("Created HTTP client %r", name)
    return _clients[name]


async def close_all() -> None:
    """Close every HTTP client singleton.  Safe to call multiple times."""
    for name, client in list(_clients.items()):
        await client.aclose()
        logger.debug("Closed HTTP client %r", name)
    _clients.clear()
