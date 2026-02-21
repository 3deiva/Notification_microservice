import asyncio
import json
from typing import Any, Callable, Awaitable

from app.config import settings
from app.config.logging import get_logger

logger = get_logger(__name__)


async def retry_with_backoff(
    func: Callable[..., Awaitable[None]],
    event_data: dict[str, Any],
    dlq_publisher: Callable[[dict], Awaitable[None]],
    max_retries: int = settings.MAX_RETRIES,
    base_delay: float = settings.RETRY_BASE_DELAY,
) -> None:
    """
    Retries `func(event_data)` up to max_retries times with exponential backoff.
    On final failure, calls dlq_publisher to route to dead-letter queue.
    """
    attempt = 0
    last_error: Exception | None = None

    while attempt <= max_retries:
        try:
            if attempt > 0:
                delay = base_delay * (2 ** (attempt - 1))
                logger.info("retry_attempt", attempt=attempt, delay=delay, event_id=event_data.get("event_id"))
                await asyncio.sleep(delay)

            await func(event_data)
            if attempt > 0:
                logger.info("retry_succeeded", attempt=attempt, event_id=event_data.get("event_id"))
            return

        except Exception as e:
            last_error = e
            logger.warning(
                "notification_attempt_failed",
                attempt=attempt,
                max_retries=max_retries,
                event_id=event_data.get("event_id"),
                error=str(e),
            )
            attempt += 1

    # All retries exhausted — send to DLQ
    logger.error(
        "all_retries_exhausted",
        event_id=event_data.get("event_id"),
        error=str(last_error),
    )
    await dlq_publisher(event_data)
