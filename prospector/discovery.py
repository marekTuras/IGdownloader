"""Zisťovanie stavu webu firmy.

Postup pre jednu firmu:
  1. Ak už poznáme vlastný web -> stiahnem HTML a klasifikujem modern/outdated.
  2. Ak web nepoznáme -> skúsim uhádnuť doménu z názvu a overiť cez DNS+HTTP.
  3. Keď net nie je dostupný (napr. egress policy), status ostane UNKNOWN
     s dôvodom, nech to vie človek doriešiť online.

Sieťové volania sú izolované a chyby (ProxyError, timeout, DNS) sa
neprejavia pádom — len znížia istotu.
"""
from __future__ import annotations

import re
import socket
import unicodedata
from typing import Optional

from .classify import classify_html, is_own_website
from .models import Company, WebsiteStatus

try:  # requests je voliteľný — offline režim funguje aj bez neho
    import requests
except Exception:  # pragma: no cover
    requests = None  # type: ignore

USER_AGENT = "Mozilla/5.0 (compatible; ProspectorBot/1.0)"
STOPWORDS = {
    "servis", "pc", "pocitacov", "pocitace", "notebookov", "notebook",
    "oprava", "opravy", "predaj", "a", "servispc", "sluzby", "it", "mobil",
    "mobilov", "smartfonov", "tabletov",
}


def slugify(text: str) -> str:
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii").lower()
    return re.sub(r"[^a-z0-9]+", "", text)


def guess_domains(company: Company) -> list[str]:
    """Vygeneruje pravdepodobné .sk domény z názvu firmy."""
    raw = re.split(r"[\s–\-|&/,]+", company.name.lower())
    words = [slugify(w) for w in raw if slugify(w)]
    content = [w for w in words if w not in STOPWORDS] or words
    joined = "".join(content[:2])
    first = content[0] if content else ""
    cands = {joined, first, joined + "sk", first + "servis", first + "pc"}
    return [f"{c}.sk" for c in cands if len(c) >= 3]


def dns_resolves(host: str) -> bool:
    try:
        socket.gethostbyname(host)
        return True
    except OSError:
        return False


def fetch(url: str, timeout: float = 8.0) -> Optional[str]:
    """Stiahne HTML. Vráti None pri akejkoľvek chybe (vrátane blokovaného proxy)."""
    if requests is None:
        return None
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    try:
        r = requests.get(url, timeout=timeout, headers={"User-Agent": USER_AGENT})
        if r.status_code < 400 and r.text:
            return r.text
    except Exception:
        return None
    return None


def verify(company: Company, *, online: bool = True) -> Company:
    """Doplní company.status / confidence / reasons."""
    # 1) Poznáme vlastný web?
    if company.website and is_own_website(company.website):
        if online:
            html = fetch(company.website)
            if html:
                label, age, why = classify_html(html, company.website)
                company.status = (WebsiteStatus.OUTDATED if label == "outdated"
                                  else WebsiteStatus.MODERN)
                company.confidence = 0.7 + 0.25 * (age if label == "outdated" else (1 - age))
                company.reasons = why or [f"web klasifikovaný ako {label}"]
                company.confidence = round(min(company.confidence, 0.98), 2)
                return company
        # web poznáme, ale nevieme stiahnuť -> označ ako má web, treba over online
        company.status = WebsiteStatus.OUTDATED if _looks_old_url(company.website) \
            else WebsiteStatus.UNKNOWN
        company.reasons.append("web existuje; obsah neoverený" +
                               (" (offline)" if not online else " (nedostupný)"))
        company.confidence = 0.4 if company.status == WebsiteStatus.OUTDATED else 0.2
        if _looks_old_url(company.website):
            company.reasons.append("URL vzor napovedá starý web")
            company.confidence = 0.55
        return company

    # 2) Web nepoznáme -> je to len sociálna sieť / katalóg?
    has_social = bool(company.facebook or company.instagram)

    # 3) Skúsim uhádnuť doménu.
    guessed_live = []
    if online:
        for dom in guess_domains(company):
            if dns_resolves(dom):
                guessed_live.append(dom)

    if guessed_live:
        # doména existuje -> možno predsa má web; nechaj človeka potvrdiť
        company.status = WebsiteStatus.UNKNOWN
        company.reasons.append("nájdená možná doména: " + ", ".join(guessed_live)
                               + " — over ručne")
        company.confidence = 0.3
        return company

    # 4) Žiadny vlastný web nenájdený.
    company.status = WebsiteStatus.NONE
    conf = 0.55
    reasons = []
    if has_social:
        reasons.append("prítomnosť len na sociálnych sieťach")
        conf += 0.10
    if "gmail.com" in company.email or "atlas.sk" in company.email \
            or "azet.sk" in company.email or "centrum.sk" in company.email:
        reasons.append("kontakt cez freemail (silný signál žiadneho webu)")
        conf += 0.20
    if online:
        reasons.append("uhádnuté domény neexistujú (DNS)")
        conf += 0.05
    else:
        reasons.append("offline — DNS neoverené")
        conf -= 0.10
    company.reasons = reasons
    company.confidence = round(min(conf, 0.95), 2)
    return company


def _looks_old_url(url: str) -> bool:
    low = (url or "").lower()
    return bool(re.search(r"index\.php\?id=|art\.php|blogspot\.|webnode\.|estranky\.", low))
