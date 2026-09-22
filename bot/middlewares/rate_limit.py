import time
import logging
from typing import Dict

logger = logging.getLogger(__name__)

class RateLimiter:
    """In-memory sliding window rate limiter per user."""
    def __init__(self, limit_seconds: float = 1.0):
        self.limit_seconds = limit_seconds
        self._user_last_action: Dict[int, float] = {}

    def is_rate_limited(self, user_id: int) -> bool:
        current_time = time.time()
        last_time = self._user_last_action.get(user_id, 0)

        if current_time - last_time < self.limit_seconds:
            return True

        self._user_last_action[user_id] = current_time
        return False
