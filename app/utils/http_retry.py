import asyncio
import random
import logging
import httpx

logger = logging.getLogger(__name__)

async def request_with_exponential_backoff(
    client: httpx.AsyncClient,
    url: str,
    max_retries: int = 4,
    base_delay: float = 2.0,
    max_delay: float = 30.0,
    **kwargs
) -> httpx.Response:
    """
    Makes an HTTP request with exponential backoff and jitter for retries.
    Expcted formula for delay: delay = min(base_delay * (2 ** attempt), max_delay) + random.uniform(0, 1)
    """

    for attempt in range(1, max_retries + 1):
        try:
            response = await client.get(url, **kwargs)

            # Handle rate limiting and server errors with exponential backoff
            if response.status_code == 429 or response.status_code in (502, 503, 504):
                if attempt == max_retries:
                    logger.error(f"[Backoff] Limit {max_retries} attempts {url}. Status: {response.status_code}")
                    return response

                # 1. Check for Retry-After header -> server response with waiting time
                retry_after = response.headers.get("Retry-After")
                if retry_after and retry_after.isdigit():
                    delay = float(retry_after) + random.uniform(0.5, 1.5)
                else:
                    # 2. Calculate Exponential Backoff with Jitter
                    exponential_delay = min(max_delay, base_delay * (2 ** (attempt - 1)))
                    jitter = random.uniform(0, exponential_delay * 0.5)
                    delay = exponential_delay + jitter

                logger.warning(
                    f"[Rate Limit {response.status_code}] Attempt {attempt}/{max_retries}. "
                    f"Waiting {delay:.2f}s before the next request..."
                )
                await asyncio.sleep(delay)
                continue

            return response

        except (httpx.RequestError, httpx.TimeoutException) as exc:
            if attempt == max_retries:
                logger.error(f"[Network Error] Final failure after {max_retries} attempts: {exc}")
                raise exc

            exponential_delay = min(max_delay, base_delay * (2 ** (attempt - 1)))
            delay = exponential_delay + random.uniform(0.5, 1.5)
            
            logger.warning(
                f"[Connection Error] Attempt {attempt}/{max_retries} failed ({exc}). "
                f"Retrying in {delay:.2f}s..."
            )
            await asyncio.sleep(delay)

    return response