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

**TeleCore** is an extensible, production-oriented starter kit designed to serve as the immediate base for any Telegram bot project — whether you are building an AI assistant, a community manager, a subscription SaaS, a referral campaign, an e-commerce storefront, or a Telegram Mini App.

---

### System Architecture

```text
                                Telegram Bot API
                                       │
                                       ▼
                     ┌──────────────────────────────────┐
                     │   aiogram 3.x Dispatcher Core    │
                     └──────────────────────────────────┘
                                       │
                       [ Global Middleware Pipeline ]
                                       │
          ┌────────────────────────────┼────────────────────────────┐
          ▼                            ▼                            ▼
   Rate Limiting               Ban & Maintenance             Multi-Language
 (Sliding Window)             (Instant Eviction)             (i18n Resolver)
          │                            │                            │
          └────────────────────────────┼────────────────────────────┘
                                       │
                                       ▼
                       [ Pluggable Feature Routers ]
      ┌──────────────┬──────────────┬──────────────┬──────────────┐
      │              │              │              │              │
    Admin        Broadcast     Subscriptions       AI          Groups / CRM
   (/panel)    (-copy, -pin)   (Free/Pro/VIP)  (Multi-LLM)     (Topic Relay)
      │              │              │              │              │
      └──────────────┴──────────────┼──────────────┴──────────────┘
                                       │
                                       ▼
                 ┌───────────────────────────────────────────┐
                 │  High-Performance DatabaseSession (DAL)   │
                 │   └─ In-Memory Sub-Millisecond TTL Cache  │
                 └───────────────────────────────────────────┘
                                       │
            ┌──────────────┬───────────┴──┬──────────────┐
            ▼              ▼              ▼              ▼
         SQLite        PostgreSQL       MySQL         MongoDB
       (aiosqlite)     (asyncpg)      (aiomysql)      (motor)
```

---

### Key Architectural Pillars

- **Async Core & Blazing Speed**: Built on Python 3.10+ and `aiogram 3.x` with native `uvloop` C-based event loops, `orjson` serialization, and sub-millisecond in-memory TTL caching.
- **Multi-Database Provider (Pluggable DAL)**: Native async driver support for **SQLite** (`aiosqlite`), **PostgreSQL** (`asyncpg`), **MySQL/MariaDB** (`aiomysql`), and **MongoDB** (`motor`). Switch engines simply by setting `DB_TYPE` or `DATABASE_URL`!
- **Internationalization (i18n)**: Clean multi-language architecture (English, Hindi) with per-user preference stored in DB, translation helper `_()`, and an interactive `/language` menu.
- **Subscriptions & Entitlements Engine**: Decoupled SaaS membership engine (Free, Pro, VIP tiers) with expiry tracking, renewal reminders, and entitlement gates.
- **Community & Group Engine**: Automatic group registration on bot join, supergroup forum topic handling, and group-level configuration.
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
│   │   ├── filters/           # Custom filters (IsAdminFilter, IsOwnerFilter)
│   │   ├── handlers/          # Core handlers (/start, /help, /ping)
│   │   ├── keyboards/         # Reusable inline and reply keyboards
│   │   ├── middlewares/       # Anti-flood, ban checks, and i18n
│   │   └── states/            # Finite State Machine (FSM) definitions
│   │
│   ├── database/
│   │   ├── adapters/          # Engine adapters (sqlite, postgres, mysql, mongo)
│   │   ├── base.py            # Abstract Base Database Provider interface
│   │   ├── cache.py           # Sub-millisecond in-memory TTL cache
│   │   ├── factory.py         # Dynamic connection string resolution
│   │   └── session.py         # Unified DatabaseSession with auto-caching
│   │
│   ├── modules/               # Pluggable feature modules
│   │   ├── admin/             # Admin dashboard, stats, RBAC, moderation
│   │   ├── ai/                # Multi-provider LLM queries & conversation memory
│   │   ├── broadcast/         # Mass messaging engine with visual progress bar
│   │   ├── force_sub/         # Channel gatekeeper middleware
│   │   ├── groups/            # Community registrations and event listeners
│   │   ├── i18n/              # Localization locales, service, and router
│   │   ├── miniapp/           # WebApp integration launcher
│   │   ├── payments/          # Digital goods and Telegram Stars checkout
│   │   ├── referrals/         # Deep-link referral tracking and rewards
│   │   ├── scheduler/         # Background recurring job engine
│   │   └── support/           # Two-way supergroup topic CRM relay
│   │
│   ├── services/              # Logger, health server, background helpers
│   ├── cli.py                 # TeleCore Developer CLI (make:module, db:seed)
│   ├── config.py              # Strongly-typed environment configuration
│   └── main.py                # Dispatcher assembly and runner
│
├── scripts/
│   ├── setup.sh               # Self-healing automated setup for Linux, macOS, WSL & Termux
│   ├── setup.py               # Universal cross-platform setup engine (Any OS)
│   ├── setup.ps1              # Native automated PowerShell setup for Windows
│   └── telecore.service       # Production systemd daemon unit template
├── tests/
│   └── test_framework.py      # Automated unit test suite (18 test cases)
├── docker-compose.yml         # Container orchestration (App + Redis)
├── Dockerfile                 # Multi-stage production container
├── Makefile                   # Developer workflow shortcuts
├── requirements.txt           # Production dependencies
└── README.md
```

---

### Quick Start

#### Method A: One-Command Automated Setup (All Operating Systems)

TeleCore includes an **intelligent, self-healing setup engine** that automatically detects your Operating System, auto-installs missing system tools, auto-remedies missing `python3-venv` packages, validates Python 3.10+, and configures your `.env` interactively.

##### 🐧 Linux / 🍎 macOS / 🪟 WSL:
```bash
git clone https://github.com/bipinone/tg-bot-boilerplate.git
cd tg-bot-boilerplate
chmod +x scripts/setup.sh
./scripts/setup.sh
```

##### 📱 Android Mobile (Termux):
```bash
# 1. Install prerequisites in Termux
pkg update -y && pkg install -y git python

# 2. Clone & run automated self-healing setup
git clone https://github.com/bipinone/tg-bot-boilerplate.git
cd tg-bot-boilerplate
bash scripts/setup.sh

# 3. Keep bot running 24/7 without Android killing it
termux-wake-lock
source venv/bin/activate
python -m app.main
```

##### 🪟 Windows (PowerShell):
```powershell
git clone https://github.com/bipinone/tg-bot-boilerplate.git
cd tg-bot-boilerplate
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\scripts\setup.ps1
```

##### 🌐 Universal Runner (Any OS with Python installed):
```bash
python scripts/setup.py   # Or: python3 scripts/setup.py
```

> [!TIP]
> **Self-Healing & Auto-Fix Capabilities:**
> - **Debian / Ubuntu `python3-venv` Fix:** Automatically detects and resolves the common `ensurepip is not available` / `python3-venv` error via `apt-get` or fallback virtualenv bootstrap.
> - **Package Manager Auto-Detection:** Automatically invokes `apt`, `dnf`, `yum`, `pacman`, `apk`, `zypper`, `pkg` (Termux), or `brew` (macOS) if Python or build tools are missing.
> - **Build Tools & Wheel Auto-Repair:** If C-extension wheels fail to compile, automatically installs development headers or safely falls back to pure-asyncio core drivers so the bot works out of the box.
> - **Interactive Bot Token Validation:** Securely prompts for `BOT_TOKEN` from [@BotFather](https://t.me/BotFather), validates syntax, and injects it into `.env`.
> - **Pre-Flight Health Verification:** Performs instant dry-run import verification before concluding.

#### Method B: Manual Virtual Environment

```bash
# 1. Clone repository
git clone https://github.com/bipinone/tg-bot-boilerplate.git
cd tg-bot-boilerplate

# 2. Setup virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env and insert your BOT_TOKEN from @BotFather

# 5. Launch bot
python -m app.main
```

---

### Multi-Database Configuration

TeleCore is designed with a **Universal Database Abstraction Layer**. You can switch database backends at any time without altering application code.

Simply configure `.env`:

#### 1. SQLite (Default Zero-Config):
```ini
DB_TYPE=sqlite
SQLITE_PATH=bot_database.sqlite3
```

#### 2. PostgreSQL (High Concurrency):
```ini
DATABASE_URL=postgresql://user:password@localhost:5432/telecore_bot
```
*TeleCore automatically provisions connection pools via `asyncpg` with a 5-20 connection pool.*

#### 3. MySQL / MariaDB:
```ini
DATABASE_URL=mysql://user:password@localhost:3306/telecore_bot
```
*Powered by `aiomysql` with DictCursor mapping.*

#### 4. MongoDB (Document Database):
```ini
DATABASE_URL=mongodb://localhost:27017/telecore_bot
# Or MongoDB Atlas:
# DATABASE_URL=mongodb+srv://user:pass@cluster0.mongodb.net/telecore_bot
```
*Powered by `motor` async driver with auto-indexing on `user_id`.*

---

### Developer CLI & Module Generator

TeleCore features an artisan-style code generator to scaffold new feature modules in seconds:

```bash
python -m app.cli make:module shop
```

This immediately creates:
```text
app/modules/shop/
├── __init__.py        # Clean router export
├── handlers.py        # Pre-wired command entrypoint
├── keyboards.py       # Inline/reply keyboards
├── services.py        # Isolated business logic class
├── schemas.py         # Pydantic data models
└── config.py          # Feature flag dataclass
```

#### Seed Demo Data:
```bash
python -m app.cli db:seed
```

#### Developer Workflow (`Makefile`):

```bash
make dev           # Start bot in development mode
make test          # Execute automated test suite (17 tests)
make seed          # Seed database with superadmin accounts
make module name=x # Scaffold a new module
make docker-up     # Launch Docker Compose stack
make docker-down   # Stop containers
make clean         # Purge cached bytecode
```

---

### Docker Deployment

To launch TeleCore and Redis as isolated background containers:

```bash
docker compose up -d --build
```

View live container logs:

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
| `/ask <query>` | AI | Public | Queries the integrated multi-provider AI assistant. |
| `/clear_ai` | AI | Public | Resets conversation memory buffer for current user. |
| `/ai_model` | AI | Public | Displays active AI provider, model, and memory size. |
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

### Production Deployment & Hardening

#### 1. Webhook Mode with Nginx Reverse Proxy
In `.env`:
```ini
WEBHOOK_ENABLED=true
WEBHOOK_HOST=127.0.0.1
WEBHOOK_PORT=8080
WEBHOOK_URL=https://your-domain.com/webhook
```

Nginx configuration snippet:
```nginx
server {
    server_name your-domain.com;

    location /webhook {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

#### 2. Systemd Service Setup
Copy the included service file:
```bash
sudo cp telecore.service /etc/systemd/system/telecore.service
sudo systemctl daemon-reload
sudo systemctl enable --now telecore
```

#### 3. Environment Security Audit
Audit your environment file against secret leaks and unsynced parameters:
```bash
npx @bipinone/envshield check
```

---

### Running Automated Tests

TeleCore includes a comprehensive, asynchronous test suite covering database adapters, caching, middlewares, i18n, and CLI generation:

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
