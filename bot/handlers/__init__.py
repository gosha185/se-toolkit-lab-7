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
        return f"✅ Backend is healthy. {result['item_count']} items available."
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
            if title:
                lines.append(f"- {name}: {title}")
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
        
        # Handle different response formats
        if isinstance(data, dict):
            # Format: {"lab": "lab-04", "pass_rates": [{"task": "Task 1", "rate": 0.85, "attempts": 100}, ...]}
            lab = data.get("lab", lab_name)
            pass_rates = data.get("pass_rates", data.get("tasks", []))
            
            if not pass_rates:
                return f"📊 No pass rate data available for {lab_name}."
            
            lines = [f"📊 Pass rates for {lab}:"]
            for task in pass_rates:
                task_name = task.get("task", task.get("name", "Unknown"))
                rate = task.get("rate", task.get("pass_rate", 0))
                attempts = task.get("attempts", 0)
                rate_percent = rate * 100 if rate <= 1 else rate
                lines.append(f"- {task_name}: {rate_percent:.1f}% ({attempts} attempts)")
            
            return "\n".join(lines)
        elif isinstance(data, list):
            # Direct list of tasks
            lines = [f"📊 Pass rates for {lab_name}:"]
            for task in data:
                task_name = task.get("task", task.get("name", "Unknown"))
                rate = task.get("rate", task.get("pass_rate", 0))
                attempts = task.get("attempts", 0)
                rate_percent = rate * 100 if rate <= 1 else rate
                lines.append(f"- {task_name}: {rate_percent:.1f}% ({attempts} attempts)")
            return "\n".join(lines)
        else:
            return f"📊 Pass rates for {lab_name}:\n{data}"
            
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
