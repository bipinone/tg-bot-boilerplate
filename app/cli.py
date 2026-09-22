# TeleCore Telegram Bot Framework - CLI Scaffolding Tool
# Author: bipinone (https://github.com/bipinone)
# Repository: https://github.com/bipinone/tg-bot-boilerplate

import sys
import os
import re
import argparse
from pathlib import Path

MODULE_INIT_TEMPLATE = """from app.modules.{name}.handlers import router

__all__ = ["router"]
"""

MODULE_HANDLERS_TEMPLATE = """from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
from app.modules.{name}.services import {class_name}Service
from app.modules.{name}.keyboards import get_{name}_main_markup

router = Router(name="{name}_module")
service = {class_name}Service()

@router.message(Command("{name}"))
async def {name}_entrypoint(message: Message):
    \"\"\"Main entrypoint for {name} module.\"\"\"
    greeting = service.get_greeting(message.from_user.first_name)
    await message.reply(
        f"📦 <b>{title} Module</b>\\n\\n{{greeting}}",
        reply_markup=get_{name}_main_markup(),
        parse_mode="HTML"
    )
"""


MODULE_KEYBOARDS_TEMPLATE = """from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_{name}_main_markup() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✨ Action 1", callback_data="{name}:action_1"),
            InlineKeyboardButton(text="ℹ️ Info", callback_data="{name}:info")
        ]
    ])
"""

MODULE_SERVICES_TEMPLATE = """class {class_name}Service:
    \"\"\"Business logic service for {name} module.\"\"\"

    def get_greeting(self, name: str) -> str:
        return f"Hello, {name}! Welcome to the {title} feature."
"""

MODULE_SCHEMAS_TEMPLATE = """from pydantic import BaseModel, Field
from typing import Optional

class {class_name}Item(BaseModel):
    id: int
    name: str = Field(..., max_length=100)
    description: Optional[str] = None
    is_active: bool = True
"""

MODULE_CONFIG_TEMPLATE = """from dataclasses import dataclass
import os

@dataclass
class {class_name}Config:
    enabled: bool = os.getenv("ENABLE_MODULE_{upper_name}", "true").lower() in ("1", "true", "yes")
"""

def make_module(name: str):
    """Scaffolds a complete feature module in app/modules/<name>/."""
    clean_name = re.sub(r"[^a-zA-Z0-9_]", "", name.lower().strip())
    if not clean_name:
        print("❌ Error: Invalid module name. Use alphanumeric characters and underscores.")
        sys.exit(1)

    base_dir = Path(__file__).resolve().parent / "modules" / clean_name
    if base_dir.exists():
        print(f"⚠️ Error: Module '{clean_name}' already exists at {base_dir}")
        sys.exit(1)

    base_dir.mkdir(parents=True, exist_ok=True)
    class_name = "".join(part.capitalize() for part in clean_name.split("_"))
    title = clean_name.replace("_", " ").title()
    upper_name = clean_name.upper()

    context = {
        "name": clean_name,
        "class_name": class_name,
        "title": title,
        "upper_name": upper_name
    }

    files = {
        "__init__.py": MODULE_INIT_TEMPLATE.format(**context),
        "handlers.py": MODULE_HANDLERS_TEMPLATE.format(**context),
        "keyboards.py": MODULE_KEYBOARDS_TEMPLATE.format(**context),
        "services.py": MODULE_SERVICES_TEMPLATE.format(**context),
        "schemas.py": MODULE_SCHEMAS_TEMPLATE.format(**context),
        "config.py": MODULE_CONFIG_TEMPLATE.format(**context),
    }

    for filename, content in files.items():
        (base_dir / filename).write_text(content, encoding="utf-8")

    print("\n" + "=" * 60)
    print(f"✨ Feature Module '{clean_name}' Scaffolding Complete!")
    print("=" * 60)
    print(f"📁 Location: app/modules/{clean_name}/")
    print(f"   ├── __init__.py")
    print(f"   ├── handlers.py")
    print(f"   ├── keyboards.py")
    print(f"   ├── services.py")
    print(f"   ├── schemas.py")
    print(f"   └── config.py\n")
    print("🚀 To register in app/main.py:")
    print(f"   from app.modules.{clean_name}.handlers import router as {clean_name}_router")
    print(f"   dp.include_router({clean_name}_router)")
    print("=" * 60 + "\n")

def main():
    parser = argparse.ArgumentParser(description="TeleCore Framework CLI Utilities")
    subparsers = parser.add_subparsers(dest="command")

    # make:module <name>
    make_mod_parser = subparsers.add_parser("make:module", help="Scaffold a new feature module")
    make_mod_parser.add_argument("name", help="Name of the module to create (e.g. shop, billing)")

    # db:seed
    subparsers.add_parser("db:seed", help="Seed default demo data into database")

    args = parser.parse_args()

    if args.command == "make:module":
        make_module(args.name)
    elif args.command == "db:seed":
        print("🌱 Seeding initial database records...")
        import asyncio
        from app.database.session import DatabaseSession
        from app.config import config

        async def _seed():
            db = DatabaseSession.from_config(config.db)
            await db.init_models()
            for admin_id in config.bot.admins:
                await db.upsert_user(user_id=admin_id, username="admin", first_name="SuperAdmin")
                await db.set_user_role(admin_id, "owner")
            await db.set_setting("welcome_message", "Welcome to TeleCore!")
            await db.close()
            print("✅ Database seeded successfully with superadmin accounts and initial settings.")

        asyncio.run(_seed())
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
