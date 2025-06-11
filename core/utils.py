import os
import random
import logging
from typing import Dict, Any

import requests

from core.exceptions import ScoutConfigurationError


def setup_logging():
    """Configure basic logging"""
    logging.basicConfig(
        format="%(asctime)s - %(levelname)s - %(message)s",
        level=logging.INFO
    )


def log(msg: str):
    """Log a message to both console and log file"""
    logging.info(msg)
    print(msg)


def load_env_vars(required_vars: list) -> Dict[str, Any]:
    """Load and validate required environment variables"""
    from dotenv import load_dotenv
    load_dotenv()

    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        raise ScoutConfigurationError(
            f"Missing required environment variables: {', '.join(missing_vars)}"
        )

    return {var: os.getenv(var) for var in required_vars}


def random_delay(base_seconds: float) -> float:
    """Add random jitter to a delay time"""
    jitter = base_seconds * 0.3  # 30% jitter
    delay = base_seconds + random.uniform(-jitter, jitter)
    return max(0, delay)


def save_run_number(run_num: int, file_path: str = "run_number.txt"):
    """Persist run number to file"""
    with open(file_path, "w") as f:
        f.write(str(run_num))


def load_run_number(file_path: str = "run_number.txt") -> int:
    """Load persisted run number"""
    try:
        with open(file_path, "r") as f:
            return int(f.read().strip())
    except Exception:
        return 0


def send_telegram_message(bot_token: str, chat_id: str, text: str):
    """Send message via Telegram

    Args:
        bot_token: Telegram bot token from environment variables
        chat_id: Telegram chat ID from environment variables
        text: Message text to send
    """
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown"
    }
    try:
        response = requests.post(url, json=payload)
        if not response.ok:
            log(f"Telegram API error: {response.status_code} {response.text}")
    except Exception as e:
        log(f"Failed to send Telegram message: {e}")