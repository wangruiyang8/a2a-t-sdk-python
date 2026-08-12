from __future__ import annotations

from copy import deepcopy
from typing import Any

_cards: dict[tuple[str, str], dict[str, Any]] = {}


def store_card(card: dict[str, Any]) -> None:
    organization = str(card.get("provider", {}).get("organization", ""))
    name = str(card.get("name", ""))
    _cards[(organization, name)] = deepcopy(card)


def get_card(organization: str, name: str) -> dict[str, Any] | None:
    card = _cards.get((organization, name))
    return deepcopy(card) if card is not None else None


def clear_cards() -> None:
    _cards.clear()
