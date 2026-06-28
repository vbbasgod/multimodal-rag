"""General utility helpers"""
import time
import hashlib
import functools
from typing import Callable, Any


def timer(func: Callable) -> Callable:
    """Decorator: log execution time of async functions"""
    @functools.wraps(func)
    async def wrapper(*args, **kwargs) -> Any:
        start = time.perf_counter()
        result = await func(*args, **kwargs)
        elapsed = (time.perf_counter() - start) * 1000
        print(f"[TIMER] {func.__name__} took {elapsed:.2f}ms")
        return result
    return wrapper


def truncate(text: str, max_chars: int = 200) -> str:
    """Truncate text with ellipsis"""
    return text if len(text) <= max_chars else text[:max_chars] + "…"


def hash_content(content: str) -> str:
    """SHA-256 hash of content string"""
    return hashlib.sha256(content.encode()).hexdigest()


def chunk_list(lst: list, size: int) -> list:
    """Split a list into chunks of given size"""
    return [lst[i:i + size] for i in range(0, len(lst), size)]
