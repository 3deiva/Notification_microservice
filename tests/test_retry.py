import pytest
from unittest.mock import AsyncMock, call
from app.services.retry_service import retry_with_backoff


DUMMY_EVENT = {"event_id": "evt-test", "event_type": "SalaryCredited"}


@pytest.mark.asyncio
async def test_succeeds_first_try():
    func = AsyncMock()
    dlq = AsyncMock()
    await retry_with_backoff(func, DUMMY_EVENT, dlq, max_retries=3, base_delay=0)
    func.assert_called_once_with(DUMMY_EVENT)
    dlq.assert_not_called()


@pytest.mark.asyncio
async def test_retries_and_succeeds():
    results = [Exception("fail"), Exception("fail"), None]
    call_count = 0

    async def func(event):
        nonlocal call_count
        r = results[call_count]
        call_count += 1
        if isinstance(r, Exception):
            raise r

    dlq = AsyncMock()
    await retry_with_backoff(func, DUMMY_EVENT, dlq, max_retries=3, base_delay=0)
    assert call_count == 3
    dlq.assert_not_called()


@pytest.mark.asyncio
async def test_exhausted_retries_sends_to_dlq():
    func = AsyncMock(side_effect=Exception("permanent failure"))
    dlq = AsyncMock()
    await retry_with_backoff(func, DUMMY_EVENT, dlq, max_retries=3, base_delay=0)
    assert func.call_count == 4  # initial + 3 retries
    dlq.assert_called_once_with(DUMMY_EVENT)


@pytest.mark.asyncio
async def test_no_retries_zero_max():
    func = AsyncMock(side_effect=Exception("fail"))
    dlq = AsyncMock()
    await retry_with_backoff(func, DUMMY_EVENT, dlq, max_retries=0, base_delay=0)
    func.assert_called_once()
    dlq.assert_called_once()
