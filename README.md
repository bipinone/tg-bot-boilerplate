<div align="center">

# TeleCore

**An enterprise-grade, modular Telegram Bot Framework and Starter Kit built with Python and aiogram 3.x.**

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

**TeleCore** is a modular, feature-flagged architecture designed to serve as the immediate base for any Telegram bot project — whether you are building an AI assistant, an SMM panel, a subscription SaaS, a community bot, or a Telegram Mini App.

---

### Key Architectural Pillars

- **Async Core**: Built on Python 3.10+ and `aiogram 3.x` using native asynchronous I/O.
- **Dual Runtime Modes**: Supports both local **Long Polling** and production **Webhooks** via `aiohttp`.
- **Feature-Flagged Modules**: Enable or disable features directly via `.env` flags without editing core application code.
- **Async Persistence Layer**: SQLite default with automatic migrations, seamlessly upgradeable to PostgreSQL.
- **Anti-Flood Middleware**: In-memory and Redis-compatible sliding window rate limiter to prevent API 429 penalties.
- **Telegram Group & Forum Topic Logging**: Real-time alerts for bot startups, new user registrations, and unhandled errors routed to standard channels or specific Supergroup Forum Topics (`message_thread_id`).
- **Docker Compose Stack**: Containerized deployment with optional Redis caching service.

---

### Pluggable Modules

TeleCore features an isolated, modular architecture where features can be toggled via environment variables:

| Module | Flag | Description |
| :--- | :--- | :--- |
| **Admin** | `ENABLE_MODULE_ADMIN=true` | System analytics (`/stats`), access controls (`/ban`, `/unban`), and moderation filters. |
| **Broadcast** | `ENABLE_MODULE_BROADCAST=true` | Safe mass announcements with progress tracking, sleep throttling, and error handling. |
| **Force Subscription** | `ENABLE_MODULE_FORCE_SUB=true` | Middleware enforcing channel/chat membership before granting bot access. |
| **Referrals** | `ENABLE_MODULE_REFERRALS=true` | Deep-link invitation engine (`/start ref_123`), referral counters, and reward points. |
| **Telegram Mini Apps** | `ENABLE_MODULE_MINIAPP=true` | Native WebApp integration buttons and handlers. |
| **AI Assistant** | `ENABLE_MODULE_AI=true` | Pluggable streaming endpoint for OpenAI and Google Gemini LLM queries. |
| **Live Support Chat** | `ENABLE_TOPIC_SUPPORT_CHAT=true` | Two-way relay: user DMs forwarded to personal forum topics; admin replies in topic sent back to user. |
| **Health & Metrics** | `HEALTH_SERVER_ENABLED=true` | Built-in HTTP server (`/health`, `/metrics`) on port 8080 preventing cloud sleeping on Render/Railway/VPS. |
| **Payments** | `ENABLE_MODULE_PAYMENTS=true` | Digital goods invoices and Telegram Stars (`XTR`) checkout handlers. |
| **Analytics** | `ENABLE_MODULE_ANALYTICS=true` | Event logging and active user telemetry. |

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
| `/ref` | Referrals | Public | Returns user's unique referral link and reward points. |
| `/app` | MiniApp | Public | Sends inline launcher for configured Telegram WebApp. |
| `/ask <query>` | AI | Public | Queries the integrated AI assistant module. |
| `/stats` | Admin | Admin Only | Returns total registered users, active counts, and event metrics. |
| `/broadcast <msg>` | Broadcast | Admin Only | Sends mass notification to all users with flood throttling. |
| `/ban <user_id>` | Admin | Admin Only | Revokes bot access for the specified Telegram ID. |
| `/unban <user_id>` | Admin | Admin Only | Restores bot access for a previously banned user. |
| `/export` | Admin | Admin Only | Exports all registered users into a downloadable CSV spreadsheet. |

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
