from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, EmailStr, Field


class Item(BaseModel):
    sku: str = Field(min_length=1, max_length=64)
    qty: int = Field(gt=0, le=1000)
    price: Decimal = Field(ge=0, decimal_places=2)


class OrderEvent(BaseModel):
    event_id: str = Field(min_length=6, max_length=100, description="Unique id; repeats are ignored (idempotency)")
    type: Literal["order.created", "order.paid", "form.submitted"]
    created_at: datetime
    customer_name: str = Field(min_length=1, max_length=120)
    customer_email: EmailStr
    phone: str | None = Field(default=None, max_length=32)
    items: list[Item] = Field(default_factory=list)
    comment: str | None = Field(default=None, max_length=2000)

    def total(self) -> Decimal:
        return sum((i.price * i.qty for i in self.items), Decimal("0"))

    def to_row(self) -> list[str]:
        return [self.event_id, self.type, self.created_at.isoformat(), self.customer_name, self.customer_email,
                self.phone or "", "; ".join(f"{i.sku}×{i.qty}" for i in self.items), f"{self.total():.2f}",
                (self.comment or "").replace("\n", " ")]


HEADER = ["event_id", "type", "created_at", "customer_name", "customer_email", "phone", "items", "total", "comment"]
