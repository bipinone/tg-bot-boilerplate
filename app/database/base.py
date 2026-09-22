from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List

class BaseDatabaseAdapter(ABC):
    """Abstract interface defining required database operations for TeleCore."""

    @abstractmethod
    async def init_models(self) -> None:
        """Initialize database schema, tables, or collections."""
        pass

    @abstractmethod
    async def upsert_user(
        self,
        user_id: int,
        username: Optional[str],
        first_name: str,
        last_name: Optional[str] = None,
        language_code: Optional[str] = "en",
        referrer_id: Optional[int] = None
    ) -> bool:
        """Register or update user; returns True if new user, False otherwise."""
        pass

    @abstractmethod
    async def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Retrieve user record by user_id."""
        pass

    @abstractmethod
    async def get_all_active_user_ids(self) -> List[int]:
        """Retrieve all active (unbanned) user IDs for broadcasting."""
        pass

    @abstractmethod
    async def get_all_users(self) -> List[Dict[str, Any]]:
        """Retrieve all registered users for CSV export."""
        pass

    @abstractmethod
    async def set_ban(self, user_id: int, is_banned: bool = True, reason: Optional[str] = None) -> bool:
        """Ban or unban a user with an optional reason."""
        pass

    @abstractmethod
    async def is_user_banned(self, user_id: int) -> bool:
        """Check if user is banned."""
        pass

    @abstractmethod
    async def log_event(self, user_id: int, event_name: str) -> None:
        """Log an analytics telemetry event."""
        pass

    @abstractmethod
    async def get_stats(self) -> Dict[str, Any]:
        """Retrieve system statistics (total users, active, banned, events)."""
        pass

    @abstractmethod
    async def get_referral_count(self, user_id: int) -> int:
        """Get number of users invited by user_id."""
        pass

    @abstractmethod
    async def set_user_topic(self, user_id: int, topic_id: int) -> bool:
        """Link a forum topic thread ID to a user."""
        pass

    @abstractmethod
    async def get_user_topic(self, user_id: int) -> Optional[int]:
        """Get the linked forum topic ID for a user."""
        pass

    @abstractmethod
    async def get_user_by_topic(self, topic_id: int) -> Optional[Dict[str, Any]]:
        """Find a user record linked to a specific topic ID."""
        pass

    @abstractmethod
    async def set_user_role(self, user_id: int, role: str) -> bool:
        """Set user RBAC role ('owner', 'admin', 'moderator', 'user')."""
        pass

    @abstractmethod
    async def get_user_role(self, user_id: int) -> str:
        """Get user RBAC role."""
        pass

    @abstractmethod
    async def get_staff_users(self) -> List[Dict[str, Any]]:
        """Get list of all staff members (owner, admin, moderator)."""
        pass

    @abstractmethod
    async def set_setting(self, key: str, value: str) -> None:
        """Save a dynamic system setting override."""
        pass

    @abstractmethod
    async def get_setting(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Retrieve a dynamic system setting override."""
        pass

    @abstractmethod
    async def get_all_settings(self) -> Dict[str, str]:
        """Retrieve all dynamic system settings."""
        pass

    @abstractmethod
    async def close(self) -> None:
        """Gracefully release connection pools or database connections."""
        pass
