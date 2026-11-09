# AI assistant for a car-service company (Telegram)

An LLM-based Telegram assistant built for a real car-service and car-rental business (2026).
This repository contains a cleaned version: no tokens, no client names, an example price list.

## Problem
Customers ask the same questions about services, prices and hours; requests get lost in chats and managers spend time on routine answers.

## What it does
- Answers naturally, but **only within the company's real service list** — prices come from the catalogue in code, not from the model
- Politely refuses unsupported services and vehicles (e.g. trucks)
- Collects a booking step by step: service, name, phone, car model, preferred time — and creates a **numbered request**
- **Escalates** complaints, unclear or out-of-scope messages to the manager chat with the reason
- Falls back to escalation if the model returns invalid output or the API is unavailable

## Architecture
```
Telegram ─► bot.py (aiogram) ─► LLMClient ─► OpenAI-compatible API (JSON answer)
                │                    ▲
                │                    └── system prompt built from services.json
                ├─► BookingDraft (validation, phone normalisation, vehicle rules)
                ├─► RequestStore (SQLite, numbered requests, retention purge)
                └─► manager chat (new bookings and escalations)
```

## Security and privacy
- Secrets only in environment variables (`.env` is git-ignored)
- Model output is treated as untrusted: strict JSON parsing, intent whitelist, service codes checked against the catalogue
- Only data needed for booking is collected; old requests are purged after a retention period
- Works with any OpenAI-compatible endpoint, including self-hosted models, so data can stay on company servers

## Run
```bash
pip install -r requirements.txt
cp .env.example .env      # fill in the values
python bot.py
pytest -q                 # business-logic tests, no network needed
```

## Stack
Python 3.10+, aiogram 3, httpx, OpenAI-compatible LLM API, SQLite, pytest
