#!/usr/bin/env python3
"""Telegram bot entry point.

Supports two modes:
1. --test mode: Call handlers directly and print output to stdout
2. Telegram mode: Run the bot with aiogram polling

Usage:
    uv run bot.py --test "/start"     # Test mode
    uv run bot.py                     # Telegram mode
"""

import argparse
import asyncio
import logging
import sys
from pathlib import Path

# Add bot directory to path for imports
bot_dir = Path(__file__).parent
sys.path.insert(0, str(bot_dir))

from config import load_config
from handlers import (
    handle_help,
    handle_health,
    handle_labs,
    handle_scores,
    handle_start,
    handle_unknown,
)

# Try to import aiogram for Telegram mode
try:
    from aiogram import Bot, Dispatcher, types
    from aiogram.filters import Command
    AIOMGRAM_AVAILABLE = True
except ImportError:
    AIOMGRAM_AVAILABLE = False


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def parse_command(text: str) -> tuple[str, list[str]]:
    """Parse a command string into command and arguments.
    
    Examples:
        "/start" -> ("start", [])
        "/scores lab-04" -> ("scores", ["lab-04"])
        "hello world" -> ("", ["hello", "world"])
    """
    text = text.strip()
    
    if text.startswith("/"):
        parts = text[1:].split(maxsplit=1)
        command = parts[0].lower()
        args = parts[1].split() if len(parts) > 1 else []
        return command, args
    else:
        # Plain text - will be handled by LLM in Task 3
        return "", text.split()


async def run_test_mode(command: str) -> None:
    """Run a command in test mode and print result to stdout.

    This allows testing handlers without Telegram connection.
    """
    config = load_config()
    cmd, args = parse_command(command)

    # Route to appropriate handler
    if cmd == "start":
        result = await handle_start(args, config)
    elif cmd == "help":
        result = await handle_help(args, config)
    elif cmd == "health":
        result = await handle_health(args, config)
    elif cmd == "labs":
        result = await handle_labs(args, config)
    elif cmd == "scores":
        result = await handle_scores(args, config)
    elif cmd == "":
        # Plain text query
        result = await handle_unknown(command, config)
    else:
        result = f"❌ Unknown command: /{cmd}\n\nUse /help to see available commands."

    print(result)


async def run_telegram_mode() -> None:
    """Run the bot in Telegram mode with aiogram polling."""
    if not AIOMGRAM_AVAILABLE:
        logger.error("aiogram not installed. Install with: uv add aiogram")
        sys.exit(1)

    config = load_config()

    if not config.bot_token:
        logger.error("BOT_TOKEN not found in .env.bot.secret")
        sys.exit(1)

    bot = Bot(token=config.bot_token)
    dp = Dispatcher()

    # Register command handlers
    @dp.message(Command("start"))
    async def start_handler(message: types.Message):
        result = await handle_start(config=config)
        await message.answer(result)

    @dp.message(Command("help"))
    async def help_handler(message: types.Message):
        result = await handle_help(config=config)
        await message.answer(result)

    @dp.message(Command("health"))
    async def health_handler(message: types.Message):
        result = await handle_health(config=config)
        await message.answer(result)

    @dp.message(Command("labs"))
    async def labs_handler(message: types.Message):
        result = await handle_labs(config=config)
        await message.answer(result)

    @dp.message(Command("scores"))
    async def scores_handler(message: types.Message, command: types.Command):
        # Parse arguments from command
        args = command.args.split() if command.args else []
        result = await handle_scores(args, config=config)
        await message.answer(result)

    logger.info("Bot started in Telegram mode")
    await dp.start_polling(bot)


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="LMS Telegram Bot")
    parser.add_argument(
        "--test",
        type=str,
        metavar="COMMAND",
        help="Run in test mode with the given command (e.g., '/start')",
    )
    
    args = parser.parse_args()
    
    if args.test:
        # Test mode - call handlers directly
        asyncio.run(run_test_mode(args.test))
    else:
        # Telegram mode - run the bot
        asyncio.run(run_telegram_mode())


if __name__ == "__main__":
    main()
