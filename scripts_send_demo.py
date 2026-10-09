"""Send signed demo webhooks to a running server (incl. a duplicate and a bad signature).
    python scripts_send_demo.py http://127.0.0.1:8000"""
import json, sys, time, urllib.request
from app.security import sign
URL = (sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000") + "/webhooks/orders"
SECRET = "dev-secret-change-me"
events = [
 {"event_id": "evt_demo_0001", "type": "order.created", "created_at": "2026-10-09T18:05:00+03:00", "customer_name": "Демо Покупець 1",
  "customer_email": "buyer1@example.com", "phone": "+380000000001", "items": [{"sku": "CAKE-NAPOLEON", "qty": 1, "price": "520.00"}]},
 {"event_id": "evt_demo_0002", "type": "form.submitted", "created_at": "2026-10-09T18:07:00+03:00", "customer_name": "Демо Клієнт 2",
  "customer_email": "lead2@example.com", "comment": "Прошу передзвонити щодо замовлення на свято"},
 {"event_id": "evt_demo_0003", "type": "order.paid", "created_at": "2026-10-09T18:10:00+03:00", "customer_name": "Демо Покупець 3",
  "customer_email": "buyer3@example.com", "items": [{"sku": "CROISSANT", "qty": 6, "price": "45.00"}, {"sku": "COFFEE-BEANS", "qty": 1, "price": "390.00"}]},
]
def send(ev, secret=SECRET):
    body = json.dumps(ev, ensure_ascii=False).encode(); ts = str(int(time.time()))
    req = urllib.request.Request(URL, body, {"Content-Type": "application/json", "X-Timestamp": ts, "X-Signature": sign(secret, ts, body)})
    try:
        with urllib.request.urlopen(req) as r: return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e: return e.code, json.loads(e.read())
for ev in events: print(ev["event_id"], *send(ev))
print("duplicate     ", *send(events[0]))
print("bad signature ", *send(events[1], secret="attacker"))
