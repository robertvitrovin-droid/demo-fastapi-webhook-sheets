# Webhook → Google Sheets (FastAPI)

> **Демо-проєкт для портфоліо.** Не робота для клієнта; дані в прикладах тестові.

Сервіс приймає вебхуки (замовлення інтернет-магазину, заявки з форм), перевіряє HMAC-підпис,
обробляє кожну подію **рівно один раз** і дописує рядок у Google Sheets. Для демо й тестів є локальний CSV-writer.

## Як працює
1. `POST /webhooks/orders` з заголовками `X-Timestamp` (unix) та `X-Signature: sha256=HMAC(secret, ts + "." + raw_body)`.
2. Підпис перевіряється за постійний час (`hmac.compare_digest`), запити старші за 5 хв відхиляються (захист від replay) → `401`.
3. Тіло валідується Pydantic-моделлю (email, кількість, ціни) → `422`.
4. Ідемпотентність: `event_id` фіксується в SQLite; повтор тієї ж події → `202 {"status":"duplicate"}` без дублювання рядка.
5. Запис у таблицю з повторами й експоненційною затримкою (0.5 → 1 → 2 с…). Якщо Sheets недоступна — `503`,
   подія позначається `failed`, і повторна доставка від відправника обробиться заново.

Writer підключається через `SHEETS_WRITER`: `csv` (демо) або `gspread` (реальна таблиця через service account).

## Запуск
```bash
cp .env.example .env
docker compose up --build             # або: pip install -r requirements.txt && uvicorn app.main:app
python scripts_send_demo.py           # надіслати 3 підписані події + дублікат + підроблений підпис
```
Документація OpenAPI: http://127.0.0.1:8000/docs (скриншот: `docs/openapi-swagger.png`, схема: `docs/openapi.json`).

### Реальний Google Sheets
1. Google Cloud → service account → JSON-ключ → `service_account.json` (не комітиться).
2. Поділитися таблицею з email сервісного акаунта (Editor).
3. `.env`: `SHEETS_WRITER=gspread`, `GSHEET_ID=<id з URL таблиці>`; у compose розкоментувати монтування ключа.

## Тести
```bash
pip install -r requirements.txt -r requirements-dev.txt && python -m pytest -q
```
11 тестів: валідний запис, невірний/відсутній підпис, replay, зміна тіла, дублікат, валідація,
повтор після збою, вичерпані повтори + повторна доставка, затримки backoff, CSV-writer.

## Результат демо-прогону
`data/demo-run.txt` (відповіді сервера) і `data/sheet.csv` (рядки, що потрапили б у таблицю).
Docker-образ у цьому середовищі не збирався (Docker недоступний); сервіс запускався напряму через uvicorn.
