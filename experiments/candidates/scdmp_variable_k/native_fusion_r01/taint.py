"""Explicit order-token views for the CLOSED R01 consumer registry."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .contract import EventOrder


class Consumer(str, Enum):
    FOUNDATION = "FOUNDATION"
    TREAT = "TREAT"
    FREE = "FREE"
    REVERSED = "REVERSED"
    SET = "SET"


@dataclass(frozen=True)
class TokenView:
    consumer: Consumer
    unordered_tokens: tuple[str, str]
    ordered_tokens: tuple[str, str] | None
    chronology_q: float | None
    set_coordinate: float | None


def token_view(order: EventOrder, consumer: Consumer) -> TokenView:
    """Return only the order information permitted for one registered arm."""

    if not isinstance(order, EventOrder) or not isinstance(consumer, Consumer):
        raise TypeError("order and consumer must use the frozen registries")
    unordered = tuple(sorted(order.tokens))
    if consumer is Consumer.FOUNDATION:
        return TokenView(consumer, unordered, None, None, None)
    if consumer is Consumer.SET:
        return TokenView(consumer, unordered, None, None, 0.5)
    chronology_q = 1.0 - order.q if consumer is Consumer.REVERSED else order.q
    return TokenView(consumer, unordered, order.tokens, chronology_q, None)
