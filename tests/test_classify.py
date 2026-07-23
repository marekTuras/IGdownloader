from pathlib import Path

from prospector.classify import classify_html, is_own_website

FIX = Path(__file__).parent / "fixtures"


def test_old_site_is_outdated():
    html = (FIX / "old_site.html").read_text(encoding="utf-8")
    label, score, reasons = classify_html(html, "https://mkpc.sk/index.php?id=dizajn")
    assert label == "outdated"
    assert score >= 0.45
    assert reasons


def test_modern_site_is_modern():
    html = (FIX / "modern_site.html").read_text(encoding="utf-8")
    label, score, reasons = classify_html(html, "https://example.sk/")
    assert label == "modern"
    assert score < 0.45


def test_is_own_website():
    assert is_own_website("https://mojafirma.sk")
    assert not is_own_website("https://www.facebook.com/mojafirma")
    assert not is_own_website("https://mojafirma.blogspot.com")
    assert not is_own_website("https://www.atlasfiriem.info/xyz")
    assert not is_own_website(None)
