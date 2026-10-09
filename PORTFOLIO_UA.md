# Інтеграція: вебхуки → Google Sheets на FastAPI (демо)

**Демо-проєкт для портфоліо**, не робота для клієнта. Дані в прикладах тестові.

**Задача.** Автоматично записувати замовлення й заявки з сайту в Google-таблицю без дублікатів і втрат.

**Що зроблено.**
- Endpoint для вебхуків з документацією OpenAPI (Swagger).
- Перевірка підпису HMAC-SHA256 і часу запиту; кожна подія записується рівно один раз.
- Повтори запису при збоях; справжній Google Sheets (gspread) або CSV для демо; Docker / docker-compose.

**Результат.** 11 [тестів](https://github.com/robertvitrovin-droid/demo-fastapi-webhook-sheets/blob/main/tests/test_webhook.py) на підпис, replay, дублікати, валідацію й повтори. Демо-прогін: 3 події записано, дублікат проігноровано, підроблений підпис відхилено з 401 ([demo-run.txt](https://github.com/robertvitrovin-droid/demo-fastapi-webhook-sheets/blob/main/data/demo-run.txt), [sheet.csv](https://github.com/robertvitrovin-droid/demo-fastapi-webhook-sheets/blob/main/data/sheet.csv)). Запуск у Docker у демо не перевірявся.

**Посилання.** [Код на GitHub](https://github.com/robertvitrovin-droid/demo-fastapi-webhook-sheets)

Стек: Python, FastAPI, Pydantic, gspread, SQLite, Docker, pytest · **Ціна від 3 000 грн**, від 2 днів
