"""Rozhranie zdroja firiem."""
from __future__ import annotations

from typing import Iterable

from ..models import Company


class Source:
    """Základná trieda zdroja. Podtriedy implementujú `fetch()`."""

    name: str = "base"

    def fetch(self, **kwargs) -> Iterable[Company]:  # pragma: no cover
        raise NotImplementedError
