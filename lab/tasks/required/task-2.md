# Backend Integration

A bot that only returns placeholder text isn't useful. In this task, you connect it to the real LMS backend — the same one you deployed in previous labs. After this, the bot fetches live data and formats it for the user.

## Requirements targeted

- **P0.3** `/start` — welcome message
- **P0.4** `/help` — lists all available commands
- **P0.5** `/health` — calls backend, reports up/down status
- **P0.6** `/labs` — lists available labs
- **P0.7** `/scores <lab>` — per-task pass rates
- **P0.8** Error handling — friendly message when backend is down

## What you will build

5 slash commands hitting the real backend, all verifiable via `--test`:

```terminal
$ uv run bot.py --test "/health"
Backend is healthy. 42 items available.

$ uv run bot.py --test "/labs"
Available labs:
- Lab 01 — Products, Architecture & Roles
- Lab 02 — Run, Fix, and Deploy
- Lab 03 — Backend API
- Lab 04 — Testing, Front-end, and AI Agents
- Lab 05 — Data Pipeline and Analytics
- Lab 06 — Build Your Own Agent

$ uv run bot.py --test "/scores lab-04"
Pass rates for Lab 04:
- Repository Setup: 92.1% (187 attempts)
- Back-end Testing: 71.4% (156 attempts)
- Add Front-end: 68.3% (142 attempts)
```

When the backend is down, the bot must show a user-friendly message that **includes the actual error** — not a raw traceback, but not a generic "something went wrong" either. The user needs enough information to debug.

Good — includes the error:

```terminal
$ uv run bot.py --test "/health"
Backend error: connection refused (localhost:42002). Check that the services are running.
```

```terminal
$ uv run bot.py --test "/health"
Backend error: HTTP 502 Bad Gateway. The backend service may be down.
```

Bad — hides the error (useless for debugging):

```terminal
Backend is not responding.
```

Bad — raw traceback (not user-friendly):

```terminal
Traceback (most recent call last):
  ...
httpx.ConnectError: [Errno 111] Connection refused
```

## Before you start

Verify your backend is running and has data:

```terminal
curl -s http://localhost:42002/items/ -H "Authorization: Bearer YOUR_LMS_API_KEY" | head -c 200
```

If this returns `[]` or an error, your bot's data commands will return empty results — that's a data problem, not a code problem. Fix it:
- Backend not running → `cd ~/se-toolkit-lab-7 && docker compose --env-file .env.docker.secret up -d`
- Empty data → re-run ETL sync: `curl -X POST http://localhost:42002/pipeline/sync -H "Authorization: Bearer YOUR_LMS_API_KEY" -H "Content-Type: application/json" -d '{}'`

## Backend endpoints

All on `localhost:42002`, require `Authorization: Bearer YOUR_LMS_API_KEY`:

| Endpoint                                         | Returns                        |
| ------------------------------------------------ | ------------------------------ |
| `GET /items/`                                    | Labs and tasks                 |
| `GET /learners/`                                 | Enrolled students              |
| `GET /analytics/scores?lab=lab-01`               | Score distribution (4 buckets) |
| `GET /analytics/pass-rates?lab=lab-01`           | Per-task averages              |
| `GET /analytics/timeline?lab=lab-01`             | Submissions per day            |
| `GET /analytics/groups?lab=lab-01`               | Per-group performance          |
| `GET /analytics/top-learners?lab=lab-01&limit=5` | Top N learners                 |
| `GET /analytics/completion-rate?lab=lab-01`      | Completion percentage          |
| `POST /pipeline/sync`                            | Trigger ETL sync               |

> [!TIP]
> Explore these in Swagger UI at `http://localhost:42002/docs` to see response formats before implementing.

## Required commands

| Command         | Endpoint                         | What it does                         |
| --------------- | -------------------------------- | ------------------------------------ |
| `/start`        | —                                | Welcome message with bot name        |
| `/help`         | —                                | Lists all commands with descriptions |
| `/health`       | `GET /items/`                    | Reports healthy/unhealthy status     |
| `/labs`         | `GET /items/`                    | Lists labs (filter by type)          |
| `/scores <lab>` | `GET /analytics/pass-rates?lab=` | Per-task scores for a lab            |

## Verify

### Test mode — happy path

Run all commands on your VM:

```terminal
cd ~/se-toolkit-lab-7/bot
uv run bot.py --test "/start"
uv run bot.py --test "/help"
uv run bot.py --test "/health"
uv run bot.py --test "/labs"
uv run bot.py --test "/scores lab-04"
```

**What to check:**
- `/start` — contains a welcome message or bot name
- `/help` — lists at least 4 commands with descriptions
- `/health` — says "healthy" or shows item count (proves backend connection works)
- `/labs` — lists real lab names from your backend
- `/scores lab-04` — shows task names with percentages

### Test mode — edge cases

```terminal
uv run bot.py --test "/scores"              # missing argument — should not crash
uv run bot.py --test "/scores lab-99"       # non-existent lab — should handle gracefully
uv run bot.py --test "/unknown"             # unknown command — should suggest /help
```

### Test mode — error handling

Stop the backend and verify the bot handles it gracefully:

```terminal
cd ~/se-toolkit-lab-7
docker compose --env-file .env.docker.secret stop backend
cd bot && uv run bot.py --test "/health"
cd ~/se-toolkit-lab-7
docker compose --env-file .env.docker.secret start backend
```

The response must include the actual error (e.g., "connection refused") — not a raw traceback, and not a vague "something went wrong."

### Deploy and verify in Telegram

Pull, restart, verify:

```terminal
cd ~/se-toolkit-lab-7 && git pull
cd bot && pkill -f "bot.py" 2>/dev/null; nohup uv run bot.py > bot.log 2>&1 &
```

In Telegram, try:
1. `/health` — should show backend status
2. `/labs` — should list labs
3. `/scores lab-04` — should show per-task scores

If a command works in `--test` but not in Telegram, check `bot.log` — it's usually a handler that crashes only when called from the Telegram transport layer.

## Acceptance criteria

- [ ] `--test "/start"` returns text containing "welcome" or bot name.
- [ ] `--test "/help"` lists at least 4 `/command` entries.
- [ ] `--test "/health"` returns a status indicator.
- [ ] `--test "/labs"` lists at least 2 labs.
- [ ] `--test "/scores lab-04"` shows task names and scores.
- [ ] With backend stopped, `--test "/health"` returns a message with the actual error (e.g., "connection refused", "HTTP 502"), no raw `Traceback`.
- [ ] Bot responds to `/health` and `/labs` in Telegram with real data.
- [ ] Git workflow followed.
