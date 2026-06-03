"""Retry helpers with exponential backoff for the harvest pipeline.

The core ``run_with_attempts`` helper is pure and offline-testable: the sleep
function is injectable so tests can run instantly, and the retry decision is
delegated to a classifier predicate.

Retry policy (per the roadmap):
- Retryable: ``HandlerError`` and timeouts (transient navigation/selector flakiness).
- Non-retryable: ``CaptchaDetected``, ``RequiresManualLogin``, ``UserSkipped``,
  ``AIBudgetExhausted`` — these need human action or signal a hard stop, so
  retrying just wastes time and risks duplicate accounts.
"""

from __future__ import annotations

import asyncio
import time
from collections.abc import Awaitable, Callable
from typing import TypeVar

T = TypeVar("T")

# Exceptions that should never be retried (need human action or are terminal).
# Imported lazily inside the classifier to avoid import cycles with handlers.
_NON_RETRYABLE_NAMES = frozenset(
    {
        "CaptchaDetected",
        "RequiresManualLogin",
        "UserSkipped",
        "AIBudgetExhausted",
    }
)


def is_retryable(exc: BaseException) -> bool:
    """Classify whether an exception from a handler run should be retried.

    Pure and dependency-light: matches on the exception's class name (and MRO)
    so it works regardless of where the exception type is defined, and treats
    asyncio/Playwright timeouts as retryable.
    """
    # Cancellation and keyboard interrupts are never "retryable" — they must
    # propagate so the caller can clean up.
    if isinstance(exc, asyncio.CancelledError | KeyboardInterrupt):
        return False

    # Timeouts are transient → retryable.
    if isinstance(exc, TimeoutError):
        return True

    # Walk the class hierarchy and reject if any base is a known non-retryable.
    for klass in type(exc).__mro__:
        if klass.__name__ in _NON_RETRYABLE_NAMES:
            return False

    # HandlerError (and most other handler-raised errors) are transient enough
    # to retry; default to retryable for generic Exceptions too.
    return True


async def run_with_attempts(
    operation: Callable[[], Awaitable[T]],
    *,
    max_attempts: int = 1,
    retryable: Callable[[BaseException], bool] = is_retryable,
    backoff_base: float = 1.0,
    on_retry: Callable[[int, BaseException], Awaitable[None]] | None = None,
    sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
) -> T:
    """Run ``operation`` up to ``max_attempts`` times with exponential backoff.

    Args:
        operation: Zero-arg async callable producing the result.
        max_attempts: Total attempts (1 = no retries).
        retryable: Predicate deciding whether a raised exception is retryable.
        backoff_base: Base seconds; delay before attempt N+1 is
            ``backoff_base * 2**(N-1)`` (1s, 2s, 4s, ... for base=1).
        on_retry: Optional async hook called as ``on_retry(attempt, exc)`` just
            before sleeping, for emitting a RETRY event.
        sleep: Injectable sleep (defaults to ``asyncio.sleep``); tests pass a
            no-op to avoid real delays.

    Returns:
        The result of the first successful ``operation`` call.

    Raises:
        The last exception if all attempts fail or an exception is non-retryable.
    """
    if max_attempts < 1:
        raise ValueError("max_attempts must be >= 1")

    last_exc: BaseException | None = None
    for attempt in range(1, max_attempts + 1):
        try:
            return await operation()
        except (asyncio.CancelledError, KeyboardInterrupt):
            # Never swallow or retry interrupts.
            raise
        except Exception as exc:  # noqa: BLE001 - we re-raise after policy check
            last_exc = exc
            if attempt >= max_attempts or not retryable(exc):
                raise
            if on_retry is not None:
                await on_retry(attempt, exc)
            await sleep(backoff_base * (2 ** (attempt - 1)))

    # Unreachable in practice (loop either returns or raises), but satisfies typing.
    assert last_exc is not None
    raise last_exc


async def run_with_timeout(
    operation: Callable[[], Awaitable[T]],
    *,
    timeout_s: float,
    is_paused: Callable[[], bool] = lambda: False,
    poll_interval_s: float = 0.5,
    clock: Callable[[], float] = time.monotonic,
    sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
) -> T:
    """Run ``operation`` with a wall-clock timeout that pauses while blocked.

    A naive ``asyncio.wait_for`` would kill a provider mid manual takeover (the
    user entering a credit card / SMS code / solving a CAPTCHA). This watchdog
    instead accrues elapsed time only while ``is_paused()`` is False, so the
    clock stops whenever an interactive prompt is open.

    Args:
        operation: Zero-arg async callable to run as a task.
        timeout_s: Max *active* (non-paused) seconds before cancelling.
        is_paused: Predicate returning True while the user is blocking input.
        poll_interval_s: How often the watchdog wakes to tick the clock.
        clock: Monotonic clock source (injectable for tests).
        sleep: Injectable sleep (injectable for tests).

    Returns:
        The operation's result if it finishes within the active-time budget.

    Raises:
        TimeoutError: If active elapsed time exceeds ``timeout_s``.
        Whatever ``operation`` raises otherwise.
    """
    task: asyncio.Task[T] = asyncio.ensure_future(operation())
    active_elapsed = 0.0
    last_tick = clock()

    while True:
        if task.done():
            return task.result()

        await sleep(poll_interval_s)

        now = clock()
        delta = now - last_tick
        last_tick = now
        if not is_paused():
            active_elapsed += delta

        if active_elapsed >= timeout_s and not task.done():
            task.cancel()
            try:
                await task
            except (asyncio.CancelledError, Exception):
                pass
            raise TimeoutError(
                f"provider exceeded {timeout_s:.0f}s active wall-clock budget"
            )
