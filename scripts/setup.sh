#!/usr/bin/env bash
set -e

echo "=========================================================="
echo "🚀 TeleCore: Quickstart Setup Script"
echo "=========================================================="

# 1. Verify Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.10+ first."
    exit 1
fi

PY_VER=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo "✔ Detected Python $PY_VER"

# 2. Virtual Environment
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment in ./venv..."
    python3 -m venv venv
else
    echo "✔ Virtual environment already exists."
fi

# 3. Activate venv
source venv/bin/activate
echo "✔ Virtual environment activated."

# 4. Install dependencies
echo "📥 Installing dependencies from requirements.txt..."
pip install --upgrade pip
pip install -r requirements.txt

# 5. Environment configuration
if [ ! -f ".env" ]; then
    echo "📝 Creating .env from .env.example..."
    cp .env.example .env
    echo "⚠️ Please edit .env and insert your BOT_TOKEN from @BotFather!"
else
    echo "✔ .env file exists."
fi

echo ""
echo "=========================================================="
echo "🎉 TeleCore setup complete!"
echo "=========================================================="
echo "Next steps:"
echo "  1. Add your BOT_TOKEN in .env"
echo "  2. Run: source venv/bin/activate"
echo "  3. Start the bot: make dev (or python -m app.main)"
echo "=========================================================="
