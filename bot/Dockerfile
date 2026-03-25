# Bot Dockerfile
# Uses uv for dependency management (no requirements.txt)

FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

# Set working directory
WORKDIR /app

# Copy pyproject.toml and uv.lock for dependency installation
COPY pyproject.toml uv.lock ./

# Install dependencies using uv
RUN uv sync --frozen --no-dev

# Copy bot source code
COPY bot.py ./
COPY config.py ./
COPY handlers/ ./handlers/
COPY services/ ./services/

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Run the bot
CMD ["uv", "run", "python", "bot.py"]
