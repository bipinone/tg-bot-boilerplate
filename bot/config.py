import os
import sys
from dataclasses import dataclass
from typing import List
from dotenv import load_dotenv

load_dotenv()

@dataclass(frozen=True)
class Config:
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
    ADMIN_IDS: List[int] = None
    DATABASE_PATH: str = os.getenv("DATABASE_PATH", "bot_database.sqlite3")
    RATE_LIMIT_SECONDS: float = float(os.getenv("RATE_LIMIT_SECONDS", "1.0"))
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    def __post_init__(self):
        raw_admins = os.getenv("ADMIN_IDS", "")
        admin_list = []
        if raw_admins:
            for admin_str in raw_admins.split(","):
                admin_str = admin_str.strip()
                if admin_str.isdigit():
                    admin_list.append(int(admin_str))
        object.__setattr__(self, "ADMIN_IDS", admin_list)

def load_config() -> Config:
    config = Config()
    return config

config = load_config()
