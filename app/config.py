import os
from dataclasses import dataclass, field
from typing import List, Optional
from dotenv import load_dotenv

load_dotenv()

def _parse_bool(value: Optional[str], default: bool = False) -> bool:
    if value is None:
        return default
    return str(value).lower().strip() in ("1", "true", "yes", "on", "t")

def _parse_list_ints(value: Optional[str]) -> List[int]:
    if not value:
        return []
    result = []
    for item in value.split(","):
        clean = item.strip()
        if clean.isdigit():
            result.append(int(clean))
    return result

@dataclass
class BotConfig:
    token: str = field(default_factory=lambda: os.getenv("BOT_TOKEN", ""))
    admins: List[int] = field(default_factory=lambda: _parse_list_ints(os.getenv("ADMIN_IDS", "")))
    rate_limit: float = field(default_factory=lambda: float(os.getenv("RATE_LIMIT_SECONDS", "1.0")))
    drop_pending_updates: bool = field(default_factory=lambda: _parse_bool(os.getenv("DROP_PENDING_UPDATES", "true"), True))

@dataclass
class DatabaseConfig:
    url: str = field(default_factory=lambda: os.getenv("DATABASE_URL", "sqlite+aiosqlite:///bot_database.sqlite3"))
    sqlite_path: str = field(default_factory=lambda: os.getenv("SQLITE_PATH", "bot_database.sqlite3"))

@dataclass
class RedisConfig:
    enabled: bool = field(default_factory=lambda: _parse_bool(os.getenv("REDIS_ENABLED", "false")))
    url: str = field(default_factory=lambda: os.getenv("REDIS_URL", "redis://localhost:6379/0"))

@dataclass
class WebhookConfig:
    enabled: bool = field(default_factory=lambda: _parse_bool(os.getenv("WEBHOOK_ENABLED", "false")))
    host: str = field(default_factory=lambda: os.getenv("WEBHOOK_HOST", "0.0.0.0"))
    port: int = field(default_factory=lambda: int(os.getenv("WEBHOOK_PORT", "8080")))
    path: str = field(default_factory=lambda: os.getenv("WEBHOOK_PATH", "/webhook"))
    url: str = field(default_factory=lambda: os.getenv("WEBHOOK_URL", ""))

@dataclass
class ModuleFlags:
    admin: bool = field(default_factory=lambda: _parse_bool(os.getenv("ENABLE_MODULE_ADMIN", "true"), True))
    broadcast: bool = field(default_factory=lambda: _parse_bool(os.getenv("ENABLE_MODULE_BROADCAST", "true"), True))
    force_sub: bool = field(default_factory=lambda: _parse_bool(os.getenv("ENABLE_MODULE_FORCE_SUB", "false")))
    referrals: bool = field(default_factory=lambda: _parse_bool(os.getenv("ENABLE_MODULE_REFERRALS", "false")))
    ai: bool = field(default_factory=lambda: _parse_bool(os.getenv("ENABLE_MODULE_AI", "false")))
    payments: bool = field(default_factory=lambda: _parse_bool(os.getenv("ENABLE_MODULE_PAYMENTS", "false")))
    miniapp: bool = field(default_factory=lambda: _parse_bool(os.getenv("ENABLE_MODULE_MINIAPP", "false")))
    analytics: bool = field(default_factory=lambda: _parse_bool(os.getenv("ENABLE_MODULE_ANALYTICS", "true"), True))

def _parse_optional_int(value: Optional[str]) -> Optional[int]:
    if not value:
        return None
    clean = value.strip()
    return int(clean) if clean.lstrip("-").isdigit() else None

@dataclass
class LoggingConfig:
    chat_id: Optional[int] = field(default_factory=lambda: _parse_optional_int(os.getenv("LOG_CHAT_ID", "")))
    thread_id: Optional[int] = field(default_factory=lambda: _parse_optional_int(os.getenv("LOG_THREAD_ID", "")))
    level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))

@dataclass
class AppConfig:
    bot: BotConfig = field(default_factory=BotConfig)
    db: DatabaseConfig = field(default_factory=DatabaseConfig)
    redis: RedisConfig = field(default_factory=RedisConfig)
    webhook: WebhookConfig = field(default_factory=WebhookConfig)
    modules: ModuleFlags = field(default_factory=ModuleFlags)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    log_level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))

config = AppConfig()
