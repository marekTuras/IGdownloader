"""Scraper katalógov rodiny atlasfiriem.info / info-*.sk.

Tieto katalógy zdieľajú štruktúru a listujú firmy po okresoch pre kategóriu,
napr. „elektro-a-pocitace/elektroservisy/pocitace-a-prislusenstvo".
Každý záznam má názov, adresu, telefón a *voliteľne* odkaz na web —
firmy BEZ www odkazu sú presne naši kandidáti.

POZNÁMKA: presné CSS selektory sa môžu líšiť podľa aktuálneho HTML katalógu
a v izolovanom prostredí (egress policy) je tento zdroj nedostupný. Preto je
parsovanie oddelené do `parse_listing(html)`, ktoré sa dá testovať offline
nad fixtúrou a doladiť podľa reálneho HTML.
"""
from __future__ import annotations

from typing import Iterable, Optional
from urllib.parse import urljoin

from ..classify import is_own_website
from ..models import Company
from .base import Source

BASE = "https://www.atlasfiriem.info"
# Predvolená kategória: elektroservisy -> počítače a príslušenstvo.
CATEGORY_PATH = "katalog/elektro-a-pocitace/elektroservisy/pocitace-a-prislusenstvo"


def listing_url(okres_slug: str, okres_id: int, strana: int = 1,
                base: str = BASE) -> str:
    """Zostaví URL výpisu firiem pre okres.

    Príklad: okres-150-michalovce-strana-1.html
    """
    return f"{base}/{CATEGORY_PATH}/okres-{okres_id}-{okres_slug}-strana-{strana}.html"


def parse_listing(html: str, base: str = BASE) -> list[Company]:
    """Vyparsuje firmy zo stránky katalógu.

    Hľadá bloky firiem (kontajner s triedou obsahujúcou 'firma'/'company'/'item')
    a z nich názov, adresu, telefón a prípadný odkaz na vlastný web.
    """
    from bs4 import BeautifulSoup  # lokálny import, nech je modul importovateľný aj bez bs4

    soup = BeautifulSoup(html, "html.parser")
    companies: list[Company] = []

    blocks = soup.select(
        "[class*=firma], [class*=company], [class*=subjekt], li.item, div.item"
    )
    for b in blocks:
        name_el = b.find(["h2", "h3", "a"], class_=lambda c: True)
        name = (name_el.get_text(strip=True) if name_el else "").strip()
        if not name:
            continue

        text = b.get_text(" ", strip=True)
        phone = _find_phone(text)
        city = _find_city(b)
        website = _find_website(b, base)

        companies.append(Company(
            name=name,
            city=city,
            phone=phone,
            website=website if website and is_own_website(website) else None,
            category="pc-servis",
            source="atlasfiriem",
            source_url=base,
        ))
    return companies


def _find_phone(text: str) -> str:
    import re
    m = re.search(r"(\+421[\s\d]{9,}|0\d{2}[\s/]?\d{3}[\s]?\d{3})", text)
    return m.group(1).strip() if m else ""


def _find_city(block) -> str:
    el = block.find(class_=lambda c: c and ("mesto" in c or "adresa" in c or "city" in c))
    return el.get_text(strip=True) if el else ""


def _find_website(block, base: str) -> Optional[str]:
    for a in block.find_all("a", href=True):
        href = a["href"]
        low = href.lower()
        if low.startswith(("http", "www")) and is_own_website(low) \
                and "atlasfiriem" not in low and base.split("//")[-1] not in low:
            return urljoin(base, href)
    return None


class AtlasFiriemSource(Source):
    name = "atlasfiriem"

    def fetch(self, *, okres_slug: str = "michalovce", okres_id: int = 150,
              strany: int = 1, **kwargs) -> Iterable[Company]:
        from ..discovery import fetch as http_fetch
        for strana in range(1, strany + 1):
            url = listing_url(okres_slug, okres_id, strana)
            html = http_fetch(url)
            if not html:
                # zdroj nedostupný (egress policy / chyba) — preskoč ticho
                continue
            yield from parse_listing(html)
