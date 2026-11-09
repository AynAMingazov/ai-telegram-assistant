"""LLM layer: one call per customer message, strict JSON answer.

Works with any OpenAI-compatible chat completions API (OpenAI, DeepSeek, Qwen,
local Ollama, ...). The model never decides prices: it only chooses a service
code from the catalogue; prices are taken from the catalogue in code.
"""
from __future__ import annotations

import json
import os
import re

import httpx

from .catalog import Catalog

INTENTS = {"info", "booking", "escalate", "smalltalk"}

SYSTEM_TEMPLATE = """You are the assistant of a car-service company in Telegram.
Answer in the customer's language, briefly and politely, like a friendly manager.
{catalog}

Rules:
- Offer only services from the list. If a service or vehicle is not supported, say so politely.
- Never invent prices, discounts or free time slots; the manager confirms the time.
- If the customer wants to book, collect: service code, name, phone, car model, preferred time.
- If the question is outside the list, a complaint, or you are not sure: intent "escalate".
- Do not ask for documents, addresses or any data that is not needed for booking.

Return ONLY JSON:
{{"reply": "...", "intent": "info|booking|escalate|smalltalk",
  "booking": {{"service": null, "name": null, "phone": null, "car": null, "time": null}},
  "escalation_reason": null}}"""


def parse_answer(text: str) -> dict:
    """Extract and sanitise the JSON object returned by the model."""
    match = re.search(r"\{.*\}", text or "", flags=re.S)
    try:
        data = json.loads(match.group(0)) if match else {}
    except json.JSONDecodeError:
        data = {}
    intent = data.get("intent") if data.get("intent") in INTENTS else "escalate"
    reply = str(data.get("reply") or "").strip()
    if not reply:
        intent = "escalate"
        reply = "Passing your question to a manager, they will answer shortly."
    booking = data.get("booking") if isinstance(data.get("booking"), dict) else {}
    return {
        "reply": reply[:1500],
        "intent": intent,
        "booking": booking,
        "escalation_reason": data.get("escalation_reason") or ("unclear request" if intent == "escalate" else None),
    }


class LLMClient:
    def __init__(self, catalog: Catalog, base_url: str | None = None, api_key: str | None = None,
                 model: str | None = None, timeout: float = 30):
        self.catalog = catalog
        self.base_url = (base_url or os.environ["LLM_BASE_URL"]).rstrip("/")
        self.api_key = api_key or os.environ["LLM_API_KEY"]
        self.model = model or os.environ.get("LLM_MODEL", "gpt-4o-mini")
        self._http = httpx.AsyncClient(timeout=timeout)

    def system_prompt(self) -> str:
        return SYSTEM_TEMPLATE.format(catalog=self.catalog.as_prompt())

    async def answer(self, history: list[dict], booking_state: dict) -> dict:
        messages = [{"role": "system", "content": self.system_prompt()},
                    {"role": "system", "content": f"Current booking draft: {json.dumps(booking_state, ensure_ascii=False)}"},
                    *history[-12:]]
        try:
            resp = await self._http.post(
                f"{self.base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={"model": self.model, "messages": messages, "temperature": 0.3,
                      "response_format": {"type": "json_object"}},
            )
            resp.raise_for_status()
            content = resp.json()["choices"][0]["message"]["content"]
        except (httpx.HTTPError, KeyError, IndexError, ValueError):
            content = ""
        return parse_answer(content)
