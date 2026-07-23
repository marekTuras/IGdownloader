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

    # rozhodnutie človeka (approval flow): "yes" / "no" / "" (nerozhodnuté)
    approved: str = ""

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

    @classmethod
    def from_row(cls, row: dict) -> "Company":
        """Zrekonštruuje firmu z riadku CSV (vrátane stĺpca approved)."""
        def _status(v: str) -> WebsiteStatus:
            try:
                return WebsiteStatus(v)
            except ValueError:
                return WebsiteStatus.UNKNOWN

        try:
            conf = float(row.get("confidence") or 0.0)
        except ValueError:
            conf = 0.0

        reasons = [r.strip() for r in (row.get("reasons") or "").split(";") if r.strip()]
        return cls(
            name=row.get("name", ""),
            city=row.get("city", ""),
            district=row.get("district", ""),
            region=row.get("region", ""),
            category=row.get("category", ""),
            phone=row.get("phone", ""),
            email=row.get("email", ""),
            facebook=row.get("facebook", ""),
            instagram=row.get("instagram", ""),
            website=(row.get("website") or None),
            source=row.get("source", ""),
            source_url=row.get("source_url", ""),
            status=_status(row.get("status", "unknown")),
            confidence=conf,
            reasons=reasons,
            approved=(row.get("approved") or "").strip(),
        )


# Poradie stĺpcov v CSV výstupe. `approved` je prvý, aby sa ľahko vypĺňal.
CSV_FIELDS = [
    "approved",
    "name", "city", "district", "region", "category",
    "phone", "email", "facebook", "instagram", "website",
    "status", "is_lead", "confidence", "reasons",
    "source", "source_url",
]
