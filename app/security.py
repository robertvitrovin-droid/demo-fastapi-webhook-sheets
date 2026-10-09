import hashlib
import hmac
import time


def sign(secret: str, timestamp: str, body: bytes) -> str:
    mac = hmac.new(secret.encode(), timestamp.encode() + b"." + body, hashlib.sha256)
    return "sha256=" + mac.hexdigest()


def verify(secret: str, timestamp: str | None, signature: str | None, body: bytes,
           max_skew: int = 300, now: float | None = None) -> bool:
    """Signature = HMAC-SHA256(secret, f"{timestamp}.{raw_body}"). Rejects replays outside the time window."""
    if not timestamp or not signature:
        return False
    try:
        ts = int(timestamp)
    except ValueError:
        return False
    if abs((now or time.time()) - ts) > max_skew:
        return False
    return hmac.compare_digest(sign(secret, timestamp, body), signature)
