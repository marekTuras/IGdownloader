"""Pipeline: zozbieraj firmy zo zdrojov -> overuj -> deduplikuj -> CSV."""
from __future__ import annotations

import csv
from pathlib import Path
from typing import Iterable

from .discovery import verify
from .models import CSV_FIELDS, Company, WebsiteStatus
from .sources import SOURCES


def collect(source_names: list[str], *, online: bool = True,
            source_kwargs: dict | None = None) -> list[Company]:
    """Zozbiera firmy z uvedených zdrojov."""
    source_kwargs = source_kwargs or {}
    out: list[Company] = []
    for sn in source_names:
        cls = SOURCES.get(sn)
        if cls is None:
            raise ValueError(f"Neznámy zdroj: {sn}. Dostupné: {', '.join(SOURCES)}")
        out.extend(cls().fetch(**source_kwargs))
    return out


def dedupe(companies: Iterable[Company]) -> list[Company]:
    seen: dict[str, Company] = {}
    for c in companies:
        seen.setdefault(c.key(), c)
    return list(seen.values())


def run(source_names: list[str], *, online: bool = True,
        leads_only: bool = False, source_kwargs: dict | None = None
        ) -> list[Company]:
    """Kompletný beh: zber -> dedupe -> verifikácia -> zoradenie."""
    companies = dedupe(collect(source_names, online=online,
                               source_kwargs=source_kwargs))
    for c in companies:
        verify(c, online=online)

    if leads_only:
        companies = [c for c in companies if c.status.is_lead]

    # zoradenie: leady hore, potom podľa istoty
    order = {WebsiteStatus.NONE: 0, WebsiteStatus.OUTDATED: 1,
             WebsiteStatus.UNKNOWN: 2, WebsiteStatus.MODERN: 3}
    companies.sort(key=lambda c: (order[c.status], -c.confidence))
    return companies


def write_csv(companies: list[Company], path: Path | str) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=CSV_FIELDS, extrasaction="ignore")
        w.writeheader()
        for c in companies:
            w.writerow(c.to_row())
    return path


def summary(companies: list[Company]) -> dict:
    counts: dict[str, int] = {}
    for c in companies:
        counts[c.status.value] = counts.get(c.status.value, 0) + 1
    return {
        "total": len(companies),
        "leads": sum(1 for c in companies if c.status.is_lead),
        "by_status": counts,
    }
