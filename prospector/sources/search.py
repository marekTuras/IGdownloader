"""Keyword-driven zdroj: z kľúčového slova + lokalít nájde firmy.

Pre každú lokalitu vygeneruje dotazy z vertical konfigurácie a stiahne stránku
výsledkov od vyhľadávacieho providera. Provider je konfigurovateľný
(`search_url_template` + `result_selector`), aby sa dal napojiť SERP API alebo
katalóg s full-textovým hľadaním — bez viazanosti na jeden zdroj.

Parsovanie výsledkov je v `parse_results()`, ktoré sa dá testovať offline.
Sieť je gated: keď fetch zlyhá (egress policy/offline), zdroj ticho preskočí.
"""
from __future__ import annotations

from typing import Iterable, Optional
from urllib.parse import quote_plus

from ..classify import is_own_website
from ..models import Company
from ..vertical import Vertical, load_vertical
from .base import Source


def parse_results(html: str, *, result_selector: str = "[class*=result]",
                  link_selector: str = "a[href]",
                  title_selector: str | None = None) -> list[Company]:
    """Zo stránky výsledkov vytiahne kandidátov (názov + odkaz).

    Odkaz na vlastnú doménu -> `website`; odkaz na Facebook/IG -> sociálna sieť.
    """
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, "html.parser")
    out: list[Company] = []
    for block in soup.select(result_selector):
        link = block.select_one(link_selector)
        if not link or not link.get("href"):
            continue
        href = link["href"]
        title_el = block.select_one(title_selector) if title_selector else link
        name = (title_el.get_text(strip=True) if title_el else "").strip()
        if not name:
            continue

        low = href.lower()
        website = href if is_own_website(href) else None
        facebook = href if ("facebook.com" in low or "fb.com" in low) else ""
        instagram = href if "instagram.com" in low else ""

        out.append(Company(
            name=name,
            website=website,
            facebook=facebook,
            instagram=instagram,
            source="search",
            source_url=href,
        ))
    return out


class SearchSource(Source):
    name = "search"

    # Predvolený provider je len šablóna — reálne URL/kľúč doplň podľa providera.
    DEFAULT_TEMPLATE = "https://example-search.invalid/search?q={query}"

    def __init__(self, vertical: Vertical | str = "firma",
                 locations: Optional[list[str]] = None,
                 search_url_template: str | None = None,
                 result_selector: str = "[class*=result]",
                 title_selector: str | None = None):
        self.vertical = (vertical if isinstance(vertical, Vertical)
                         else load_vertical(vertical))
        self.locations = locations or [""]
        self.template = search_url_template or self.DEFAULT_TEMPLATE
        self.result_selector = result_selector
        self.title_selector = title_selector

    def _url(self, query: str) -> str:
        return self.template.format(query=quote_plus(query))

    def fetch(self, **kwargs) -> Iterable[Company]:
        from ..discovery import fetch as http_fetch
        for loc in self.locations:
            for query in self.vertical.queries(loc):
                html = http_fetch(self._url(query))
                if not html:
                    continue  # sieť nedostupná / prázdne -> preskoč
                for c in parse_results(html, result_selector=self.result_selector,
                                       title_selector=self.title_selector):
                    c.city = c.city or loc
                    c.category = self.vertical.label
                    yield c
