<div align="center">

# TeleCore

**A production-ready, asynchronous Telegram bot boilerplate built with Python, SQLite, and modular architecture.**

<br />

[![CI](https://img.shields.io/github/actions/workflow/status/bipinone/tg-bot-boilerplate/ci.yml?branch=main&style=flat-square&label=CI&logo=github)](https://github.com/bipinone/tg-bot-boilerplate/actions)
[![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-blue?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-black?style=flat-square)](https://opensource.org/licenses/MIT)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=flat-square&logo=docker&logoColor=white)](#docker-deployment)

<br />

[![Telegram Channel](https://img.shields.io/badge/Telegram-Channel-24A1DE?style=flat-square&logo=telegram&logoColor=white)](https://t.me/BipinOne)
[![Telegram Group](https://img.shields.io/badge/Telegram-Community-24A1DE?style=flat-square&logo=telegram&logoColor=white)](https://t.me/BipinOneChat)
[![Instagram](https://img.shields.io/badge/Instagram-@bipinone-E4405F?style=flat-square&logo=instagram&logoColor=white)](https://www.instagram.com/bipinone)

</div>

---

### Overview

Building a robust Telegram bot often requires repeatedly implementing boilerplate features: database persistence, user registration, administrative controls, broadcast tools, and rate limiting.

**TeleCore** solves this by providing a clean, battle-tested, modular foundation. Clone the repository, configure your environment variables, and start building business logic immediately.

---

### Key Features

- **Async Database Layer**: Non-blocking SQLite storage powered by `aiosqlite` with automatic table creation and user registration.
- **Administrative Command Suite**:
  - `/stats`: Real-time analytics (total users, active users, banned users, message volume).
  - `/broadcast`: Safe mass broadcasting with sleep throttling to prevent Telegram API rate limit blocks.
  - `/ban` & `/unban`: Access control directly from the Telegram chat interface.
- **Anti-Flood Middleware**: Sliding window rate-limiting to protect against spam attacks and Telegram 429 errors.
- **Interactive UI**: Clean inline menu navigation with callback query routing.
- **Graceful Error Handling**: Global exception handler with detailed logging and user notification.
- **Deployment Ready**: Standard `Dockerfile` and `docker-compose.yml` included for one-command deployment.

---

### Project Structure

```text
tg-bot-boilerplate/
├── bot/
│   ├── config.py              # Strongly-typed environment configuration
│   ├── database/
│   │   └── db.py              # Async SQLite persistence engine
│   ├── handlers/
│   │   ├── admin.py           # /stats, /broadcast, /ban, /unban
│   │   ├── common.py          # /start, /help, /ping & menu callbacks
│   │   └── errors.py          # Global exception handler
│   ├── middlewares/
│   │   └── rate_limit.py      # Anti-flood sliding window limiter
│   └── utils/
│       └── keyboards.py       # Reusable inline menu keyboards
├── tests/
│   └── test_core.py           # Automated unit tests for db & limiter
├── .github/workflows/
│   └── ci.yml                 # Multi-version Python CI pipeline
├── .env.example               # Configuration template
├── .gitignore
├── docker-compose.yml
├── Dockerfile
├── LICENSE
├── requirements.txt
└── main.py                    # Application entrypoint & poller
```

---

### Quick Start

#### 1. Clone the Repository

```bash
git clone https://github.com/bipinone/tg-bot-boilerplate.git
cd tg-bot-boilerplate
```

#### 2. Configure Environment

Copy the template configuration file:

```bash
cp .env.example .env
```

Edit `.env` with your credentials:

```ini
BOT_TOKEN=your_bot_token_from_botfather
ADMIN_IDS=123456789,987654321
DATABASE_PATH=bot_database.sqlite3
RATE_LIMIT_SECONDS=1.0
LOG_LEVEL=INFO
```

#### 3. Install & Run Locally

```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start the bot
python main.py
```

---

### Docker Deployment

Run the bot as a background container with persistent storage:

```bash
docker compose up -d --build
```

View live container logs:

```bash
docker compose logs -f
```

---

### Command Reference

| Command | Permission | Description |
| :--- | :--- | :--- |
| `/start` | Public | Registers the user in the database and displays interactive menu. |
| `/help` | Public | Displays command list and instructions. |
| `/ping` | Public | Measures and returns bot latency in milliseconds. |
| `/stats` | Admin | Returns total, active, and banned user counts. |
| `/broadcast <msg>` | Admin | Sends text or copies replied message to all registered users. |
| `/ban <user_id>` | Admin | Blocks a user from using the bot. |
| `/unban <user_id>` | Admin | Restores a previously banned user's access. |

---

### Running Tests

Execute the built-in test suite:

```bash
python -m unittest discover tests
```

---

### Connect & Community

For updates, questions, and discussions:

- **Telegram Channel**: [@BipinOne](https://t.me/BipinOne)
- **Telegram Group**: [@BipinOneChat](https://t.me/BipinOneChat)
- **Instagram**: [@bipinone](https://www.instagram.com/bipinone)

---

### License

Distributed under the [MIT License](LICENSE).
