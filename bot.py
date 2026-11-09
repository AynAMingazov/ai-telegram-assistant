"""Telegram entry point (aiogram 3)."""
from __future__ import annotations

import asyncio
import logging
import os
from collections import defaultdict

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import Message

from assistant.booking import BookingDraft
from assistant.catalog import Catalog
from assistant.llm import LLMClient
from assistant.storage import RequestStore

logging.basicConfig(level=logging.INFO)

catalog = Catalog.load(os.environ.get("CATALOG_PATH", "services.example.json"))
llm = LLMClient(catalog)
store = RequestStore(os.environ.get("DB_PATH", "requests.db"))
MANAGER_CHAT_ID = int(os.environ["MANAGER_CHAT_ID"])

history: dict[int, list[dict]] = defaultdict(list)
drafts: dict[int, BookingDraft] = defaultdict(BookingDraft)

dp = Dispatcher()

FIELD_NAMES = {"service": "service", "name": "name", "phone": "phone number",
               "car": "car model", "time": "preferred time"}


@dp.message(CommandStart())
async def start(message: Message) -> None:
    history.pop(message.from_user.id, None)
    drafts.pop(message.from_user.id, None)
    await message.answer("Hello! I can tell you about our services and prices and book you in. How can I help?")


@dp.message(F.text)
async def on_text(message: Message, bot: Bot) -> None:
    uid = message.from_user.id
    history[uid].append({"role": "user", "content": message.text[:1000]})
    draft = drafts[uid]

    result = await llm.answer(history[uid], draft.to_dict())
    reply = result["reply"]

    if result["intent"] == "booking":
        problems = draft.update(result["booking"])
        if draft.car and not catalog.is_vehicle_supported(draft.car):
            reply = "Unfortunately we do not service this type of vehicle."
            draft.car = None
        elif draft.service and not catalog.by_code(draft.service):
            draft.service = None
        if "phone" in problems:
            reply += "\nPlease check the phone number, e.g. +7 900 123-45-67."
        if draft.is_complete():
            service = catalog.by_code(draft.service)
            req_id = store.add(uid, "booking", draft.to_dict())
            reply = (f"Request #{req_id} created: {service.name} (from {service.price_from} RUB), "
                     f"{draft.car}, {draft.time}. A manager will call {draft.phone} to confirm the time.")
            await bot.send_message(MANAGER_CHAT_ID, f"New booking #{req_id}\n{draft.to_dict()}\n@{message.from_user.username}")
            drafts.pop(uid, None)
        elif draft.missing():
            reply += "\n(Still needed: " + ", ".join(FIELD_NAMES[f] for f in draft.missing()) + ")"

    elif result["intent"] == "escalate":
        req_id = store.add(uid, "escalation", {"text": message.text, "reason": result["escalation_reason"]})
        await bot.send_message(
            MANAGER_CHAT_ID,
            f"Escalation #{req_id} from @{message.from_user.username} (id {uid})\n"
            f"Reason: {result['escalation_reason']}\nMessage: {message.text}",
        )

    history[uid].append({"role": "assistant", "content": reply})
    await message.answer(reply)


async def main() -> None:
    bot = Bot(os.environ["TELEGRAM_BOT_TOKEN"])
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
