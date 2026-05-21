"""
Helper Functions
"""

from typing import List, Any, Optional, TypeVar, Iterator
import uuid
import re
import json
from datetime import datetime
from urllib.parse import urlparse
import hashlib

T = TypeVar("T")


def generate_uuid() -> str:
    """Generate a random UUID string."""
    return str(uuid.uuid4())


def generate_short_id(length: int = 8) -> str:
    """Generate a short random ID."""
    return uuid.uuid4().hex[:length]


def slugify(text: str, max_length: int = 50) -> str:
    """
    Convert text to a URL-friendly slug.
    
    Args:
        text: Text to slugify
        max_length: Maximum length of slug
        
    Returns:
        Slugified text
    """
    # Convert to lowercase
    slug = text.lower()
    
    # Replace non-alphanumeric characters with hyphens
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    
    # Remove leading/trailing hyphens
    slug = slug.strip("-")
    
    # Truncate
    if len(slug) > max_length:
        slug = slug[:max_length].rsplit("-", 1)[0]
    
    return slug


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Truncate text to a maximum length.
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add when truncated
        
    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    
    truncated = text[: max_length - len(suffix)]
    
    # Try to break at word boundary
    last_space = truncated.rfind(" ")
    if last_space > max_length * 0.7:
        truncated = truncated[:last_space]
    
    return truncated + suffix


def extract_domain(url: str) -> Optional[str]:
    """
    Extract domain from URL.
    
    Args:
        url: URL string
        
    Returns:
        Domain or None
    """
    try:
        parsed = urlparse(url)
        return parsed.netloc or None
    except Exception:
        return None


def format_timestamp(dt: datetime, format: str = "iso") -> str:
    """
    Format datetime to string.
    
    Args:
        dt: Datetime object
        format: Format type ('iso', 'human', 'date')
        
    Returns:
        Formatted string
    """
    if format == "iso":
        return dt.isoformat()
    elif format == "human":
        return dt.strftime("%B %d, %Y at %I:%M %p")
    elif format == "date":
        return dt.strftime("%Y-%m-%d")
    else:
        return dt.strftime(format)


def chunk_list(items: List[T], chunk_size: int) -> Iterator[List[T]]:
    """
    Split a list into chunks.
    
    Args:
        items: List to chunk
        chunk_size: Size of each chunk
        
    Yields:
        List chunks
    """
    for i in range(0, len(items), chunk_size):
        yield items[i : i + chunk_size]


def safe_json_loads(json_str: str, default: Any = None) -> Any:
    """
    Safely parse JSON string.
    
    Args:
        json_str: JSON string
        default: Default value if parsing fails
        
    Returns:
        Parsed value or default
    """
    try:
        return json.loads(json_str)
    except (json.JSONDecodeError, TypeError):
        return default


def safe_json_dumps(obj: Any, default: str = "{}") -> str:
    """
    Safely serialize to JSON string.
    
    Args:
        obj: Object to serialize
        default: Default value if serialization fails
        
    Returns:
        JSON string or default
    """
    try:
        return json.dumps(obj, default=str)
    except (TypeError, ValueError):
        return default


def hash_text(text: str, algorithm: str = "sha256") -> str:
    """
    Generate hash of text.
    
    Args:
        text: Text to hash
        algorithm: Hash algorithm
        
    Returns:
        Hex digest
    """
    hasher = hashlib.new(algorithm)
    hasher.update(text.encode("utf-8"))
    return hasher.hexdigest()


def merge_dicts(*dicts: dict) -> dict:
    """
    Merge multiple dictionaries.
    
    Later dictionaries override earlier ones.
    
    Args:
        *dicts: Dictionaries to merge
        
    Returns:
        Merged dictionary
    """
    result = {}
    for d in dicts:
        if d:
            result.update(d)
    return result


def deep_merge(base: dict, override: dict) -> dict:
    """
    Deep merge two dictionaries.
    
    Args:
        base: Base dictionary
        override: Override dictionary
        
    Returns:
        Merged dictionary
    """
    result = base.copy()
    
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    
    return result


def clean_text(text: str) -> str:
    """
    Clean text by removing extra whitespace.
    
    Args:
        text: Text to clean
        
    Returns:
        Cleaned text
    """
    # Replace multiple whitespace with single space
    text = re.sub(r"\s+", " ", text)
    
    # Strip
    text = text.strip()
    
    return text


def extract_numbers(text: str) -> List[float]:
    """
    Extract numbers from text.
    
    Args:
        text: Text to search
        
    Returns:
        List of numbers
    """
    pattern = r"-?\d+\.?\d*"
    matches = re.findall(pattern, text)
    
    numbers = []
    for match in matches:
        try:
            numbers.append(float(match))
        except ValueError:
            pass
    
    return numbers


def ensure_list(value: Any) -> List:
    """
    Ensure value is a list.
    
    Args:
        value: Value to convert
        
    Returns:
        List
    """
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def first_not_none(*args: Any) -> Optional[Any]:
    """
    Return first non-None value.
    
    Args:
        *args: Values to check
        
    Returns:
        First non-None value or None
    """
    for arg in args:
        if arg is not None:
            return arg
    return None


def timeit(func):
    """Decorator to time function execution."""
    import functools
    import time
    import logging
    
    logger = logging.getLogger(__name__)
    
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = time.perf_counter() - start
        logger.debug(f"{func.__name__} took {elapsed:.3f}s")
        return result
    
    @functools.wraps(func)
    async def async_wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = await func(*args, **kwargs)
        elapsed = time.perf_counter() - start
        logger.debug(f"{func.__name__} took {elapsed:.3f}s")
        return result
    
    import asyncio
    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    return wrapper


def retry(max_attempts: int = 3, delay: float = 1.0, backoff: float = 2.0):
    """
    Decorator for retrying failed function calls.
    
    Args:
        max_attempts: Maximum retry attempts
        delay: Initial delay between retries
        backoff: Backoff multiplier
    """
    import functools
    import time
    import logging
    
    logger = logging.getLogger(__name__)
    
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            current_delay = delay
            
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_attempts - 1:
                        raise
                    
                    logger.warning(
                        f"{func.__name__} failed (attempt {attempt + 1}): {e}. "
                        f"Retrying in {current_delay}s..."
                    )
                    time.sleep(current_delay)
                    current_delay *= backoff
        
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            import asyncio
            current_delay = delay
            
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_attempts - 1:
                        raise
                    
                    logger.warning(
                        f"{func.__name__} failed (attempt {attempt + 1}): {e}. "
                        f"Retrying in {current_delay}s..."
                    )
                    await asyncio.sleep(current_delay)
                    current_delay *= backoff
        
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return wrapper
    
    return decorator
