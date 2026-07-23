"""Odvetvová (vertical) konfigurácia.

Nástroj má byť univerzálny: zadáš kľúčové slovo (napr. "notár", "kaderníctvo",
"autoservis") a on preň hľadá firmy a ich weby. Táto konfigurácia hovorí, čo je
pre dané odvetvie špecifické:

- `label`            — kategória do CSV
- `domain_stopwords` — slová, ktoré sa NEMAJÚ použiť pri hádaní domény z názvu
- `catalog_path`     — cesta v katalógoch atlasfiriem/info-*.sk (ak ju poznáme)
- `search_queries`   — šablóny dotazov pre vyhľadávací zdroj ({kw}, {loc})

Preset sa načíta podľa mena/kľúčového slova z `data/verticals.json`. Ak preset
neexistuje, vyrobí sa **generický** z kľúčového slova — nástroj teda funguje pre
ľubovoľné odvetvie, len s presnejšími výsledkami pre nakonfigurované odvetvia.
"""
from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path

PRESETS_PATH = Path(__file__).resolve().parents[1] / "data" / "verticals.json"

# Generické slovenské slová, ktoré nikdy nechceme v hádanej doméne.
BASE_STOPWORDS = {
    "a", "s", "pre", "na", "v", "vo", "the", "sk", "slovensko", "firma",
    "spol", "sro", "sr", "zo", "office", "as",
}


def _norm(text: str) -> str:
    text = unicodedata.normalize("NFKD", text)
    return text.encode("ascii", "ignore").decode("ascii").lower()


@dataclass
class Vertical:
    keyword: str                                   # napr. "notár"
    label: str = ""                                # kategória do CSV
    domain_stopwords: set[str] = field(default_factory=set)
    catalog_path: str | None = None                # cesta v katalógu (ak známa)
    search_queries: list[str] = field(default_factory=list)

    def __post_init__(self):
        if not self.label:
            self.label = _norm(self.keyword).replace(" ", "-") or "firma"
        # kľúčové slovo aj jeho tvary vždy patria medzi stopwords
        kw_tokens = {t for t in re.split(r"\s+", _norm(self.keyword)) if t}
        self.domain_stopwords = (
            {_norm(w) for w in self.domain_stopwords} | BASE_STOPWORDS | kw_tokens
        )
        if not self.search_queries:
            self.search_queries = [
                "{kw} {loc}",
                "{kw} {loc} kontakt",
                "{kw} {loc} facebook",
            ]

    def queries(self, location: str = "") -> list[str]:
        return [q.format(kw=self.keyword, loc=location).strip()
                for q in self.search_queries]


def _load_presets() -> dict:
    if PRESETS_PATH.exists():
        return json.loads(PRESETS_PATH.read_text(encoding="utf-8"))
    return {}


def load_vertical(keyword_or_name: str) -> Vertical:
    """Načíta preset podľa mena/kľúčového slova, alebo vyrobí generický."""
    presets = _load_presets()
    needle = _norm(keyword_or_name)

    for name, cfg in presets.items():
        candidates = {_norm(name), _norm(cfg.get("keyword", ""))}
        candidates |= {_norm(a) for a in cfg.get("aliases", [])}
        if needle in candidates:
            return Vertical(
                keyword=cfg.get("keyword", keyword_or_name),
                label=cfg.get("label", ""),
                domain_stopwords=set(cfg.get("domain_stopwords", [])),
                catalog_path=cfg.get("catalog_path"),
                search_queries=cfg.get("search_queries", []),
            )

    # generický vertical priamo z kľúčového slova
    return Vertical(keyword=keyword_or_name)
