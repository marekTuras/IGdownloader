"""Dátové modely pre prospecting nástroj.

Cieľom je nájsť firmy (PC servisy a podobné) ktoré nemajú vlastný web,
alebo majú veľmi zastaraný web — teda ideálnych kandidátov na redesign.
"""
from __future__ import annotations

import dataclasses
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class WebsiteStatus(str, Enum):
    """Stav webu firmy z pohľadu obchodnej príležitosti."""

    NONE = "none"          # firma nemá vlastný web (len FB / IG / katalóg)
    OUTDATED = "outdated"  # firma má, ale veľmi zastaraný web
    MODERN = "modern"      # firma má moderný web -> nie je to lead
    UNKNOWN = "unknown"    # nepodarilo sa zistiť (napr. bez prístupu na net)

    @property
    def is_lead(self) -> bool:
        """Kandidát na oslovenie = nemá web alebo má starý web."""
        return self in (WebsiteStatus.NONE, WebsiteStatus.OUTDATED)


@dataclass
class Company:
    """Jedna firma / lead."""

    name: str
    city: str = ""
    district: str = ""          # okres
    region: str = ""            # kraj
    category: str = "pc-servis"
    phone: str = ""
    email: str = ""
    facebook: str = ""
    instagram: str = ""
    website: Optional[str] = None      # vlastná doména, ak existuje
    source: str = ""                   # odkiaľ sme firmu získali
    source_url: str = ""

    # výsledky verifikácie
    status: WebsiteStatus = WebsiteStatus.UNKNOWN
    confidence: float = 0.0            # 0.0 - 1.0
    reasons: list[str] = field(default_factory=list)

    def key(self) -> str:
        """Kľúč pre deduplikáciu (názov + mesto, znormalizované)."""
        norm = lambda s: "".join(ch for ch in s.lower() if ch.isalnum())
        return f"{norm(self.name)}|{norm(self.city)}"

    def to_row(self) -> dict:
        d = dataclasses.asdict(self)
        d["status"] = self.status.value
        d["is_lead"] = self.status.is_lead
        d["reasons"] = "; ".join(self.reasons)
        return d


# Poradie stĺpcov v CSV výstupe.
CSV_FIELDS = [
    "name", "city", "district", "region", "category",
    "phone", "email", "facebook", "instagram", "website",
    "status", "is_lead", "confidence", "reasons",
    "source", "source_url",
]
