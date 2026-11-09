# ai-telegram-assistant

Telegram assistant for a car service. Production use since 2026.
Public version: no tokens, no client data, example price list.

## Task
Remove routine questions from managers. Do not lose booking requests.

## Logic
1. Message and service list go to the LLM. Response format: JSON.
2. Response is validated in code. Unknown service, invalid phone, unsupported vehicle are rejected.
3. Complete booking gets a number and goes to the manager chat.
4. Unclear request or invalid model output goes to the manager.

Prices are taken from the catalog, not from the model. The model invented discounts in early tests.

## Models
API is OpenAI-compatible. Model is set in `.env`.

| Model | Notes |
|---|---|
| GPT-4o-mini | Main. Stable JSON, low cost. |
| DeepSeek-V3 | Cheaper. Sometimes adds text around JSON. |
| Qwen2.5 | Can run locally. |
| YandexGPT, GigaChat | Data stays in Russia. Different API. |
| Llama 3 via Ollama | Fully local. Needs GPU, slower. |

Choice for small business: cheap cloud model and strict validation in code.

## Security
- Secrets in `.env` only.
- Model output is untrusted input.
- Only booking data is collected.
- Old requests are deleted after a set period.

## Next
Voice input (Whisper). Calendar with free slots. RAG over company FAQ.

## Run
```
pip install -r requirements.txt
cp .env.example .env
python bot.py
pytest -q
```

Python, aiogram 3, httpx, SQLite.
