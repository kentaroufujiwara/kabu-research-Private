"""
シンプルな TTL キャッシュ。
- 株価・財務データ: TTL 30分
- ニュース: TTL 15分
- 検索: TTL 5分
"""

import threading
from cachetools import TTLCache
from functools import wraps
from typing import Any, Callable

_lock = threading.Lock()

# キャッシュストア（maxsize は同時保持する銘柄数の上限）
_caches: dict[str, TTLCache] = {
    "company":    TTLCache(maxsize=200, ttl=1800),   # 30分
    "financials": TTLCache(maxsize=200, ttl=1800),   # 30分
    "chart":      TTLCache(maxsize=400, ttl=1800),   # 30分
    "news":       TTLCache(maxsize=200, ttl=900),    # 15分
    "search":     TTLCache(maxsize=500, ttl=300),    # 5分
}


def cached(store: str) -> Callable:
    """指定ストアを使う TTL キャッシュデコレータ。第1引数をキャッシュキーとする。"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # キャッシュキー: 全引数を文字列化
            key = str(args) + str(sorted(kwargs.items()))
            cache = _caches[store]
            with _lock:
                if key in cache:
                    return cache[key]
            result = func(*args, **kwargs)
            with _lock:
                cache[key] = result
            return result
        return wrapper
    return decorator
