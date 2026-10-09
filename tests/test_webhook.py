import json, time
from fastapi.testclient import TestClient
from app.config import Settings
from app.main import create_app, write_with_retry
from app.security import sign, verify
from app.store import EventStore
from app.writers import CsvWriter, MemoryWriter

SECRET = "test-secret"
EV = {"event_id": "evt_000123", "type": "order.created", "created_at": "2026-10-09T18:00:00+03:00",
      "customer_name": "Тест Тестенко", "customer_email": "test@example.com",
      "items": [{"sku": "CAKE-1", "qty": 2, "price": "350.00"}], "comment": "без горіхів"}


def client(writer=None, retries=3):
    w = writer or MemoryWriter()
    app = create_app(Settings(webhook_secret=SECRET, retries=retries), writer=w, store=EventStore(":memory:"),
                     sleep=lambda _: None)
    return TestClient(app), w


def post(c, payload, secret=SECRET, ts=None):
    body = json.dumps(payload).encode(); ts = str(ts or int(time.time()))
    return c.post("/webhooks/orders", content=body, headers={"X-Timestamp": ts, "X-Signature": sign(secret, ts, body),
                                                             "Content-Type": "application/json"})


def test_valid_event_written():
    c, w = client(); r = post(c, EV)
    assert r.status_code == 202 and r.json()["status"] == "accepted"
    assert w.rows[0][0] == "evt_000123" and w.rows[0][7] == "700.00"


def test_bad_signature_rejected():
    c, w = client(); assert post(c, EV, secret="wrong").status_code == 401 and not w.rows


def test_missing_headers_rejected():
    c, _ = client(); assert c.post("/webhooks/orders", json=EV).status_code == 401


def test_replay_old_timestamp_rejected():
    c, _ = client(); assert post(c, EV, ts=int(time.time()) - 3600).status_code == 401


def test_tampered_body_rejected():
    ts = "1700000000"; sig = sign(SECRET, ts, b'{"a":1}')
    assert not verify(SECRET, ts, sig, b'{"a":2}', now=1700000000)


def test_idempotent_duplicate():
    c, w = client(); post(c, EV); r = post(c, EV)
    assert r.json()["status"] == "duplicate" and len(w.rows) == 1


def test_validation_error():
    c, _ = client(); bad = dict(EV, customer_email="not-an-email")
    assert post(c, bad).status_code == 422


def test_retry_then_success():
    c, w = client(MemoryWriter(fail_times=2)); r = post(c, EV)
    assert r.json()["attempts"] == 3 and len(w.rows) == 1


def test_retries_exhausted_returns_503_and_allows_redelivery():
    w = MemoryWriter(fail_times=5); c, _ = client(w, retries=3)
    assert post(c, EV).status_code == 503
    w.fail_times = 0
    assert post(c, EV).json()["status"] == "accepted" and len(w.rows) == 1


def test_backoff_delays():
    delays = []; w = MemoryWriter(fail_times=3)
    write_with_retry(w, ["x"], 4, sleep=delays.append)
    assert delays == [0.5, 1.0, 2.0]


def test_csv_writer(tmp_path):
    p = tmp_path / "s.csv"; w = CsvWriter(str(p)); w.append(["a"]); w.append(["b"])
    assert p.read_text(encoding="utf-8").splitlines()[0].startswith("event_id") and len(p.read_text().splitlines()) == 3
