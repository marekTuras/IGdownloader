from pathlib import Path

from prospector.discovery import verify
from prospector.models import WebsiteStatus
from prospector.sources.search import parse_results
from prospector.vertical import load_vertical

FIX = Path(__file__).parent / "fixtures"


def test_parse_results_notar_classifies_links():
    html = (FIX / "search_notar.html").read_text(encoding="utf-8")
    companies = parse_results(html)
    by_name = {c.name: c for c in companies}

    # vlastný web
    assert by_name["Notársky úrad JUDr. Ľubomír Vlha"].website == "https://notarvlha.sk/"
    # facebook -> nie vlastný web, ale evidovaný ako sociálna sieť
    nz = by_name["Notársky úrad Nové Zámky"]
    assert nz.website is None
    assert "facebook.com" in nz.facebook
    # katalóg tvojnotar.sk -> nie vlastný web
    assert by_name["JUDr. Daniela Šikutová"].website is None


def test_search_leads_detected_offline():
    html = (FIX / "search_notar.html").read_text(encoding="utf-8")
    v = load_vertical("notár")
    companies = parse_results(html)
    for c in companies:
        verify(c, online=False, stopwords=v.domain_stopwords)

    status = {c.name: c.status for c in companies}
    # facebook-only notár = lead (nemá vlastný web)
    assert status["Notársky úrad Nové Zámky"] == WebsiteStatus.NONE
    # katalógový záznam bez vlastného webu = lead
    assert status["JUDr. Daniela Šikutová"] == WebsiteStatus.NONE
