"""Approval flow.

Workflow:
  1. `prospector.cli` vygeneruje CSV s prázdnym stĺpcom `approved`.
  2. Človek v CSV vyplní `approved` = "yes" / "no" (nechá prázdne = nerozhodnuté).
  3. `prospector.approve` CSV načíta, rozdelí na schválené / zamietnuté / čakajúce
     a zo schválených vyrobí "generation queue" (JSON) pripravenú na tvorbu webu.

DÔLEŽITÉ: tento modul NIČ negeneruje. Len pripraví zoznam schválených firiem.
Samotná tvorba webu (blok 3) je oddelená a spúšťa sa až na výslovný pokyn.
"""
from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from .models import Company

# Ako sa interpretuje hodnota v stĺpci `approved`.
_YES = {"yes", "y", "ano", "áno", "1", "true", "ok", "approved", "schvalene", "schválené"}
_NO = {"no", "n", "nie", "0", "false", "reject", "rejected", "zamietnute", "zamietnuté"}


class Decision(str, Enum):
    APPROVED = "approved"
    REJECTED = "rejected"
    PENDING = "pending"


def parse_decision(value: str | None) -> Decision:
    v = (value or "").strip().lower()
    if v in _YES:
        return Decision.APPROVED
    if v in _NO:
        return Decision.REJECTED
    return Decision.PENDING


def read_companies(csv_path: str | Path) -> list[Company]:
    """Načíta firmy z CSV (výstup pipeline, prípadne doplnený o approved)."""
    path = Path(csv_path)
    with path.open(encoding="utf-8", newline="") as f:
        return [Company.from_row(row) for row in csv.DictReader(f)]


def decide(companies: list[Company]) -> dict[Decision, list[Company]]:
    buckets: dict[Decision, list[Company]] = {d: [] for d in Decision}
    for c in companies:
        buckets[parse_decision(c.approved)].append(c)
    return buckets


@dataclass
class ApprovalResult:
    approved: list[Company]
    rejected: list[Company]
    pending: list[Company]

    @property
    def summary(self) -> dict:
        return {
            "approved": len(self.approved),
            "rejected": len(self.rejected),
            "pending": len(self.pending),
            "total": len(self.approved) + len(self.rejected) + len(self.pending),
        }


def process(csv_path: str | Path) -> ApprovalResult:
    buckets = decide(read_companies(csv_path))
    return ApprovalResult(
        approved=buckets[Decision.APPROVED],
        rejected=buckets[Decision.REJECTED],
        pending=buckets[Decision.PENDING],
    )


def write_queue(approved: list[Company], path: str | Path) -> Path:
    """Zapíše frontu schválených firiem (JSON) pripravenú na generovanie webu.

    Toto NIE je generovanie — len vstupný zoznam pre blok 3, ktorý sa spustí
    samostatne a len na výslovný pokyn.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    items = []
    for c in approved:
        items.append({
            "name": c.name,
            "city": c.city,
            "region": c.region,
            "category": c.category,
            "phone": c.phone,
            "email": c.email,
            "facebook": c.facebook,
            "instagram": c.instagram,
            "website": c.website,
            "status": c.status.value,   # none / outdated -> nový web vs. redesign
        })
    payload = {"count": len(items), "companies": items}
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path
