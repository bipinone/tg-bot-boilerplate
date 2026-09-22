#!/usr/bin/env python3
# TeleCore Telegram Bot Framework - Universal Cross-Platform Setup Engine
# Author: bipinone (https://github.com/bipinone)
# Repository: https://github.com/bipinone/tg-bot-boilerplate
"""
Universal, self-healing automated setup script for TeleCore.
Compatible with: Linux, macOS, Windows, Android (Termux), BSD.
Features:
- Auto-detects OS and environment
- Auto-recovers from missing virtual environment / ensurepip packages
- Auto-installs and verifies dependencies with fallback for build-less systems
- Interactive Telegram Bot Token configuration and validation
- Pre-flight import health check
"""

import os
import sys
import platform
import subprocess
import shutil
import re
from pathlib import Path

# ANSI Terminal Colors
class Colors:
    HEADER = "\033[95m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BOLD = "\033[1m"
    RESET = "\033[0m"

# Disable colors on Windows if ANSI is unsupported
if platform.system() == "Windows" and os.getenv("TERM") is None:
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
    except Exception:
        for attr in dir(Colors):
            if not attr.startswith("__"):
                setattr(Colors, attr, "")

def print_banner():
    banner = f"""
{Colors.CYAN}{Colors.BOLD}========================================================================
⚡ TeleCore Telegram Bot Framework — Automated Cross-Platform Setup
👨‍💻 Author: bipinone (https://github.com/bipinone)
📦 Repo:   https://github.com/bipinone/tg-bot-boilerplate
========================================================================{Colors.RESET}
"""
    print(banner)

def log_info(msg: str):
    print(f"{Colors.BLUE}[INFO]{Colors.RESET} {msg}")

def log_success(msg: str):
    print(f"{Colors.GREEN}[✔ SUCCESS]{Colors.RESET} {msg}")

def log_warning(msg: str):
    print(f"{Colors.YELLOW}[▲ WARNING]{Colors.RESET} {msg}")

def log_error(msg: str):
    print(f"{Colors.RED}[✖ ERROR]{Colors.RESET} {msg}")

def check_python_version() -> bool:
    log_info(f"Checking Python version on {platform.system()} ({platform.machine()})...")
    major, minor, micro = sys.version_info.major, sys.version_info.minor, sys.version_info.micro
    version_str = f"{major}.{minor}.{micro}"
    
    if sys.version_info < (3, 10):
        log_error(f"Detected Python {version_str}. TeleCore requires Python 3.10 or higher!")
        if platform.system() == "Linux":
            log_info("On Ubuntu/Debian, install Python 3.11+: sudo apt update && sudo apt install -y python3.11 python3.11-venv")
        elif platform.system() == "Darwin":
            log_info("On macOS, install via Homebrew: brew install python@3.11")
        elif platform.system() == "Windows":
            log_info("On Windows, download Python 3.11+ from https://www.python.org/downloads/ and ensure 'Add to PATH' is checked.")
        return False
    
    log_success(f"Python {version_str} meets requirements (>= 3.10).")
    return True

def get_venv_paths(venv_dir: Path):
    if platform.system() == "Windows":
        python_exe = venv_dir / "Scripts" / "python.exe"
        pip_exe = venv_dir / "Scripts" / "pip.exe"
        activate_cmd = f"{venv_dir}\\Scripts\\activate"
    else:
        python_exe = venv_dir / "bin" / "python"
        pip_exe = venv_dir / "bin" / "pip"
        activate_cmd = f"source {venv_dir}/bin/activate"
    return python_exe, pip_exe, activate_cmd

def create_virtualenv(venv_dir: Path) -> Path:
    log_info(f"Setting up virtual environment in: {venv_dir}...")
    python_exe, pip_exe, _ = get_venv_paths(venv_dir)

    # If venv exists and python binary exists, verify health
    if python_exe.exists():
        log_success(f"Existing virtual environment detected at {venv_dir}.")
        return python_exe

    # Try creating with built-in venv module
    try:
        import venv
        builder = venv.EnvBuilder(with_pip=True)
        builder.create(str(venv_dir))
    except Exception as exc:
        log_warning(f"Standard venv creation failed: {exc}")
        log_info("Attempting auto-recovery with fallback virtualenv mechanisms...")

        # Subprocess attempt with ensurepip fallback
        try:
            res = subprocess.run([sys.executable, "-m", "venv", str(venv_dir)], capture_output=True, text=True)
            if res.returncode != 0:
                raise RuntimeError(res.stderr)
        except Exception as sub_exc:
            log_warning(f"Subprocess venv failed: {sub_exc}")
            # Try pip-installed virtualenv
            try:
                subprocess.run([sys.executable, "-m", "pip", "install", "--user", "virtualenv"], check=True)
                subprocess.run([sys.executable, "-m", "virtualenv", str(venv_dir)], check=True)
            except Exception as venv_exc:
                log_error(f"Auto-recovery for virtual environment failed: {venv_exc}")
                log_info("If on Ubuntu/Debian, please run: sudo apt install -y python3-venv python3-pip")
                sys.exit(1)

    if not python_exe.exists():
        log_error(f"Virtual environment created but python binary not found at {python_exe}!")
        sys.exit(1)

    log_success("Virtual environment created successfully.")
    return python_exe

def install_dependencies(python_exe: Path, requirements_file: Path):
    log_info("Upgrading pip, setuptools, and wheel in virtual environment...")
    try:
        subprocess.run([str(python_exe), "-m", "pip", "install", "--upgrade", "pip", "setuptools", "wheel"], check=True)
    except Exception as e:
        log_warning(f"Pip upgrade encountered non-fatal notice: {e}")

    log_info(f"Installing dependencies from {requirements_file.name}...")
    try:
        subprocess.run([str(python_exe), "-m", "pip", "install", "-r", str(requirements_file)], check=True)
        log_success("All dependencies installed successfully.")
    except subprocess.CalledProcessError:
        log_warning("Standard installation had compilation or wheel errors. Attempting auto-fix...")

        # If on Linux, suggest or attempt installing build essentials
        if platform.system() == "Linux":
            log_info("Attempting fallback install with --no-cache-dir and binary-preferred flags...")
            try:
                subprocess.run([str(python_exe), "-m", "pip", "install", "--only-binary=:all:", "-r", str(requirements_file)], check=True)
                log_success("Installed binary dependencies.")
                return
            except Exception:
                pass

        # Fallback to installing core framework dependencies
        log_info("Installing core framework dependencies without optional C-extensions...")
        core_packages = [
            "aiogram>=3.13.0",
            "pydantic>=2.7.0",
            "pydantic-settings>=2.2.0",
            "python-dotenv>=1.0.1",
            "aiohttp>=3.9.5",
            "cachetools>=5.3.0",
            "aiosqlite>=0.20.0"
        ]
        try:
            subprocess.run([str(python_exe), "-m", "pip", "install"] + core_packages, check=True)
            log_success("Core dependencies installed successfully! Bot is ready to run on SQLite.")
        except Exception as fatal_e:
            log_error(f"Fatal error installing dependencies: {fatal_e}")
            sys.exit(1)

def configure_environment(root_dir: Path):
    env_file = root_dir / ".env"
    env_example = root_dir / ".env.example"

    if not env_file.exists():
        if env_example.exists():
            shutil.copy(env_example, env_file)
            log_success("Created .env from .env.example template.")
        else:
            log_warning(".env.example not found, creating minimal .env file...")
            env_file.write_text("BOT_TOKEN=\nBOT_ADMINS=\nDB_TYPE=sqlite\n")

    # Read current .env
    content = env_file.read_text(encoding="utf-8")
    bot_token_configured = False
    
    match = re.search(r"^\s*BOT_TOKEN\s*=\s*(.+)$", content, re.MULTILINE)
    if match:
        token_val = match.group(1).strip().strip('"').strip("'")
        if token_val and token_val != "your_bot_token_here" and len(token_val) > 20:
            bot_token_configured = True

    if bot_token_configured:
        log_success("BOT_TOKEN is already configured in .env.")
        return

    # Check if interactive terminal
    if sys.stdin.isatty():
        print(f"\n{Colors.YELLOW}{Colors.BOLD}--- Interactive Bot Configuration ---{Colors.RESET}")
        print("You can obtain a Bot Token by messaging @BotFather on Telegram.")
        try:
            token_input = input("🤖 Enter your Telegram BOT_TOKEN (or press Enter to skip): ").strip()
            if token_input:
                # Basic token format validation: 123456789:ABCdefGhIjkLmNoPqRsTuVwXyZ
                if ":" in token_input and len(token_input) > 25:
                    if re.search(r"^\s*BOT_TOKEN\s*=.*$", content, re.MULTILINE):
                        content = re.sub(r"^\s*BOT_TOKEN\s*=.*$", f"BOT_TOKEN={token_input}", content, flags=re.MULTILINE)
                    else:
                        content += f"\nBOT_TOKEN={token_input}\n"
                    env_file.write_text(content, encoding="utf-8")
                    masked = token_input[:6] + "..." + token_input[-4:]
                    log_success(f"Configured BOT_TOKEN: {masked}")
                else:
                    log_warning("Invalid token format provided. Please edit .env manually before starting.")
            
            admin_input = input("👑 Enter your numeric Telegram User ID (optional, press Enter to skip): ").strip()
            if admin_input and admin_input.isdigit():
                content = env_file.read_text(encoding="utf-8")
                if re.search(r"^\s*BOT_ADMINS\s*=.*$", content, re.MULTILINE):
                    content = re.sub(r"^\s*BOT_ADMINS\s*=.*$", f"BOT_ADMINS={admin_input}", content, flags=re.MULTILINE)
                else:
                    content += f"\nBOT_ADMINS={admin_input}\n"
                env_file.write_text(content, encoding="utf-8")
                log_success(f"Configured BOT_ADMINS: {admin_input}")
        except (KeyboardInterrupt, EOFError):
            print("\nSkipping interactive configuration.")
    else:
        log_info("Non-interactive mode detected. Please edit .env to insert your BOT_TOKEN.")

def run_health_check(python_exe: Path) -> bool:
    log_info("Running pre-flight framework health check...")
    test_code = """
import aiogram
import aiosqlite
from app.config import config
print("PREFLIGHT_OK")
"""
    try:
        proc = subprocess.run([str(python_exe), "-c", test_code], capture_output=True, text=True, check=True)
        if "PREFLIGHT_OK" in proc.stdout:
            log_success("Pre-flight health check PASSED! All core imports loaded cleanly.")
            return True
    except subprocess.CalledProcessError as exc:
        log_warning(f"Health check notice: {exc.stderr.strip() if exc.stderr else exc}")
    return False

def print_next_steps(activate_cmd: str):
    print(f"""
{Colors.GREEN}{Colors.BOLD}========================================================================
🎉 TeleCore Setup Completed Successfully!
========================================================================{Colors.RESET}

{Colors.BOLD}Quick Launch Instructions:{Colors.RESET}
  1. Activate your virtual environment:
     {Colors.CYAN}{activate_cmd}{Colors.RESET}

  2. Ensure your BOT_TOKEN is set in {Colors.BOLD}.env{Colors.RESET}

  3. Start the bot:
     {Colors.GREEN}python -m app.main{Colors.RESET}  (or: {Colors.GREEN}make dev{Colors.RESET})

{Colors.BOLD}Useful Workflow Commands:{Colors.RESET}
  • Run test suite:           {Colors.CYAN}python -m unittest discover tests{Colors.RESET} (or make test)
  • Scaffold a new module:    {Colors.CYAN}python -m app.cli make:module <name>{Colors.RESET}
  • Docker deployment:        {Colors.CYAN}docker compose up -d --build{Colors.RESET}

👨‍💻 {Colors.BOLD}Developed with ❤️ by Bipin (@bipinone){Colors.RESET}
📢 Telegram Channel:  https://t.me/BipinOne
💬 Community Chat:    https://t.me/BipinOneChat
⭐ GitHub Repo:       https://github.com/bipinone/tg-bot-boilerplate
========================================================================
""")

def main():
    print_banner()
    root_dir = Path(__file__).resolve().parent.parent
    os.chdir(root_dir)

    if not check_python_version():
        sys.exit(1)

    venv_dir = root_dir / "venv"
    python_exe = create_virtualenv(venv_dir)
    _, _, activate_cmd = get_venv_paths(venv_dir)

    requirements_file = root_dir / "requirements.txt"
    if requirements_file.exists():
        install_dependencies(python_exe, requirements_file)
    else:
        log_warning("requirements.txt not found! Skipping dependency install.")

    configure_environment(root_dir)
    run_health_check(python_exe)
    print_next_steps(activate_cmd)

if __name__ == "__main__":
    main()
