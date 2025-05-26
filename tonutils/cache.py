import functools
import hashlib
import inspect
from types import FunctionType
from typing import Callable, Coroutine, Any, TypeVar, cast

from cachetools import TTLCache

F = TypeVar("F", bound=Callable[..., Coroutine[Any, Any, Any]])

cache_registry: dict[int, TTLCache] = {}


def get_cache(ttl: int, maxsize: int = 10_000) -> TTLCache:
    """
    Get or create a TTLCache instance for the specified TTL.

    :param ttl: Time-to-live in seconds for cache entries.
    :param maxsize: Maximum number of entries in the cache.
    :return: A cachetools.TTLCache instance associated with the given TTL.
    """
    if ttl not in cache_registry:
        cache_registry[ttl] = TTLCache(maxsize=maxsize, ttl=ttl)
    return cache_registry[ttl]


def normalize_arguments(func: Callable[..., Any], *args, **kwargs) -> dict:
    """
    Normalize function arguments into a consistent kwargs dictionary.

    This ensures that calls with the same logical arguments but different
    positional/keyword formats produce the same result.
    Additionally, removes common instance/context arguments like 'self', 'cls', or 'client'.
    """
    sig = inspect.signature(func)
    bound = sig.bind(*args, **kwargs)
    bound.apply_defaults()

    skip_names = {"self", "cls", "client"}
    return {k: v for k, v in bound.arguments.items() if k not in skip_names}


def make_args_key(func: Callable[..., Any], *args, **kwargs) -> str:
    """
    Create a stable cache key based on the function's fully qualified name and normalized arguments.

    The key includes:
    - The function's module.
    - The function's qualified name.
    - Normalized and sorted arguments.
    """
    real_func = cast(FunctionType, func)
    normalized = normalize_arguments(real_func, *args, **kwargs)
    key_string = f"{real_func.__module__}.{real_func.__qualname__}:{sorted(normalized.items())}"
    return hashlib.sha256(key_string.encode()).hexdigest()


def async_cache(ttl: int = 60 * 60 * 24) -> Callable[[F], F]:
    """
    Decorator for caching asynchronous function results using a global TTLCache registry.
    Each unique TTL value corresponds to a separate shared TTLCache instance.

    :param ttl: Time-to-live in seconds for cached results (default: 24 hours).
    :return: A decorator for caching the decorated asynchronous function.
    """

    def decorator(func: F) -> F:
        cache = get_cache(ttl)

        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            key = make_args_key(func, *args, **kwargs)
            if key in cache:
                return cache[key]

            result = await func(*args, **kwargs)
            cache[key] = result
            return result

        return cast(F, wrapper)

    return decorator
