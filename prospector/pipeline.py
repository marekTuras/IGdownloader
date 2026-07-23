"""Pipeline: zozbieraj firmy zo zdrojov -> overuj -> deduplikuj -> CSV.

Celý beh je riadený odvetvím (`Vertical`) — kľúčové slovo určuje stopwords pre
hádanie domén, kategóriu v katalógu aj vyhľadávacie dotazy. Nástroj tak funguje
pre ľubovoľné odvetvie (notár, autoservis, kaderníctvo, …), nielen PC servis.
"""
from __future__ import annotations

import csv
from pathlib import Path
from typing import Iterable

from .discovery import verify
from .models import CSV_FIELDS, Company, WebsiteStatus
from .sources import SOURCES
from .sources.atlasfiriem import AtlasFiriemSource
from .sources.search import SearchSource
from .sources.seed import SeedSource
from .vertical import Vertical, load_vertical


def build_source(name: str, vertical: Vertical, opts: dict):
    """Zostaví inštanciu zdroja nakonfigurovanú pre dané odvetvie."""
    if name == "seed":
        path = opts.get("seed_path")
        return SeedSource(path) if path else SeedSource()
    if name == "atlasfiriem":
        return AtlasFiriemSource()
    if name == "search":
        return SearchSource(
            vertical=vertical,
            locations=opts.get("locations") or [""],
            search_url_template=opts.get("search_url_template"),
            result_selector=opts.get("result_selector", "[class*=result]"),
            title_selector=opts.get("title_selector"),
        )
    cls = SOURCES.get(name)
    if cls is None:
        raise ValueError(f"Neznámy zdroj: {name}. Dostupné: {', '.join(SOURCES)}")
    return cls()


def collect(source_names: list[str], vertical: Vertical, opts: dict
            ) -> list[Company]:
    """Zozbiera firmy z uvedených zdrojov."""
    fetch_kwargs = {
        "okres_slug": opts.get("okres", "michalovce"),
        "okres_id": opts.get("okres_id", 150),
        "strany": opts.get("strany", 1),
        "category_path": vertical.catalog_path
        or "katalog/elektro-a-pocitace/elektroservisy/pocitace-a-prislusenstvo",
    }
    out: list[Company] = []
    for sn in source_names:
        out.extend(build_source(sn, vertical, opts).fetch(**fetch_kwargs))
    return out


def dedupe(companies: Iterable[Company]) -> list[Company]:
    seen: dict[str, Company] = {}
    for c in companies:
        seen.setdefault(c.key(), c)
    return list(seen.values())


def run(source_names: list[str], *, vertical: Vertical | str = "firma",
        online: bool = True, leads_only: bool = False,
        opts: dict | None = None) -> list[Company]:
    """Kompletný beh: zber -> dedupe -> verifikácia -> zoradenie."""
    vertical = vertical if isinstance(vertical, Vertical) else load_vertical(vertical)
    opts = opts or {}

    companies = dedupe(collect(source_names, vertical, opts))
    for c in companies:
        if not c.category:
            c.category = vertical.label
        verify(c, online=online, stopwords=vertical.domain_stopwords)

    if leads_only:
        companies = [c for c in companies if c.status.is_lead]

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
