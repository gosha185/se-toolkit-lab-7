"""Configuration loading from environment variables."""

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


@dataclass
class Config:
    """Bot configuration loaded from environment variables."""

    bot_token: str | None
    lms_api_url: str
    lms_api_key: str
    llm_api_key: str | None
    llm_api_base_url: str | None
    llm_api_model: str | None


def load_config() -> Config:
    """Load configuration from .env.bot.secret file.
    
    The file should be in the bot/ directory or parent directory.
    """
    # Try to load from bot/.env.bot.secret first, then from parent/.env.bot.secret
    bot_dir = Path(__file__).parent
    env_file = bot_dir / ".env.bot.secret"
    
    if not env_file.exists():
        # Try parent directory
        env_file = bot_dir.parent / ".env.bot.secret"
    
    if env_file.exists():
        load_dotenv(env_file)
    else:
        # Try to load from current working directory
        load_dotenv(".env.bot.secret")
    
    return Config(
        bot_token=os.getenv("BOT_TOKEN"),
        lms_api_url=os.getenv("LMS_API_URL", "http://localhost:42002"),
        lms_api_key=os.getenv("LMS_API_KEY", ""),
        llm_api_key=os.getenv("LLM_API_KEY"),
        llm_api_base_url=os.getenv("LLM_API_BASE_URL"),
        llm_api_model=os.getenv("LLM_API_MODEL"),
    )
