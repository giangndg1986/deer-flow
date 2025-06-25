import time
import random
import logging
from typing import Any, Dict, Optional
from langchain_openai import ChatOpenAI
import openai
from openai import RateLimitError, InternalServerError
import asyncio

logger = logging.getLogger(__name__)

class ChatOpenAIWithRetry(ChatOpenAI):
    """ChatOpenAI with built-in retry mechanism for handling API overload and rate limits"""

    def __init__(self, **kwargs):
        # Extract our custom retry parameters BEFORE calling super().__init__
        max_retries = kwargs.pop('max_retries', 3)
        base_delay = kwargs.pop('base_delay', 1.0)

        # Call parent constructor with remaining kwargs
        super().__init__(**kwargs)

        # Set attributes using object.__setattr__ to bypass Pydantic validation
        object.__setattr__(self, '_max_retries', max_retries)
        object.__setattr__(self, '_base_delay', base_delay)

    def _calculate_delay(self, attempt: int) -> float:
        """Calculate exponential backoff delay with jitter"""
        delay = self._base_delay * (2 ** attempt)
        jitter = random.uniform(0.1, 0.5) * delay
        return delay + jitter

    async def _agenerate_with_retry(self, *args, **kwargs):
        """Generate with retry logic for handling API errors"""
        last_exception = None

        for attempt in range(self._max_retries):
            try:
                logger.info(f"API attempt {attempt + 1}/{self._max_retries}")
                result = await super().agenerate(*args, **kwargs)
                return result

            except (RateLimitError, InternalServerError) as e:
                last_exception = e
                error_code = getattr(e, 'status_code', 'unknown')
                error_str = str(e).lower()

                # Check if this is an Anthropic error (since you're using Anthropic API)
                is_anthropic_error = any(keyword in error_str for keyword in [
                    'overloaded', 'anthropic', 'claude', '529'
                ])

                if attempt < self._max_retries - 1:
                    delay = self._calculate_delay(attempt)
                    api_name = "Anthropic" if is_anthropic_error else "API"
                    logger.warning(
                        f"{api_name} error (code: {error_code}): {str(e)}. "
                        f"Retrying in {delay:.2f} seconds... (attempt {attempt + 1}/{self._max_retries})"
                    )
                    await asyncio.sleep(delay)
                else:
                    api_name = "Anthropic" if is_anthropic_error else "API"
                    logger.error(
                        f"{api_name} failed after {self._max_retries} attempts. "
                        f"Last error: {str(e)}"
                    )

            except Exception as e:
                error_str = str(e).lower()

                # Check if it's a retryable error (network issues, timeouts, etc.)
                is_retryable = any(keyword in error_str for keyword in [
                    'timeout', 'connection', '500', '502', '503', '504',
                    'overloaded', 'rate limit', 'too many requests'
                ])

                if is_retryable and attempt < self._max_retries - 1:
                    delay = self._calculate_delay(attempt)
                    logger.warning(
                        f"Retryable error: {str(e)}. "
                        f"Retrying in {delay:.2f} seconds... (attempt {attempt + 1}/{self._max_retries})"
                    )
                    await asyncio.sleep(delay)
                    last_exception = e
                else:
                    # For other errors, don't retry
                    logger.error(f"Non-retryable error: {str(e)}")
                    raise e

        # If we get here, all retries failed
        raise last_exception

    async def agenerate(self, *args, **kwargs):
        """Override agenerate to use retry logic"""
        return await self._agenerate_with_retry(*args, **kwargs)