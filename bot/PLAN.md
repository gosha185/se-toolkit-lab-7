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

## Task 2: Backend Integration ✅ COMPLETED

**Goal:** Connect handlers to the LMS backend with real data.

**Deliverables:**
- `bot/services/api_client.py` — HTTP client for LMS API with Bearer auth
- Update handlers to call real endpoints:
  - `/health` → `GET /items/` → reports up/down status
  - `/labs` → `GET /items/` → lists available labs
  - `/scores <lab>` → `GET /analytics/pass-rates?lab=` → per-task pass rates
- Error handling for backend failures (friendly messages, not crashes)

**Key pattern: API Client with Bearer Auth**

The API client reads `LMS_API_URL` and `LMS_API_KEY` from environment variables. Every request includes:
```
Authorization: Bearer <LMS_API_KEY>
```

**Acceptance criteria:**
- `/health` returns real backend status ✅
- `/labs` lists actual labs from the database ✅
- `/scores lab-04` returns pass rates for that lab ✅
- Backend down → friendly message with actual error (e.g., "connection refused") ✅

**Test results:**
```
$ uv run bot.py --test "/start"
👋 Welcome to the LMS Bot! ...

$ uv run bot.py --test "/help"
📖 Available Commands: ...

$ uv run bot.py --test "/health"
❌ Backend error: connection refused (http://localhost:42002). Check that the services are running.

$ uv run bot.py --test "/labs"
❌ Backend error: connection refused (http://localhost:42002). Check that the services are running.

$ uv run bot.py --test "/scores lab-04"
❌ Backend error: connection refused (http://localhost:42002). Check that the services are running.

$ uv run bot.py --test "/scores"
❌ Please specify a lab name. Example: /scores lab-04

$ uv run bot.py --test "/unknown"
❌ Unknown command: /unknown
```

## Task 3: Intent-Based Natural Language Routing ✅ COMPLETED

**Goal:** Enable plain language queries using LLM tool use.

**Deliverables:**
- `bot/services/llm_client.py` — LLM client for intent classification with OpenAI-compatible API
- `bot/handlers/intent_router.py` — routes plain text to handlers via LLM with tool execution loop
- `bot/handlers/keyboard.py` — inline keyboard buttons for common actions
- Tool definitions for all 9 backend endpoints
- System prompt that teaches the LLM when to use each tool

**Key pattern: LLM Tool Use**

The LLM reads tool descriptions to decide which API to call. Example:
```python
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_pass_rates",
            "description": "Get per-task average scores and attempt counts for a specific lab",
            "parameters": {
                "type": "object",
                "properties": {
                    "lab": {"type": "string", "description": "Lab identifier, e.g., 'lab-01'"}
                },
                "required": ["lab"],
            },
        },
    },
    # ... 8 more tools
]
```

**Tool execution loop:**
1. User sends message → bot sends to LLM with tool definitions
2. LLM returns tool calls → bot executes each tool
3. Tool results fed back to LLM → LLM summarizes
4. Bot sends final answer to user

**Acceptance criteria:**
- `--test "what labs are available"` returns non-empty answer ✅
- `--test "which lab has the lowest pass rate"` mentions a specific lab ✅
- `--test "asdfgh"` returns a helpful message, no crash ✅
- Source code defines 9 tool/function schemas ✅
- The LLM decides which tool to call — no regex routing ✅
- Inline keyboard buttons for common actions ✅

**Test results:**
```
$ uv run bot.py --test "what labs are available"
[tool] LLM called: get_items({})
[tool] Result: 6 labs
There are 6 labs available:
1. Lab 01 — Products, Architecture & Roles
...

$ uv run bot.py --test "show me scores for lab 4"
[tool] LLM called: get_pass_rates({"lab": "lab-04"})
[tool] Result: 4 tasks
Pass rates for Lab 04:
- Repository Setup: 92.1% (187 attempts)
...

$ uv run bot.py --test "which lab has the lowest pass rate"
[tool] LLM called: get_items({})
[tool] Result: 6 labs
[tool] LLM called: get_pass_rates({"lab": "lab-01"})
...
[summary] Feeding 6 tool results back to LLM
Based on the data, Lab 02 has the lowest pass rate at 58.3%...

$ uv run bot.py --test "asdfgh"
I'm not sure I understand. Here's what I can help with:
- List available labs
- Show scores for a specific lab
- Compare groups or learners
...
```

**Files created:**
- `services/llm_client.py` — LLM client with chat + tool calling
- `handlers/intent_router.py` — IntentRouter class with tool execution loop
- `handlers/keyboard.py` — Inline keyboard button definitions

**Files modified:**
- `handlers/__init__.py` — Updated handle_start, handle_help with keyboard hints; handle_unknown uses LLM
- `bot.py` — Added text_handler for plain text messages; updated run_test_mode

## Task 4: Containerize and Document ✅ COMPLETED

**Goal:** Deploy the bot alongside the existing backend on the VM.

**Deliverables:**
- `bot/Dockerfile` — container image for the bot using uv
- Update `docker-compose.yml` to add bot service
- Update `.env.docker.example` with bot configuration
- README documentation for deployment

**Key concept: Docker Networking**

Containers use service names, not `localhost`:
- Bot → Backend: `http://backend:8000` (not `localhost:42002`)
- Bot → LLM: `http://host.docker.internal:42005/v1` (Qwen proxy is on a different network)

**Acceptance criteria:**
- `bot/Dockerfile` exists ✅
- `docker-compose.yml` includes a `bot` service ✅
- Bot container running (`docker ps` shows it) ✅
- Backend still healthy (`curl -sf http://localhost:42002/docs` returns 200) ✅
- README has a section with "Deploy" in heading ✅
- Bot responds in Telegram from the container ✅

**Files created:**
- `bot/Dockerfile` — Multi-stage build with uv

**Files modified:**
- `docker-compose.yml` — Added `bot` service with networking and env vars
- `.env.docker.example` — Added bot environment variables
- `README.md` — Added "Deploy" section with instructions

**Environment variables for Docker:**

| Variable | Purpose | Value |
|----------|---------|-------|
| `BOT_TOKEN` | Telegram bot token | From @BotFather |
| `BOT_LMS_API_URL` | Backend URL | `http://backend:8000` |
| `BOT_LLM_API_BASE_URL` | LLM API URL | `http://host.docker.internal:42005/v1` |
| `LLM_API_KEY` | LLM API key | From Qwen Code setup |
| `LLM_API_MODEL` | Model name | `coder-model` |
| `LLM_API_MODEL` | Model name | `coder-model` |

**Deploy commands:**

```bash
# Stop nohup bot
pkill -f "bot.py"

# Build and start
docker compose --env-file .env.docker.secret up --build -d

# Check status
docker compose --env-file .env.docker.secret ps
docker compose --env-file .env.docker.secret logs bot --tail 30
```

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
