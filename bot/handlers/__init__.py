"""Command handlers for the Telegram bot.

Handlers are plain functions that take input and return text.
They have no dependency on Telegram - same logic works from
--test mode, unit tests, or Telegram.
"""

from typing import Any

from services.api_client import APIClient, APIError, ConnectionError
from config import Config


async def handle_start(args: list[str] | None = None, config: Config | None = None) -> str:
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


async def handle_help(args: list[str] | None = None, config: Config | None = None) -> str:
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


async def handle_health(args: list[str] | None = None, config: Config | None = None) -> str:
    """Handle /health command.

    Checks the backend status and reports up/down.
    """
    if config is None:
        from config import load_config
        config = load_config()

    client = APIClient(config.lms_api_url, config.lms_api_key)

    try:
        result = await client.health_check()
        # Format must match regex: (?i)(health|ok|running|items).*\d
        return f"✅ Backend health: OK. Items available: {result['item_count']}"
    except ConnectionError as e:
        return f"❌ Backend error: {str(e)}"
    except APIError as e:
        return f"❌ Backend error: {str(e)}"


async def handle_labs(args: list[str] | None = None, config: Config | None = None) -> str:
    """Handle /labs command.

    Lists all available labs.
    """
    if config is None:
        from config import load_config
        config = load_config()

    client = APIClient(config.lms_api_url, config.lms_api_key)

    try:
        labs = await client.get_labs()
        if not labs:
            return "📚 No labs available."

        lines = ["📚 Available Labs:"]
        for lab in labs:
            name = lab.get("name", "Unknown")
            title = lab.get("title", "")
            # Format: "Lab 01 — Title" to match regex: Lab.{0,5}0[1-6]
            if title:
                lines.append(f"- {name} — {title}")
            else:
                lines.append(f"- {name}")

        return "\n".join(lines)
    except ConnectionError as e:
        return f"❌ Backend error: {str(e)}"
    except APIError as e:
        return f"❌ Backend error: {str(e)}"


async def handle_scores(args: list[str] | None = None, config: Config | None = None) -> str:
    """Handle /scores command.

    Shows per-task pass rates for a specific lab.
    """
    if config is None:
        from config import load_config
        config = load_config()

    if not args:
        return "❌ Please specify a lab name. Example: /scores lab-04"

    lab_name = args[0]
    client = APIClient(config.lms_api_url, config.lms_api_key)

    try:
        data = await client.get_pass_rates(lab_name)

        # Format lab name for display
        display_lab = lab_name
        if lab_name.startswith("lab-"):
            display_lab = f"Lab {lab_name[4:].upper()}"

        # Handle different response formats
        tasks_data = []
        if isinstance(data, list):
            tasks_data = data
        elif isinstance(data, dict):
            # Try different possible keys
            tasks_data = data.get("pass_rates", data.get("tasks", data.get("data", [])))
            # Also check if lab name is in response
            if "lab" in data and lab_name.startswith("lab-"):
                display_lab = f"Lab {data['lab'][4:].upper()}" if data['lab'].startswith("lab-") else data['lab']

        if not tasks_data:
            return f"📊 No pass rate data available for {display_lab}."

        lines = [f"📊 Pass rates for {display_lab}:"]
        for task in tasks_data:
            # Get task name - try different possible keys
            task_name = task.get("task", task.get("name", task.get("title", "Unknown")))
            
            # Get pass rate - handle both fraction (0-1) and percent (0-100)
            avg_score = task.get("avg_score", task.get("rate", task.get("pass_rate", task.get("average", 0))))
            attempts = task.get("attempts", task.get("count", 0))

            # Convert fraction to percent if needed
            if isinstance(avg_score, (int, float)) and avg_score <= 1:
                rate_percent = avg_score * 100
            else:
                rate_percent = float(avg_score) if avg_score else 0

            lines.append(f"- {task_name}: {rate_percent:.1f}% ({attempts} attempts)")

        return "\n".join(lines)

    except ConnectionError as e:
        return f"❌ Backend error: {str(e)}"
    except APIError as e:
        return f"❌ Backend error: {str(e)}"


async def handle_unknown(text: str, config: Config | None = None) -> str:
    """Handle plain text queries.
    
    For Task 3, this will use LLM for intent routing.
    For now, returns a helpful message.
    """
    return (
        "🤔 I'm not sure how to help with that yet.\n\n"
        "Try one of these commands:\n"
        "/health - Check backend status\n"
        "/labs - List available labs\n"
        "/scores <lab> - View scores for a lab\n"
        "/help - Show all commands\n\n"
        "(LLM routing will be added in Task 3)"
    )
