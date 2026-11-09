# ai-telegram-assistant

Telegram bot for a car service where I work as IT contractor. Customers write to the bot, it answers about services and prices and helps to book a visit. If the bot is not sure it sends the question to a manager.

This is a cleaned version for GitHub. Real token, real prices and client data are removed, `services.example.json` is just an example.

## Why I made it
Managers were answering the same questions all day: how much is oil change, do you work on sunday, can I come tomorrow. And some requests were just lost in chats. I wanted the bot to take the routine part, but not to lie to customers.

## How it works
1. Customer writes a message
2. Bot sends the dialog + list of services to LLM and asks for answer in JSON (reply, intent, booking fields)
3. Code checks the answer: service must exist in the catalog, phone must be valid, trucks and gazelle we dont service
4. When all fields are collected (service, name, phone, car, time) bot creates request with number and sends it to manager chat
5. If intent is "escalate" or JSON is broken, message goes to manager

Important thing: prices come from the catalog in code, not from the model. In first version the model sometimes invented discounts, so I moved prices out of the model answer.

## Which AI to use (my opinion)
I tried several models through OpenAI compatible API, so you can change only `LLM_BASE_URL` and `LLM_MODEL`.

- **GPT-4o-mini** - stable JSON, cheap, good Russian. I used it most of the time
- **DeepSeek-V3** - very cheap and almost same quality, sometimes adds text around JSON so parser has to cut it
- **Qwen2.5** (Alibaba) - good for Chinese and English, can run locally
- **YandexGPT / GigaChat** - better if data must stay in Russia, but API is a bit different
- **Llama 3 / Qwen via Ollama** - fully local, no data goes outside, but needs a GPU and answers slower

For a small business I think the best is a cheap cloud model + strict checks in code. Fully local model is better for privacy, I want to test it more.

## Security
- tokens only in `.env`, not in code
- answer of the model is not trusted: JSON is parsed, intent must be from the list, service code is checked
- bot asks only data needed for booking, no passport, no address
- old requests can be deleted after N days

## What I want to improve
- voice messages (Whisper)
- real calendar with free time slots instead of "manager will confirm"
- RAG on FAQ of the company so bot answers more questions without manager

## Run
```
pip install -r requirements.txt
cp .env.example .env
python bot.py
pytest -q
```

Stack: Python, aiogram 3, httpx, LLM API, SQLite
