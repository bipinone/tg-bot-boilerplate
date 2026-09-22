<div align="center">

# TeleCore

**A production-ready, modular Telegram Bot Framework & Starter Kit built with Python and aiogram 3.x.**

<br />

[![CI](https://img.shields.io/github/actions/workflow/status/bipinone/tg-bot-boilerplate/ci.yml?branch=main&style=flat-square&label=CI&logo=github)](https://github.com/bipinone/tg-bot-boilerplate/actions)
[![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-blue?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![aiogram](https://img.shields.io/badge/aiogram-v3.13+-2CA5E0?style=flat-square&logo=telegram&logoColor=white)](https://docs.aiogram.dev/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=flat-square&logo=docker&logoColor=white)](#docker-deployment)
[![License: MIT](https://img.shields.io/badge/License-MIT-black?style=flat-square)](https://opensource.org/licenses/MIT)

<br />

[![Telegram Channel](https://img.shields.io/badge/Telegram-Channel-24A1DE?style=flat-square&logo=telegram&logoColor=white)](https://t.me/BipinOne)
[![Telegram Group](https://img.shields.io/badge/Telegram-Community-24A1DE?style=flat-square&logo=telegram&logoColor=white)](https://t.me/BipinOneChat)
[![Instagram](https://img.shields.io/badge/Instagram-@bipinone-E4405F?style=flat-square&logo=instagram&logoColor=white)](https://www.instagram.com/bipinone)

</div>

---

### Overview

Most Telegram bot starters provide only a basic `/start` handler, forcing developers to rebuild user persistence, rate limiting, administrative tools, and broadcast engines repeatedly for every new project.

**TeleCore** is a modular, feature-flagged architecture designed to serve as the immediate base for any Telegram bot project — whether you are building an AI assistant, a community manager, a subscription SaaS, a referral campaign, or a Telegram Mini App.

---

### Key Architectural Pillars

- **Async Core & Blazing Speed**: Built on Python 3.10+ and `aiogram 3.x` with native `uvloop` C-based event loops, `orjson` serialization, and sub-millisecond in-memory TTL caching.
- **Multi-Database Provider (Pluggable DAL)**: Native async driver support for **SQLite** (`aiosqlite`), **PostgreSQL** (`asyncpg`), **MySQL/MariaDB** (`aiomysql`), and **MongoDB** (`motor`). Switch engines simply by setting `DB_TYPE` or `DATABASE_URL`!
- **Internationalization (i18n)**: Seamless multi-language support (English, Hindi) with per-user language preference and `/language` selector.
- **Subscriptions & Entitlements**: Decoupled SaaS membership engine (Free, Pro, VIP tiers) with expiry tracking and access gates.
- **Community & Group Engine**: Group event listeners, supergroup forum topic handling, and group-level settings.
- **Background Task Scheduler**: Async recurring job scheduler for daily routines, subscription expiry notifications, and database cleanup.
- **Flag-Based Mass Broadcast**: High-speed broadcast engine supporting flags (`-copy`, `-pin`, `-silent`, `-fast`), live visual progress bars, and pause/resume/cancel controls.
- **AI Engine**: Multi-provider LLM support (OpenAI, Gemini, Anthropic, Custom endpoints) with per-user conversation memory.
- **Dual Runtime Modes**: Supports both local **Long Polling** and production **Webhooks** via `aiohttp`.
- **Anti-Flood & Global Security**: Sliding window rate limiter, ban enforcement with reasons, and maintenance mode filters.
- **Telegram Group & Forum Topic Logging**: Real-time alerts for bot startups, new user registrations, and unhandled errors routed to standard channels or specific Supergroup Forum Topics (`message_thread_id`).
- **In-Bot Control Panel**: Dynamic `/panel` for instant setting toggles without restarting containers.
- **Module Generator CLI**: Scaffold clean feature modules with a single command (`python -m app.cli make:module <name>`).
- **Docker Compose Stack**: Containerized deployment with optional Redis caching service.

---

### Pluggable Modules

TeleCore features an isolated, modular architecture where features can be toggled via environment variables:

| Module | Location | Description |
| :--- | :--- | :--- |
| **i18n** | `modules/i18n/` | Multi-language localization (English, Hindi) with `/language` selection. |
| **Subscriptions** | `modules/subscriptions/` | SaaS plan tiers (Pro/VIP), expiry warnings, and entitlement verification. |
| **Groups** | `modules/groups/` | Community management, group tracking, and supergroup settings. |
| **Scheduler** | `modules/scheduler/` | Async background job runner for maintenance and subscription reminders. |
| **Admin** | `modules/admin/` | Analytics (`/stats`), RBAC (`/setrole`), moderation (`/ban`, `/unban`), `/panel`. |
| **Broadcast** | `modules/broadcast/` | Flag-based mass announcement engine (`-copy`, `-pin`, `-silent`, `-fast`). |
| **AI Assistant** | `modules/ai/` | OpenAI, Gemini, Anthropic & Custom LLM engine with conversation memory. |
| **Force Subscription** | `modules/force_sub/` | Channel membership gatekeeper with real-time in-bot settings. |
| **Referrals** | `modules/referrals/` | Deep-link invitation engine (`/start ref_123`), referral counters, points. |
| **Telegram Mini Apps** | `modules/miniapp/` | Native WebApp integration buttons and handlers. |
| **Live Support Chat** | `modules/support/` | Two-way relay: user DMs forwarded to personal forum topics; admin replies sent back. |
| **Health & Metrics** | `services/health.py` | Embedded HTTP server (`/health`, `/metrics`) preventing cloud sleeping. |
| **Payments** | `modules/payments/` | Digital goods checkout and Telegram Stars (`XTR`) handlers. |


---

### Project Structure

```text
tg-bot-boilerplate/
├── app/
│   ├── bot/
│   │   ├── filters/           # Custom filters (e.g., IsAdminFilter)
│   │   ├── handlers/          # Common application handlers (/start, /help, /ping)
│   │   ├── keyboards/         # Reusable inline and reply keyboards
│   │   ├── middlewares/       # Anti-flood rate limiting and logging
│   │   └── states/            # Finite State Machine (FSM) definitions
│   │
│   ├── database/
│   │   ├── models/            # Schema definitions
│   │   └── session.py         # Async SQLite / PostgreSQL persistence engine
│   │
│   ├── modules/               # Pluggable feature modules
│   │   ├── admin/             # Admin commands and metrics
│   │   ├── broadcast/         # Mass messaging engine
│   │   ├── force_sub/         # Channel gatekeeper middleware
│   │   ├── referrals/         # Deep-linking referral system
│   │   ├── ai/                # LLM & AI integrations
│   │   ├── payments/          # Telegram Stars and invoice processing
│   │   └── miniapp/           # WebApp integration
│   │
│   ├── services/              # Background tasks and caching utilities
│   ├── config.py              # Strongly-typed environment configuration
│   └── main.py                # Dispatcher assembly and runner (Polling/Webhook)
│
├── tests/
│   └── test_framework.py      # Automated unit test suite
├── docker-compose.yml         # Multi-container orchestration (App + Redis)
├── Dockerfile                 # Multi-stage production container
├── Makefile                   # Development workflow shortcuts
├── pyproject.toml             # Package metadata and dependencies
├── requirements.txt           # Production requirements
└── README.md
```

---

### Quick Start

#### 1. Clone the Repository

```bash
git clone https://github.com/bipinone/tg-bot-boilerplate.git
cd tg-bot-boilerplate
```

#### 2. Configure Environment

Copy the configuration template:

```bash
cp .env.example .env
```

Set your Bot Token from [@BotFather](https://t.me/BotFather) and your Telegram User ID:

```ini
BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrSTUvwxYZ
ADMIN_IDS=123456789
RATE_LIMIT_SECONDS=1.0

# Choose your database backend (sqlite | postgres | mysql | mongo):
DB_TYPE=sqlite
SQLITE_PATH=bot_database.sqlite3

# Or provide a universal connection string:
# DATABASE_URL=postgresql://user:password@localhost:5432/telecore_bot
# DATABASE_URL=mysql://user:password@localhost:3306/telecore_bot
# DATABASE_URL=mongodb://localhost:27017/telecore_bot

# Toggle feature modules
ENABLE_MODULE_ADMIN=true
ENABLE_MODULE_BROADCAST=true
ENABLE_MODULE_REFERRALS=true
ENABLE_MODULE_FORCE_SUB=false
```


#### 3. Run Locally

```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Launch bot
python -m app.main
```

---

### Docker Deployment

To launch the bot and Redis stack as background containers:

```bash
docker compose up -d --build
```

Monitor live container logs:

```bash
docker compose logs -f telecore-bot
```

---

### Command Reference

| Command | Module | Permission | Description |
| :--- | :--- | :--- | :--- |
| `/start` | Core | Public | Launches bot menu and parses deep-link referral parameters. |
| `/help` | Core | Public | Displays available command manual and navigation. |
| `/ping` | Core | Public | Returns latency between server and Telegram API. |
| `/language` | i18n | Public | Interactive multi-language picker (English, Hindi). |
| `/sub` | Subscriptions | Public | Check current subscription tier, expiry date, and status. |
| `/plans` | Subscriptions | Public | View available subscription plans (Free, Pro, VIP). |
| `/ref` | Referrals | Public | Returns user's unique referral link and reward points. |
| `/app` | MiniApp | Public | Sends inline launcher for configured Telegram WebApp. |
| `/ask <query>` | AI | Public | Queries the integrated AI assistant module. |
| `/clear_ai` | AI | Public | Resets conversation memory buffer for current user. |
| `/panel` | Admin | Admin Only | Opens the interactive real-time control dashboard with inline toggles. |
| `/stats` | Admin | Admin Only | Returns total registered users, active counts, and event metrics. |
| `/broadcast [flags]` | Broadcast | Admin Only | High-speed mass announcement (`-copy`, `-pin`, `-silent`, `-fast`). |
| `/broadcast_pause` | Broadcast | Admin Only | Pauses an active mass broadcast in real time. |
| `/broadcast_resume` | Broadcast | Admin Only | Resumes a paused mass broadcast. |
| `/broadcast_cancel` | Broadcast | Admin Only | Terminates active broadcast and cancels pending tasks. |
| `/groups` | Groups | Admin Only | Lists all registered active community groups and supergroups. |
| `/grant_sub <id> <plan>` | Admin | Admin Only | Manually grants/extends Pro or VIP membership. |
| `/ban <user_id> [reason]` | Admin | Admin Only | Revokes bot access with reason, notifying the target user. |
| `/unban <user_id>` | Admin | Admin Only | Restores bot access for a previously banned user. |
| `/user <user_id>` | Admin | Admin Only | Inspects user profile, RBAC role, points, and ban history. |
| `/setrole <id> <role>` | Admin | Owner Only | Assigns staff role (`owner`, `admin`, `moderator`, `user`). |
| `/admins` | Admin | Admin Only | Displays the directory of active staff members and permissions. |
| `/set_channel <@ch>` | Admin | Admin Only | Dynamically updates the Force-Sub channel without restarting. |
| `/set_channel_url <url>` | Admin | Admin Only | Updates the custom invite link for Force-Subscription. |
| `/maintenance <on\|off>` | Admin | Admin Only | Toggles maintenance mode (allows staff access while pausing public users). |
| `/export` | Admin | Admin Only | Exports all registered users into a downloadable CSV spreadsheet. |

---

### Developer CLI & Module Generator

TeleCore includes a built-in CLI for rapid feature scaffolding and database operations:

```bash
# Scaffold a brand new feature module in seconds:
python -m app.cli make:module shop

# This generates:
# app/modules/shop/
# ├── __init__.py
# ├── handlers.py
# ├── keyboards.py
# ├── services.py
# ├── schemas.py
# └── config.py

# Seed initial superadmin accounts and defaults:
python -m app.cli db:seed
```

#### Developer Shortcuts (`Makefile`):

```bash
make dev           # Start bot in development mode
make test          # Execute automated test suite
make seed          # Seed database with superadmin accounts
make module name=x # Scaffold a new module
make docker-up     # Launch Docker Compose stack
make docker-down   # Stop containers
```




---

### Running Tests

Execute the automated test suite:

```bash
python -m unittest discover tests
```

---

### Connect & Community

For updates, architectural discussions, and contributions:

- **Telegram Channel**: [@BipinOne](https://t.me/BipinOne)
- **Telegram Group**: [@BipinOneChat](https://t.me/BipinOneChat)
- **Instagram**: [@bipinone](https://www.instagram.com/bipinone)

---

### License

Distributed under the [MIT License](LICENSE).
