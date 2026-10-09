import json
import logging
import time

from fastapi import FastAPI, Header, HTTPException, Request, status
from pydantic import ValidationError

from .config import Settings
from .models import OrderEvent
from .security import verify
from .store import EventStore
from .writers import make_writer

log = logging.getLogger("webhook")


def write_with_retry(writer, row, retries: int, base_delay: float = 0.5, sleep=time.sleep) -> int:
    """Exponential backoff: 0.5s, 1s, 2s… Returns number of attempts used; re-raises after the last one."""
    for attempt in range(1, retries + 1):
        try:
            writer.append(row)
            return attempt
        except Exception as e:  # network / quota errors from Sheets
            log.warning("write failed (attempt %d/%d): %s", attempt, retries, e)
            if attempt == retries:
                raise
            sleep(base_delay * 2 ** (attempt - 1))


def create_app(settings: Settings | None = None, writer=None, store=None, sleep=time.sleep) -> FastAPI:
    s = settings or Settings()
    app = FastAPI(title="Webhook → Google Sheets (DEMO)", version="1.0.0", swagger_ui_parameters={"docExpansion": "full", "defaultModelsExpandDepth": 0, "deepLinking": True},
                  description="Приймає вебхуки замовлень/форм, перевіряє HMAC-підпис, обробляє кожну подію "
                              "рівно один раз і дописує рядок у Google Sheets (або CSV у демо-режимі).")
    app.state.writer = writer or make_writer(s)
    app.state.store = store or EventStore(s.db_path)

    @app.get("/health", tags=["service"])
    def health():
        return {"status": "ok", "writer": type(app.state.writer).__name__, "events": app.state.store.stats()}

    @app.post("/webhooks/orders", status_code=status.HTTP_202_ACCEPTED, tags=["webhooks"],
              summary="Прийняти подію замовлення або форми",
              responses={401: {"description": "Невірний підпис або застарілий timestamp"},
                         422: {"description": "Невалідне тіло"}, 503: {"description": "Таблиця недоступна, повторіть пізніше"}})
    async def receive(request: Request,
                      x_signature: str | None = Header(None, description="sha256=<hex HMAC(secret, ts + '.' + body)>"),
                      x_timestamp: str | None = Header(None, description="Unix time, seconds")):
        body = await request.body()
        if not verify(s.webhook_secret, x_timestamp, x_signature, body, s.max_skew_s):
            raise HTTPException(401, "invalid signature")
        try:
            ev = OrderEvent.model_validate(json.loads(body))
        except (ValueError, ValidationError) as e:
            raise HTTPException(422, str(e)[:500])
        state = app.state.store.claim(ev.event_id)
        if state != "new":
            return {"status": "duplicate", "event_id": ev.event_id, "previous": state}
        try:
            attempts = write_with_retry(app.state.writer, ev.to_row(), s.retries, sleep=sleep)
        except Exception as e:
            app.state.store.finish(ev.event_id, "failed", s.retries, str(e)[:300])
            raise HTTPException(503, "sheet temporarily unavailable, please retry")  # sender will redeliver
        app.state.store.finish(ev.event_id, "done", attempts)
        return {"status": "accepted", "event_id": ev.event_id, "attempts": attempts}

    return app


app = create_app() if __name__ != "__main__" else None
