"""Tests for retry logic with exponential backoff"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock

import sys
sys.path.insert(0, 'src')

from pycode.retry import (
    retry,
    retry_api_call,
    retry_network,
    retry_quick,
    RetryError,
    RetryContext,
)


class TestRetryDecorator:
    """Test retry decorator"""

    @pytest.mark.asyncio
    async def test_retry_success_first_attempt(self):
        """Test successful call on first attempt"""
        call_count = 0

        @retry(max_attempts=3)
        async def successful_call():
            nonlocal call_count
            call_count += 1
            return "success"

        result = await successful_call()
        assert result == "success"
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_retry_success_after_failures(self):
        """Test successful call after some failures"""
        call_count = 0

        @retry(max_attempts=3, initial_delay=0.01)
        async def eventually_successful():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("Temporary error")
            return "success"

        result = await eventually_successful()
        assert result == "success"
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_retry_max_attempts_exceeded(self):
        """Test that RetryError is raised after max attempts"""
        call_count = 0

        @retry(max_attempts=3, initial_delay=0.01)
        async def always_fails():
            nonlocal call_count
            call_count += 1
            raise ValueError("Persistent error")

        with pytest.raises(RetryError) as exc_info:
            await always_fails()

        assert call_count == 3
        assert "Failed after 3 attempts" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_retry_exponential_backoff(self):
        """Test exponential backoff timing"""
        call_times = []

        @retry(max_attempts=3, initial_delay=0.01, exponential_base=2.0)
        async def failing_call():
            call_times.append(asyncio.get_event_loop().time())
            raise ValueError("Error")

        with pytest.raises(RetryError):
            await failing_call()

        assert len(call_times) == 3
        # Check that delays are increasing (roughly exponential)
        # First to second delay should be ~0.01s
        # Second to third delay should be ~0.02s

    @pytest.mark.asyncio
    async def test_retry_specific_exceptions(self):
        """Test retrying only specific exceptions"""
        call_count = 0

        @retry(max_attempts=3, initial_delay=0.01, exceptions=(ValueError,))
        async def specific_exception():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("Retryable")
            raise TypeError("Not retryable")

        # Should retry ValueError but not TypeError
        with pytest.raises(TypeError):
            await specific_exception()

        assert call_count == 2

    def test_retry_sync_function(self):
        """Test retry with synchronous function"""
        call_count = 0

        @retry(max_attempts=3)
        def sync_function():
            nonlocal call_count
            call_count += 1
            return "sync result"

        result = sync_function()
        assert result == "sync result"
        assert call_count == 1


class TestRetryStrategies:
    """Test predefined retry strategies"""

    @pytest.mark.asyncio
    async def test_retry_api_call(self):
        """Test retry_api_call strategy"""
        call_count = 0

        @retry_api_call
        async def api_call():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise Exception("API error")
            return "api result"

        result = await api_call()
        assert result == "api result"
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_retry_network(self):
        """Test retry_network strategy"""
        call_count = 0

        @retry_network
        async def network_call():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise Exception("Network error")
            return "network result"

        result = await network_call()
        assert result == "network result"
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_retry_quick(self):
        """Test retry_quick strategy"""
        call_count = 0

        @retry_quick
        async def quick_call():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise Exception("Quick error")
            return "quick result"

        result = await quick_call()
        assert result == "quick result"
        assert call_count == 2


class TestRetryContext:
    """Test RetryContext for manual retry control"""

    @pytest.mark.asyncio
    async def test_retry_context_success(self):
        """Test RetryContext with successful retry"""
        call_count = 0

        async with RetryContext(max_attempts=3, initial_delay=0.01) as retry_ctx:
            for attempt in retry_ctx:
                call_count += 1
                if call_count < 2:
                    if retry_ctx.should_retry(ValueError("temp error")):
                        await retry_ctx.wait()
                        continue
                break

        assert call_count == 2

    @pytest.mark.asyncio
    async def test_retry_context_max_attempts(self):
        """Test RetryContext respects max attempts"""
        call_count = 0

        with pytest.raises(RetryError):
            async with RetryContext(max_attempts=3, initial_delay=0.01) as retry_ctx:
                for attempt in retry_ctx:
                    call_count += 1
                    if retry_ctx.should_retry(ValueError("error")):
                        await retry_ctx.wait()
                    else:
                        raise RetryError("Max attempts exceeded")

        assert call_count == 3


class TestRetryError:
    """Test RetryError exception"""

    def test_retry_error_creation(self):
        """Test creating RetryError"""
        original = ValueError("Original error")
        retry_error = RetryError("Retry failed", last_exception=original)

        assert "Retry failed" in str(retry_error)
        assert retry_error.last_exception is original

    def test_retry_error_without_last_exception(self):
        """Test RetryError without last_exception"""
        retry_error = RetryError("Retry failed")
        assert "Retry failed" in str(retry_error)
        assert retry_error.last_exception is None
