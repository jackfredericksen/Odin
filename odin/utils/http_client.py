"""
HTTP Client Utilities

Provides a shared httpx async client with connection pooling,
retry logic, and proper timeout handling.
"""

import asyncio
import logging
from typing import Any, Dict, Optional

import httpx

logger = logging.getLogger(__name__)


class HTTPClientManager:
    """
    Manages a shared httpx AsyncClient with connection pooling.

    Usage:
        async with await HTTPClientManager.get_client() as client:
            response = await client.get(url)
            data = response.json()

    Or use the convenience method:
        data = await HTTPClientManager.fetch_json(url)
    """

    _client: Optional[httpx.AsyncClient] = None
    _lock = asyncio.Lock()

    # Default configuration
    DEFAULT_TIMEOUT = httpx.Timeout(30.0, connect=10.0, read=20.0)
    MAX_CONNECTIONS = 100
    MAX_KEEPALIVE_CONNECTIONS = 20

    @classmethod
    async def get_client(cls) -> httpx.AsyncClient:
        """
        Get or create the shared client.

        Returns:
            Shared httpx AsyncClient with connection pooling
        """
        if cls._client is None or cls._client.is_closed:
            async with cls._lock:
                # Double-check after acquiring lock
                if cls._client is None or cls._client.is_closed:
                    limits = httpx.Limits(
                        max_connections=cls.MAX_CONNECTIONS,
                        max_keepalive_connections=cls.MAX_KEEPALIVE_CONNECTIONS,
                    )
                    cls._client = httpx.AsyncClient(
                        limits=limits,
                        timeout=cls.DEFAULT_TIMEOUT,
                        headers={
                            "User-Agent": "Odin-Trading-Bot/2.0",
                            "Accept": "application/json",
                        },
                        follow_redirects=True,
                    )
                    logger.info("Created shared HTTP client with connection pooling")

        return cls._client

    @classmethod
    async def close(cls) -> None:
        """Close the shared client."""
        if cls._client and not cls._client.is_closed:
            await cls._client.aclose()
            cls._client = None
            logger.info("Closed shared HTTP client")

    @classmethod
    async def fetch_json(
        cls,
        url: str,
        method: str = "GET",
        timeout: Optional[float] = None,
        retries: int = 3,
        retry_delay: float = 1.0,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Fetch JSON with retry logic.

        Args:
            url: URL to fetch
            method: HTTP method (GET, POST, etc.)
            timeout: Optional custom timeout in seconds
            retries: Number of retry attempts
            retry_delay: Initial delay between retries (exponential backoff)
            **kwargs: Additional arguments for httpx request

        Returns:
            Parsed JSON response

        Raises:
            httpx.HTTPError: On network errors after all retries
            ValueError: On JSON decode errors
        """
        client = await cls.get_client()
        last_error = None

        custom_timeout = httpx.Timeout(timeout) if timeout else None

        for attempt in range(retries):
            try:
                response = await client.request(
                    method,
                    url,
                    timeout=custom_timeout,
                    **kwargs
                )
                response.raise_for_status()
                return response.json()

            except httpx.HTTPStatusError as e:
                # Don't retry on 4xx errors (except 429 rate limit)
                if 400 <= e.response.status_code < 500 and e.response.status_code != 429:
                    raise
                last_error = e

            except (httpx.HTTPError, asyncio.TimeoutError) as e:
                last_error = e

            # Exponential backoff
            if attempt < retries - 1:
                delay = retry_delay * (2 ** attempt)
                logger.warning(
                    f"Request to {url} failed (attempt {attempt + 1}/{retries}), "
                    f"retrying in {delay}s: {last_error}"
                )
                await asyncio.sleep(delay)

        logger.error(f"All {retries} attempts to {url} failed: {last_error}")
        if last_error:
            raise last_error
        raise httpx.HTTPError(f"Failed to fetch {url}")


# Convenience function for simple usage
async def fetch_json(url: str, **kwargs) -> Dict[str, Any]:
    """Fetch JSON from URL using shared client."""
    return await HTTPClientManager.fetch_json(url, **kwargs)


# Cleanup function for application shutdown
async def cleanup_http_client():
    """Clean up HTTP client resources."""
    await HTTPClientManager.close()
