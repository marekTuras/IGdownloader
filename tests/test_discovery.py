from prospector.discovery import guess_domains, slugify, verify
from prospector.models import Company, WebsiteStatus


def test_slugify_strips_diacritics():
    assert slugify("Servis Počítačov Detva") == "servispocitacovdetva"


def test_guess_domains_uses_meaningful_words():
    c = Company(name="Agharta Computers", city="Zvolen")
    doms = guess_domains(c)
    assert any(d.startswith("agharta") for d in doms)
    assert all(d.endswith(".sk") for d in doms)


def test_verify_offline_facebook_only_is_none():
    c = Company(name="pcMauer", city="Bardejov",
                facebook="https://www.facebook.com/pcMauer/")
    verify(c, online=False)
    assert c.status == WebsiteStatus.NONE
    assert c.status.is_lead


def test_verify_offline_freemail_boosts_confidence():
    c = Company(name="Tabacko", city="Zámutov", email="lukas.tabacko@gmail.com",
                facebook="https://www.facebook.com/servistabacko/")
    verify(c, online=False)
    assert c.status == WebsiteStatus.NONE
    assert c.confidence >= 0.6
    assert any("freemail" in r for r in c.reasons)


def test_verify_offline_old_url_website_is_outdated():
    c = Company(name="MK PC", city="Slovenský Grob",
                website="https://mkpc.sk/index.php?id=dizajn")
    verify(c, online=False)
    assert c.status == WebsiteStatus.OUTDATED
    assert c.status.is_lead
