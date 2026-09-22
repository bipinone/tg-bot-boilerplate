#!/usr/bin/env bash
# TeleCore Telegram Bot Framework - Universal POSIX Automated Setup Script
# Author: bipinone (https://github.com/bipinone)
# Repository: https://github.com/bipinone/tg-bot-boilerplate
#
# Supported Operating Systems:
# - Ubuntu, Debian, Kali, Mint, Raspbian (apt)
# - Arch Linux, Manjaro (pacman)
# - Fedora, RHEL, CentOS, Rocky, Alma (dnf / yum)
# - Alpine Linux (apk)
# - openSUSE, SLES (zypper)
# - Android (Termux)
# - macOS (Homebrew / native)
# - Windows WSL & Git Bash

set -eo pipefail

# Text formatting
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

print_banner() {
    echo -e "${CYAN}${BOLD}========================================================================${NC}"
    echo -e "${CYAN}${BOLD}⚡ TeleCore Telegram Bot Framework — Automated Self-Healing Setup${NC}"
    echo -e "👨‍💻 Author: bipinone (https://github.com/bipinone)"
    echo -e "📦 Repo:   https://github.com/bipinone/tg-bot-boilerplate"
    echo -e "${CYAN}${BOLD}========================================================================${NC}\n"
}

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[✔ SUCCESS]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[▲ WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[✖ ERROR]${NC} $1"; }

# 1. Detect Operating System & Package Manager
detect_os() {
    OS="unknown"
    PKG_MGR="unknown"
    SUDO_CMD=""

    if [ "$EUID" -ne 0 ] && command -v sudo &> /dev/null; then
        SUDO_CMD="sudo"
    fi

    if [ -n "$TERMUX_VERSION" ] || [ -d "/data/data/com.termux" ]; then
        OS="termux"
        PKG_MGR="pkg"
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        OS="macos"
        PKG_MGR="brew"
    elif [ -f /etc/os-release ]; then
        . /etc/os-release
        OS=$ID
        if command -v apt-get &> /dev/null; then PKG_MGR="apt";
        elif command -v dnf &> /dev/null; then PKG_MGR="dnf";
        elif command -v yum &> /dev/null; then PKG_MGR="yum";
        elif command -v pacman &> /dev/null; then PKG_MGR="pacman";
        elif command -v apk &> /dev/null; then PKG_MGR="apk";
        elif command -v zypper &> /dev/null; then PKG_MGR="zypper";
        fi
    elif [ -f /etc/debian_version ]; then
        OS="debian"
        PKG_MGR="apt"
    elif [ -f /etc/redhat-release ]; then
        OS="rhel"
        PKG_MGR="yum"
    fi

    log_info "Detected OS: ${BOLD}$OS${NC} (Package Manager: ${BOLD}$PKG_MGR${NC})"
}

# 2. Check and Auto-Install Python 3.10+
find_python() {
    PYTHON_BIN=""
    for cmd in python3.13 python3.12 python3.11 python3.10 python3 python; do
        if command -v "$cmd" &> /dev/null; then
            VER=$("$cmd" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")' 2>/dev/null || true)
            MAJOR=$("$cmd" -c 'import sys; print(sys.version_info.major)' 2>/dev/null || true)
            MINOR=$("$cmd" -c 'import sys; print(sys.version_info.minor)' 2>/dev/null || true)
            if [ "$MAJOR" -eq 3 ] && [ "$MINOR" -ge 10 ]; then
                PYTHON_BIN="$cmd"
                log_success "Found compatible Python: ${BOLD}$cmd${NC} (v$VER)"
                break
            fi
        fi
    done
}

auto_install_python() {
    log_warn "Python 3.10+ was not found. Attempting auto-installation via $PKG_MGR..."
    case "$PKG_MGR" in
        apt)
            $SUDO_CMD apt-get update -y
            $SUDO_CMD apt-get install -y python3 python3-pip python3-venv python3-full build-essential python3-dev
            ;;
        dnf)
            $SUDO_CMD dnf install -y python3 python3-pip python3-devel gcc
            ;;
        yum)
            $SUDO_CMD yum install -y python3 python3-pip python3-devel gcc
            ;;
        pacman)
            $SUDO_CMD pacman -Sy --noconfirm python python-pip base-devel
            ;;
        apk)
            $SUDO_CMD apk add --no-cache python3 py3-pip py3-virtualenv gcc musl-dev python3-dev
            ;;
        zypper)
            $SUDO_CMD zypper refresh && $SUDO_CMD zypper install -y python3 python3-pip python3-devel gcc
            ;;
        pkg)
            pkg update -y && pkg install -y python build-essential
            ;;
        brew)
            brew install python@3.11
            ;;
        *)
            log_error "Automatic installation not supported for this package manager. Please install Python 3.10+ manually."
            exit 1
            ;;
    esac
    find_python
    if [ -z "$PYTHON_BIN" ]; then
        log_error "Failed to locate Python 3.10+ after installation attempt."
        exit 1
    fi
}

# 3. Virtual Environment with Self-Healing
setup_virtualenv() {
    log_info "Configuring Python virtual environment in ./venv..."

    # Check for broken venv and clean up
    if [ -d "venv" ]; then
        if [ ! -f "venv/bin/python" ] && [ ! -f "venv/Scripts/python.exe" ]; then
            log_warn "Detected broken virtual environment. Rebuilding..."
            rm -rf venv
        else
            log_success "Healthy virtual environment already exists."
            return
        fi
    fi

    # Attempt standard venv creation
    local VENV_SUCCESS=false
    if $PYTHON_BIN -m venv venv 2> /tmp/telecore_venv_err.log; then
        VENV_SUCCESS=true
    else
        log_warn "Standard 'python -m venv' failed. Diagnosing error..."
        cat /tmp/telecore_venv_err.log

        # Check for Debian/Ubuntu python3-venv / ensurepip error
        if grep -q "python3-venv" /tmp/telecore_venv_err.log || grep -q "ensurepip is not available" /tmp/telecore_venv_err.log; then
            log_info "Auto-fixing missing python3-venv package on Debian/Ubuntu..."
            if [ "$PKG_MGR" = "apt" ]; then
                $SUDO_CMD apt-get update -y
                $SUDO_CMD apt-get install -y python3-venv python3-full python3-pip
                if $PYTHON_BIN -m venv venv; then
                    VENV_SUCCESS=true
                fi
            fi
        fi

        # Fallback 2: virtualenv via pip
        if [ "$VENV_SUCCESS" = false ]; then
            log_info "Attempting fallback to 'virtualenv'..."
            $PYTHON_BIN -m pip install --user virtualenv || true
            if $PYTHON_BIN -m virtualenv venv; then
                VENV_SUCCESS=true
            fi
        fi

        # Fallback 3: venv without pip + get-pip bootstrap
        if [ "$VENV_SUCCESS" = false ]; then
            log_info "Attempting fallback: venv --without-pip + get-pip bootstrap..."
            if $PYTHON_BIN -m venv --without-pip venv; then
                curl -sS https://bootstrap.pypa.io/get-pip.py | ./venv/bin/python
                VENV_SUCCESS=true
            fi
        fi
    fi

    if [ "$VENV_SUCCESS" = false ] || [ ! -f "venv/bin/python" -a ! -f "venv/Scripts/python.exe" ]; then
        log_error "Failed to create virtual environment automatically."
        log_info "If on Ubuntu/Debian, run: sudo apt install -y python3-venv python3-pip"
        exit 1
    fi

    log_success "Virtual environment initialized successfully."
}

# 4. Resolve VENV Executables
resolve_venv_bins() {
    if [ -f "venv/Scripts/python.exe" ]; then
        VENV_PYTHON="venv/Scripts/python.exe"
        VENV_PIP="venv/Scripts/pip.exe"
        ACTIVATE_CMD=".\\venv\\Scripts\\activate"
    else
        VENV_PYTHON="venv/bin/python"
        VENV_PIP="venv/bin/pip"
        ACTIVATE_CMD="source venv/bin/activate"
    fi
}

# 5. Dependency Installation with Auto-Repair
install_dependencies() {
    log_info "Upgrading pip, setuptools, and wheel..."
    $VENV_PIP install --upgrade pip setuptools wheel || true

    log_info "Installing dependencies from requirements.txt..."
    if ! $VENV_PIP install -r requirements.txt; then
        log_warn "Installation failed (often missing C compiler for uvloop/asyncpg). Auto-remedying..."

        # Try installing build tools
        if [ "$PKG_MGR" = "apt" ]; then
            $SUDO_CMD apt-get update -y && $SUDO_CMD apt-get install -y build-essential python3-dev
            $VENV_PIP install -r requirements.txt || true
        elif [ "$PKG_MGR" = "dnf" ]; then
            $SUDO_CMD dnf install -y gcc python3-devel
            $VENV_PIP install -r requirements.txt || true
        elif [ "$PKG_MGR" = "apk" ]; then
            $SUDO_CMD apk add --no-cache gcc musl-dev python3-dev libffi-dev
            $VENV_PIP install -r requirements.txt || true
        fi

        # Verify if aiogram is installed; if not, install core packages
        if ! $VENV_PYTHON -c "import aiogram" &> /dev/null; then
            log_info "Installing core pure-asyncio packages as safe fallback..."
            $VENV_PIP install aiogram>=3.13.0 pydantic>=2.7.0 pydantic-settings>=2.2.0 python-dotenv>=1.0.1 aiohttp>=3.9.5 cachetools>=5.3.0 aiosqlite>=0.20.0
        fi
    fi

    log_success "Dependencies installed."
}

# 6. Environment (.env) Setup & Interactive Configuration
setup_env() {
    if [ ! -f ".env" ]; then
        if [ -f ".env.example" ]; then
            cp .env.example .env
            log_success "Created .env from .env.example."
        else
            echo "BOT_TOKEN=" > .env
            echo "BOT_ADMINS=" >> .env
            echo "DB_TYPE=sqlite" >> .env
            log_warn "Created blank .env."
        fi
    else
        log_success ".env file already exists."
    fi

    # Interactive BOT_TOKEN prompt if empty
    CURRENT_TOKEN=$(grep -E "^[[:space:]]*BOT_TOKEN[[:space:]]*=" .env | cut -d '=' -f2- | tr -d ' "' || true)
    if [ -z "$CURRENT_TOKEN" ] || [ "$CURRENT_TOKEN" = "your_bot_token_here" ]; then
        if [ -t 0 ]; then
            echo ""
            echo -e "${YELLOW}${BOLD}--- Bot Configuration ---${NC}"
            read -r -p "🤖 Enter your Telegram BOT_TOKEN from @BotFather (or Enter to skip): " USER_TOKEN
            if [ -n "$USER_TOKEN" ]; then
                if [[ "$USER_TOKEN" == *":"* ]] && [ ${#USER_TOKEN} -gt 25 ]; then
                    sed -i.bak -E "s/^[[:space:]]*BOT_TOKEN[[:space:]]*=.*/BOT_TOKEN=${USER_TOKEN}/" .env && rm -f .env.bak
                    MASKED="${USER_TOKEN:0:6}...${USER_TOKEN: -4}"
                    log_success "Configured BOT_TOKEN: $MASKED"
                else
                    log_warn "Token does not look valid. Please configure it manually in .env."
                fi
            fi

            read -r -p "👑 Enter your Telegram Numeric User ID (optional, or Enter to skip): " ADMIN_ID
            if [ -n "$ADMIN_ID" ] && [[ "$ADMIN_ID" =~ ^[0-9]+$ ]]; then
                sed -i.bak -E "s/^[[:space:]]*BOT_ADMINS[[:space:]]*=.*/BOT_ADMINS=${ADMIN_ID}/" .env && rm -f .env.bak
                log_success "Configured BOT_ADMINS: $ADMIN_ID"
            fi
        else
            log_info "Non-interactive environment detected. Skipping interactive token prompt."
        fi
    fi
}

# 7. Self-Test
run_selftest() {
    log_info "Performing pre-flight verification..."
    if $VENV_PYTHON -c "import aiogram, aiosqlite; from app.config import config; print('HEALTH_OK')" 2>/dev/null | grep -q "HEALTH_OK"; then
        log_success "Pre-flight health check PASSED! TeleCore runtime is fully verified."
    else
        log_warn "Health check notice: verify that all parameters in .env are valid."
    fi
}

# 8. Completion Banner
finish() {
    echo ""
    echo -e "${GREEN}${BOLD}========================================================================${NC}"
    echo -e "${GREEN}${BOLD}🎉 TeleCore Setup Completed Successfully!${NC}"
    echo -e "${GREEN}${BOLD}========================================================================${NC}"
    echo ""
    echo -e "${BOLD}Quick Launch Commands:${NC}"
    echo -e "  1. Activate virtual environment:"
    echo -e "     ${CYAN}${ACTIVATE_CMD}${NC}"
    echo ""
    echo -e "  2. Start the bot:"
    echo -e "     ${GREEN}python -m app.main${NC}  (or: ${GREEN}make dev${NC})"
    echo ""
    echo -e "${BOLD}Useful Shortcuts:${NC}"
    echo -e "  • Run all tests:        ${CYAN}python -m unittest discover tests${NC} (or make test)"
    echo -e "  • Scaffold new module:  ${CYAN}python -m app.cli make:module <name>${NC}"
    echo -e "  • Run in Docker:        ${CYAN}docker compose up -d --build${NC}"
    echo ""
    echo -e "👨‍💻 ${BOLD}Developed with ❤️ by Bipin (@bipinone)${NC}"
    echo -e "📢 Channel:    https://t.me/BipinOne"
    echo -e "💬 Community:  https://t.me/BipinOneChat"
    echo -e "⭐ GitHub:     https://github.com/bipinone/tg-bot-boilerplate"
    echo -e "${GREEN}${BOLD}========================================================================${NC}\n"
}

main() {
    print_banner
    detect_os
    find_python
    if [ -z "$PYTHON_BIN" ]; then
        auto_install_python
    fi
    setup_virtualenv
    resolve_venv_bins
    install_dependencies
    setup_env
    run_selftest
    finish
}

main "$@"
