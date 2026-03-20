# Bot Development Plan

## Overview

This document outlines the implementation plan for the Telegram bot that interacts with the LMS backend. The bot enables users to check system health, browse labs and scores, and ask questions in plain language using an LLM for intent routing.

## Architecture

The bot follows a **layered architecture** with clear separation of concerns:

```
┌─────────────────────────────────────────┐
│           Telegram API                  │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│  bot.py (entry point, Telegram polling) │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│  handlers/ (command logic, no Telegram) │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│  services/ (API client, LLM client)     │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│  LMS Backend / LLM API                  │
└─────────────────────────────────────────┘
```

**Key design pattern: Testable Handlers**

Handlers are plain functions that take input and return text. They have no dependency on Telegram. This means:
- Same handler works from `--test` mode, unit tests, and Telegram
- Easy to test without mocking Telegram
- Clear separation between "what to do" (handlers) and "how to receive/send" (bot.py)

## Task 1: Plan and Scaffold

**Goal:** Create project structure with `--test` mode for offline verification.

**Deliverables:**
- `bot/bot.py` — entry point with `--test` mode support
- `bot/handlers/` — directory for command handlers
- `bot/config.py` — environment variable loading
- `bot/pyproject.toml` — bot dependencies (aiogram, httpx, python-dotenv)
- `bot/PLAN.md` — this document

**Acceptance criteria:**
- `uv run bot.py --test "/start"` prints welcome message and exits 0
- Handlers return placeholder text (no real API calls yet)
- Project structure matches the architecture diagram

## Task 2: Backend Integration

**Goal:** Connect handlers to the LMS backend with real data.

**Deliverables:**
- `bot/services/api_client.py` — HTTP client for LMS API with Bearer auth
- Update handlers to call real endpoints:
  - `/health` → `GET /health` → reports up/down status
  - `/labs` → `GET /items` → lists available labs
  - `/scores <lab>` → `GET /analytics/{lab_id}` → per-task pass rates
- Error handling for backend failures (friendly messages, not crashes)

**Key pattern: API Client with Bearer Auth**

The API client reads `LMS_API_URL` and `LMS_API_KEY` from environment variables. Every request includes:
```
Authorization: Bearer <LMS_API_KEY>
```

**Acceptance criteria:**
- `/health` returns real backend status
- `/labs` lists actual labs from the database
- `/scores lab-04` returns pass rates for that lab
- Backend down → friendly message like "LMS is currently unavailable"

## Task 3: Intent-Based Natural Language Routing

**Goal:** Enable plain language queries using LLM tool use.

**Deliverables:**
- `bot/services/llm_client.py` — LLM client for intent classification
- `bot/handlers/intent_router.py` — routes plain text to handlers via LLM
- Tool definitions for all 9 backend endpoints
- System prompt that teaches the LLM when to use each tool

**Key pattern: LLM Tool Use**

The LLM reads tool descriptions to decide which API to call. Example:
```python
tools = [
    {
        "name": "get_health",
        "description": "Check if the LMS backend is running",
        "parameters": {}
    },
    {
        "name": "get_labs",
        "description": "List all available labs",
        "parameters": {}
    },
    # ... more tools
]
```

When a user asks "what labs are available?", the LLM calls `get_labs`.

**Acceptance criteria:**
- Plain text queries work: "what labs are available" → lists labs
- LLM calls correct tool based on user intent
- Tool descriptions are clear enough for the LLM to choose correctly
- Fallback message when LLM service is unreachable

## Task 4: Containerize and Document

**Goal:** Deploy the bot alongside the existing backend on the VM.

**Deliverables:**
- `bot/Dockerfile` — container image for the bot
- Update `docker-compose.yml` to add bot service
- Update `.env.docker.example` with bot configuration
- README documentation for deployment

**Key concept: Docker Networking**

Containers use service names, not `localhost`:
- Bot → Backend: `http://backend:42002` (not `localhost:42002`)
- Bot → LLM: configured via environment variable

**Acceptance criteria:**
- `docker compose up` starts bot and backend together
- Bot responds to commands in Telegram
- README documents how to deploy

## Testing Strategy

1. **Unit tests** (Task 1-2): Test handlers in isolation
2. **Integration tests** (Task 2): Test API client with real backend
3. **E2E tests** (Task 3): Test full flow from Telegram to backend
4. **Manual testing**: `--test` mode for quick verification

## Git Workflow

For each task:
1. Create issue on GitHub
2. Create branch: `task-X-description`
3. Implement, test, commit
4. Create PR with `Closes #<issue-number>`
5. Partner review
6. Merge

## Environment Variables

| Variable | Purpose | Source |
|----------|---------|--------|
| `BOT_TOKEN` | Telegram bot authentication | @BotFather |
| `LMS_API_URL` | Backend URL | Local: `http://localhost:42002`, Docker: `http://backend:42002` |
| `LMS_API_KEY` | Backend API key | Generated during setup |
| `LLM_API_KEY` | LLM API authentication | Generated during setup |
| `LLM_API_BASE_URL` | LLM endpoint | Local: `http://localhost:42005/v1`, Docker: configured |
| `LLM_API_MODEL` | Model name | `coder-model` |

## Risks and Mitigations

| Risk | Mitigation |
|------|------------|
| LLM picks wrong tool | Improve tool descriptions, not code-based routing |
| Backend unavailable | Graceful error messages, retry logic |
| Bot token exposed | Never commit `.env.bot.secret`, use `.gitignore` |
| Docker networking issues | Use service names, test with `docker compose exec` |
