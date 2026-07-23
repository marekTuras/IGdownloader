"""Klasifikácia webovej stránky: moderná vs. zastaraná.

Nepoužíva žiadne externé závislosti — pracuje priamo nad HTML reťazcom,
takže sa dá testovať offline nad fixtúrami.
"""
from __future__ import annotations

import re
from datetime import datetime

# Domény, ktoré NIE sú vlastný web firmy (sociálne siete a katalógy).
NON_OWN_HOST_PATTERNS = [
    "facebook.com", "fb.com", "instagram.com", "linktr.ee", "linktree",
    "azet.sk", "zlatestranky.sk", "zoznam.sk", "cylex.sk", "atlasfiriem",
    "info-", "virtualne.sk", "123dopyt", "edb.eu", "near-place", "findglocal",
    "bazos.sk", "bazar.sk", "poi.oma.sk", "skmapy.sk", "google.com/maps",
    # freehostingy / stavače stránok = často "polovičný" web, nie vlastná prezentácia
    "blogspot.", "webnode.", "estranky.", "wordpress.com", "wixsite.com",
    "sites.google.com", "webs.com", "webmium",
]


def is_own_website(url: str | None) -> bool:
    """Je to vlastná doména firmy, alebo len profil na sociálnej sieti/katalógu?"""
    if not url:
        return False
    low = url.lower()
    return not any(p in low for p in NON_OWN_HOST_PATTERNS)


# ---- Heuristiky "starého" webu -------------------------------------------------

def _count(pattern: str, html: str) -> int:
    return len(re.findall(pattern, html, flags=re.IGNORECASE))


def classify_html(html: str, url: str = "", *, now: datetime | None = None
                  ) -> tuple[str, float, list[str]]:
    """Vráti (label, skore_zastaranosti 0-1, dôvody).

    label je jeden z: "modern", "outdated".
    skore_zastaranosti: 1.0 = úplne zastaraný, 0.0 = moderný.
    """
    now = now or datetime.now()
    html = html or ""
    reasons: list[str] = []
    score = 0.0

    low = html.lower()

    # 1) Responzívnosť: chýbajúci viewport meta = nie je mobile-friendly.
    if not re.search(r'<meta[^>]+name=["\']viewport["\']', low):
        score += 0.30
        reasons.append("bez responzívneho viewport meta (nie je mobile-friendly)")

    # 2) Layout cez <table> / zastarané tagy.
    tables = _count(r"<table", low)
    if tables >= 3:
        score += 0.20
        reasons.append(f"layout postavený na tabuľkách ({tables}x <table>)")
    if _count(r"<font\b", low) or 'bgcolor=' in low or _count(r"<marquee", low):
        score += 0.20
        reasons.append("zastarané HTML tagy (<font>/bgcolor/<marquee>)")

    # 3) Flash / staré technológie.
    if ".swf" in low or "shockwave-flash" in low:
        score += 0.20
        reasons.append("Flash obsah (.swf)")

    # 4) Staré CMS URL vzory.
    if re.search(r"index\.php\?id=", low) or re.search(r"\bart\.php\b", low):
        score += 0.15
        reasons.append("staré CMS URL (index.php?id=…)")

    # 5) Starý copyright rok.
    years = [int(y) for y in re.findall(r"(?:©|&copy;|copyright)[^0-9]{0,12}(20\d{2})", low)]
    if years:
        newest = max(years)
        if newest <= now.year - 3:
            score += 0.20
            reasons.append(f"starý copyright rok ({newest})")

    # 6) jQuery dávnej verzie (1.x) = typicky staré weby.
    if re.search(r"jquery[-/](1\.\d)", low):
        score += 0.10
        reasons.append("stará verzia jQuery (1.x)")

    # 7) Pozitívne signály modernosti (znižujú skóre).
    modern_hits = []
    if re.search(r'<meta[^>]+name=["\']viewport["\']', low):
        modern_hits.append("viewport")
    for token in ("tailwind", "bootstrap-5", "srcset=", "loading=\"lazy\"",
                  "gtag(", "wp-content/themes", "next/static", "__nuxt"):
        if token in low:
            modern_hits.append(token)
    if len(modern_hits) >= 2:
        score = max(0.0, score - 0.15)
        reasons.append("moderné signály: " + ", ".join(modern_hits))

    score = max(0.0, min(1.0, score))
    label = "outdated" if score >= 0.45 else "modern"
    return label, round(score, 2), reasons
