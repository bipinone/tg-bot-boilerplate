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

    async def set_user_language(self, user_id: int, language_code: str) -> bool:
        """Set preferred language for a user."""
        return False

    async def update_user_activity(
        self,
        user_id: int,
        username: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Update last_seen and detect username/name changes."""
        return None

    # --- Group / Chat Management ---
    async def upsert_group(
        self,
        chat_id: int,
        title: str,
        chat_type: str = "supergroup",
        is_active: bool = True
    ) -> bool:
        """Register or update group chat details."""
        return False

    async def get_group(self, chat_id: int) -> Optional[Dict[str, Any]]:
        """Retrieve group record by chat_id."""
        return None

    async def get_all_active_group_ids(self) -> List[int]:
        """Retrieve all registered active group chat IDs."""
        return []

    async def set_group_setting(self, chat_id: int, key: str, value: str) -> None:
        """Update per-group setting."""
        pass

    async def get_group_setting(self, chat_id: int, key: str, default: Optional[str] = None) -> Optional[str]:
        """Retrieve per-group setting value."""
        return default

    # --- Subscriptions & Entitlements ---
    async def create_subscription(self, user_id: int, plan: str, duration_days: int = 30) -> Dict[str, Any]:
        """Create or extend user subscription."""
        return {"user_id": user_id, "plan": plan, "is_active": True}

    async def get_user_subscription(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Retrieve current subscription status for user."""
        return None

    async def is_subscription_active(self, user_id: int) -> bool:
        """Check if user has a non-expired subscription."""
        return False

    async def get_expiring_subscriptions(self, within_days: int = 1) -> List[Dict[str, Any]]:
        """Find subscriptions expiring soon for notification/renewal."""
        return []

    @abstractmethod
    async def close(self) -> None:

        """Gracefully release connection pools or database connections."""
        pass

