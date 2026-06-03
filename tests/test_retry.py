"""Tests for harvest.retry (offline, no real sleeps)."""

from __future__ import annotations

import asyncio

import pytest

from harvest.retry import is_retryable, run_with_attempts, run_with_timeout

# --- exception classification --------------------------------------------------


class HandlerError(Exception):
    pass


class CaptchaDetected(Exception):
    pass


class RequiresManualLogin(Exception):
    pass


class UserSkipped(Exception):
    pass


class AIBudgetExhausted(Exception):
    pass


def test_is_retryable_handler_error() -> None:
    assert is_retryable(HandlerError("boom")) is True


def test_is_retryable_generic_exception() -> None:
    assert is_retryable(ValueError("x")) is True


def test_is_retryable_timeout() -> None:
    assert is_retryable(TimeoutError("slow")) is True


@pytest.mark.parametrize(
    "exc",
    [CaptchaDetected(), RequiresManualLogin(), UserSkipped(), AIBudgetExhausted()],
)
def test_non_retryable_exceptions(exc: Exception) -> None:
    assert is_retryable(exc) is False


def test_cancellation_not_retryable() -> None:
    assert is_retryable(asyncio.CancelledError()) is False
    assert is_retryable(KeyboardInterrupt()) is False


# --- run_with_attempts ---------------------------------------------------------


async def _noop_sleep(_seconds: float) -> None:
    return None


@pytest.mark.asyncio
async def test_succeeds_first_try() -> None:
    calls = 0

    async def op() -> str:
        nonlocal calls
        calls += 1
        return "ok"

    result = await run_with_attempts(op, max_attempts=3, sleep=_noop_sleep)
    assert result == "ok"
    assert calls == 1


@pytest.mark.asyncio
async def test_retries_then_succeeds() -> None:
    calls = 0

    async def op() -> str:
        nonlocal calls
        calls += 1
        if calls < 3:
            raise HandlerError("transient")
        return "recovered"

    result = await run_with_attempts(op, max_attempts=3, sleep=_noop_sleep)
    assert result == "recovered"
    assert calls == 3


@pytest.mark.asyncio
async def test_exhausts_attempts_and_raises_last() -> None:
    calls = 0

    async def op() -> str:
        nonlocal calls
        calls += 1
        raise HandlerError(f"fail-{calls}")

    with pytest.raises(HandlerError, match="fail-2"):
        await run_with_attempts(op, max_attempts=2, sleep=_noop_sleep)
    assert calls == 2


@pytest.mark.asyncio
async def test_non_retryable_stops_immediately() -> None:
    calls = 0

    async def op() -> str:
        nonlocal calls
        calls += 1
        raise CaptchaDetected()

    with pytest.raises(CaptchaDetected):
        await run_with_attempts(
            op, max_attempts=5, retryable=is_retryable, sleep=_noop_sleep
        )
    assert calls == 1  # never retried


@pytest.mark.asyncio
async def test_on_retry_hook_called_with_attempt_and_exc() -> None:
    seen: list[tuple[int, str]] = []

    async def op() -> str:
        raise HandlerError("nope")

    async def on_retry(attempt: int, exc: BaseException) -> None:
        seen.append((attempt, type(exc).__name__))

    with pytest.raises(HandlerError):
        await run_with_attempts(
            op, max_attempts=3, on_retry=on_retry, sleep=_noop_sleep
        )
    # Hook fires before each retry sleep — twice for 3 attempts.
    assert seen == [(1, "HandlerError"), (2, "HandlerError")]


@pytest.mark.asyncio
async def test_backoff_delays_are_exponential() -> None:
    delays: list[float] = []

    async def record_sleep(seconds: float) -> None:
        delays.append(seconds)

    async def op() -> str:
        raise HandlerError("x")

    with pytest.raises(HandlerError):
        await run_with_attempts(
            op, max_attempts=4, backoff_base=1.0, sleep=record_sleep
        )
    assert delays == [1.0, 2.0, 4.0]


@pytest.mark.asyncio
async def test_invalid_max_attempts() -> None:
    async def op() -> str:
        return "x"

    with pytest.raises(ValueError):
        await run_with_attempts(op, max_attempts=0)


@pytest.mark.asyncio
async def test_cancelled_error_propagates_without_retry() -> None:
    calls = 0

    async def op() -> str:
        nonlocal calls
        calls += 1
        raise asyncio.CancelledError()

    with pytest.raises(asyncio.CancelledError):
        await run_with_attempts(op, max_attempts=3, sleep=_noop_sleep)
    assert calls == 1


# --- run_with_timeout ----------------------------------------------------------


@pytest.mark.asyncio
async def test_timeout_returns_result_when_fast() -> None:
    async def op() -> str:
        return "quick"

    result = await run_with_timeout(op, timeout_s=5.0, poll_interval_s=0.01)
    assert result == "quick"


@pytest.mark.asyncio
async def test_timeout_fires_when_active() -> None:
    async def op() -> str:
        await asyncio.sleep(10)
        return "never"

    # Fake clock advances 1s per poll; not paused → active time accrues fast.
    ticks = iter([0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0])

    def clock() -> float:
        return next(ticks)

    async def fast_sleep(_s: float) -> None:
        await asyncio.sleep(0)  # yield control without real delay

    with pytest.raises(TimeoutError, match="active wall-clock"):
        await run_with_timeout(
            op,
            timeout_s=3.0,
            poll_interval_s=0.01,
            clock=clock,
            sleep=fast_sleep,
        )


@pytest.mark.asyncio
async def test_timeout_paused_clock_does_not_fire() -> None:
    """While is_paused() is True the clock must not accrue, so a long manual
    takeover never trips the timeout."""
    done = asyncio.Event()

    async def op() -> str:
        await done.wait()
        return "finished after takeover"

    # Clock jumps 100s per tick — would blow any timeout if it counted.
    t = {"v": 0.0}

    def clock() -> float:
        t["v"] += 100.0
        return t["v"]

    poll_count = {"n": 0}

    async def controlled_sleep(_s: float) -> None:
        poll_count["n"] += 1
        # After a few polls, let the operation finish.
        if poll_count["n"] >= 3:
            done.set()
        await asyncio.sleep(0)

    result = await run_with_timeout(
        op,
        timeout_s=1.0,
        is_paused=lambda: True,  # always blocking on user
        poll_interval_s=0.01,
        clock=clock,
        sleep=controlled_sleep,
    )
    assert result == "finished after takeover"
