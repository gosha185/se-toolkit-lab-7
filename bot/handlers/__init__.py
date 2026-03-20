"""Command handlers for the Telegram bot.

Handlers are plain functions that take input and return text.
They have no dependency on Telegram - same logic works from
--test mode, unit tests, or Telegram.
"""

from typing import Any


async def handle_start(args: list[str] | None = None) -> str:
    """Handle /start command.
    
    Returns a welcome message for new users.
    """
    return (
        "👋 Welcome to the LMS Bot!\n\n"
        "I can help you check system health, browse labs, and view scores.\n\n"
        "Available commands:\n"
        "/help - Show this help message\n"
        "/health - Check backend status\n"
        "/labs - List available labs\n"
        "/scores <lab> - View scores for a lab"
    )


async def handle_help(args: list[str] | None = None) -> str:
    """Handle /help command.
    
    Returns a list of available commands with descriptions.
    """
    return (
        "📖 Available Commands:\n\n"
        "/start - Welcome message\n"
        "/help - Show this help\n"
        "/health - Check if LMS backend is running\n"
        "/labs - List all available labs\n"
        "/scores <lab-name> - View pass rates for a specific lab\n\n"
        "You can also ask questions in plain language!"
    )


async def handle_health(args: list[str] | None = None) -> str:
    """Handle /health command.
    
    Checks the backend status and reports up/down.
    For Task 1, returns a placeholder. Task 2 will call real API.
    """
    # Placeholder for Task 1 - will be implemented in Task 2
    return "🔍 Checking LMS backend status...\n\nStatus: OK (placeholder)"


async def handle_labs(args: list[str] | None = None) -> str:
    """Handle /labs command.
    
    Lists all available labs.
    For Task 1, returns a placeholder. Task 2 will call real API.
    """
    # Placeholder for Task 1 - will be implemented in Task 2
    return (
        "📚 Available Labs:\n\n"
        "lab-01: Introduction\n"
        "lab-02: Basic Concepts\n"
        "lab-03: Advanced Topics\n"
        "lab-04: Integration\n\n"
        "(placeholder data - real data in Task 2)"
    )


async def handle_scores(args: list[str] | None = None) -> str:
    """Handle /scores command.
    
    Shows per-task pass rates for a specific lab.
    For Task 1, returns a placeholder. Task 2 will call real API.
    """
    if not args:
        return "❌ Please specify a lab name. Example: /scores lab-04"
    
    lab_name = args[0] if args else "unknown"
    
    # Placeholder for Task 1 - will be implemented in Task 2
    return (
        f"📊 Scores for {lab_name}:\n\n"
        f"Task 1: 85% pass rate\n"
        f"Task 2: 72% pass rate\n"
        f"Task 3: 90% pass rate\n\n"
        "(placeholder data - real data in Task 2)"
    )


async def handle_unknown(text: str) -> str:
    """Handle plain text queries.
    
    For Task 3, this will use LLM for intent routing.
    For now, returns a placeholder.
    """
    return (
        "🤔 I'm not sure how to help with that yet.\n\n"
        "Try one of these commands:\n"
        "/health, /labs, /scores <lab>\n\n"
        "(LLM routing will be added in Task 3)"
    )
