"""
Retry Logic with Exponential Backoff

Handles transient failures for API calls and network operations.
"""

import asyncio
import functools
from typing import Callable, Type, TypeVar, Union, Tuple
from .logging import get_logger

T = TypeVar('T')


class RetryError(Exception):
    """Raised when all retry attempts are exhausted"""
    def __init__(self, message: str, last_exception: Exception):
        super().__init__(message)
        self.last_exception = last_exception


def retry(
    max_attempts: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    on_retry: Union[Callable, None] = None
):
    """Retry decorator with exponential backoff

    Args:
        max_attempts: Maximum number of retry attempts
        initial_delay: Initial delay in seconds
        max_delay: Maximum delay between retries
        exponential_base: Base for exponential backoff calculation
        exceptions: Tuple of exception types to catch and retry
        on_retry: Optional callback function called on each retry

    Usage:
        @retry(max_attempts=3, initial_delay=2.0)
        async def fetch_data():
            # API call that might fail
            return await client.get("/data")

        @retry(
            max_attempts=5,
            exceptions=(httpx.HTTPError, TimeoutError),
            on_retry=lambda attempt, delay, exc: print(f"Retry {attempt} after {delay}s")
        )
        async def robust_api_call():
            # Your code here
            pass
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs) -> T:
            logger = get_logger()
            last_exception = None

            for attempt in range(1, max_attempts + 1):
                try:
                    return await func(*args, **kwargs)

                except exceptions as e:
                    last_exception = e

                    # Don't retry on last attempt
                    if attempt == max_attempts:
                        logger.error(
                            f"All {max_attempts} retry attempts failed",
                            function=func.__name__,
                            error=str(e)
                        )
                        raise RetryError(
                            f"Failed after {max_attempts} attempts: {str(e)}",
                            last_exception=e
                        )

                    # Calculate delay with exponential backoff
                    delay = min(
                        initial_delay * (exponential_base ** (attempt - 1)),
                        max_delay
                    )

                    logger.warning(
                        f"Attempt {attempt}/{max_attempts} failed, retrying",
                        function=func.__name__,
                        delay=f"{delay:.1f}s",
                        error=str(e)
                    )

                    # Call retry callback if provided
                    if on_retry:
                        try:
                            on_retry(attempt, delay, e)
                        except Exception as callback_error:
                            logger.debug(
                                "Retry callback failed",
                                error=str(callback_error)
                            )

                    # Wait before retrying
                    await asyncio.sleep(delay)

            # Should never reach here, but just in case
            raise RetryError(
                f"Failed after {max_attempts} attempts",
                last_exception=last_exception or Exception("Unknown error")
            )

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs) -> T:
            """Synchronous version of retry wrapper"""
            import time
            logger = get_logger()
            last_exception = None

            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)

                except exceptions as e:
                    last_exception = e

                    if attempt == max_attempts:
                        logger.error(
                            f"All {max_attempts} retry attempts failed",
                            function=func.__name__,
                            error=str(e)
                        )
                        raise RetryError(
                            f"Failed after {max_attempts} attempts: {str(e)}",
                            last_exception=e
                        )

                    delay = min(
                        initial_delay * (exponential_base ** (attempt - 1)),
                        max_delay
                    )

                    logger.warning(
                        f"Attempt {attempt}/{max_attempts} failed, retrying",
                        function=func.__name__,
                        delay=f"{delay:.1f}s",
                        error=str(e)
                    )

                    if on_retry:
                        try:
                            on_retry(attempt, delay, e)
                        except Exception as callback_error:
                            logger.debug(
                                "Retry callback failed",
                                error=str(callback_error)
                            )

                    time.sleep(delay)

            raise RetryError(
                f"Failed after {max_attempts} attempts",
                last_exception=last_exception or Exception("Unknown error")
            )

        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


# Predefined retry strategies
def retry_api_call(func: Callable[..., T]) -> Callable[..., T]:
    """Retry strategy optimized for API calls

    - 4 attempts total
    - 2s initial delay
    - Exponential backoff up to 16s
    """
    return retry(
        max_attempts=4,
        initial_delay=2.0,
        max_delay=16.0,
        exponential_base=2.0
    )(func)


def retry_network(func: Callable[..., T]) -> Callable[..., T]:
    """Retry strategy for network operations

    - 3 attempts total
    - 1s initial delay
    - Exponential backoff up to 10s
    """
    return retry(
        max_attempts=3,
        initial_delay=1.0,
        max_delay=10.0,
        exponential_base=2.0
    )(func)


def retry_quick(func: Callable[..., T]) -> Callable[..., T]:
    """Quick retry strategy for fast operations

    - 2 attempts total
    - 0.5s delay
    - No exponential backoff
    """
    return retry(
        max_attempts=2,
        initial_delay=0.5,
        max_delay=0.5,
        exponential_base=1.0
    )(func)


# Context manager for explicit retry control
class RetryContext:
    """Context manager for manual retry control

    Usage:
        async with RetryContext(max_attempts=3) as retry_ctx:
            for attempt in retry_ctx:
                try:
                    result = await api_call()
                    break  # Success
                except Exception as e:
                    if not retry_ctx.should_retry(e):
                        raise
                    await retry_ctx.wait()
    """

    def __init__(
        self,
        max_attempts: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0
    ):
        self.max_attempts = max_attempts
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.current_attempt = 0
        self.logger = get_logger()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return False

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        return False

    def __iter__(self):
        """Iterate over retry attempts"""
        for attempt in range(1, self.max_attempts + 1):
            self.current_attempt = attempt
            yield attempt

    def should_retry(self, exception: Exception) -> bool:
        """Check if should retry after this exception"""
        return self.current_attempt < self.max_attempts

    async def wait(self):
        """Wait before next retry attempt"""
        delay = min(
            self.initial_delay * (self.exponential_base ** (self.current_attempt - 1)),
            self.max_delay
        )

        self.logger.debug(
            f"Waiting {delay:.1f}s before retry",
            attempt=self.current_attempt,
            max_attempts=self.max_attempts
        )

        await asyncio.sleep(delay)

    def get_delay(self) -> float:
        """Get the current delay duration"""
        return min(
            self.initial_delay * (self.exponential_base ** (self.current_attempt - 1)),
            self.max_delay
        )
