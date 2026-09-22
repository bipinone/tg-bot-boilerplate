import time
from typing import Any, Optional, Dict

class MemoryTTLCache:
    """
    Lightweight, ultra-fast in-memory cache with Time-To-Live (TTL) expiration.
    Eliminates database round-trips for high-frequency checks (is_banned, roles, settings).
    """
    def __init__(self, default_ttl_seconds: float = 60.0):
        self.default_ttl = default_ttl_seconds
        self._store: Dict[str, tuple[Any, float]] = {}

    def get(self, key: str) -> Optional[Any]:
        item = self._store.get(key)
        if item is None:
            return None
        val, expiry = item
        if time.time() > expiry:
            del self._store[key]
            return None
        return val

    def set(self, key: str, value: Any, ttl: Optional[float] = None) -> None:
        expiry = time.time() + (ttl if ttl is not None else self.default_ttl)
        self._store[key] = (value, expiry)

    def delete(self, key: str) -> None:
        self._store.pop(key, None)

    def delete_prefix(self, prefix: str) -> None:
        keys_to_del = [k for k in self._store if k.startswith(prefix)]
        for k in keys_to_del:
            del self._store[k]

    def clear(self) -> None:
        self._store.clear()
