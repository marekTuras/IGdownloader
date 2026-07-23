"""Zdroj z ručne overeného JSON datasetu (data/seed_companies.json).

Slúži ako okamžitý vstup do pipeline aj bez prístupu na internet.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from ..models import Company
from .base import Source

DEFAULT_PATH = Path(__file__).resolve().parents[2] / "data" / "seed_companies.json"


class SeedSource(Source):
    name = "seed"

    def __init__(self, path: Path | str = DEFAULT_PATH):
        self.path = Path(path)

    def fetch(self, **kwargs) -> Iterable[Company]:
        records = json.loads(self.path.read_text(encoding="utf-8"))
        for rec in records:
            yield Company(
                name=rec.get("name", ""),
                city=rec.get("city", ""),
                district=rec.get("district", ""),
                region=rec.get("region", ""),
                category=rec.get("category", "pc-servis"),
                phone=rec.get("phone", ""),
                email=rec.get("email", ""),
                facebook=rec.get("facebook", ""),
                instagram=rec.get("instagram", ""),
                website=rec.get("website"),
                source="seed",
                source_url=rec.get("source_url", ""),
            )
