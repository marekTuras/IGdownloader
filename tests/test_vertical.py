from prospector.discovery import guess_domains
from prospector.models import Company
from prospector.vertical import load_vertical


def test_preset_notar_loaded():
    v = load_vertical("notár")
    assert v.label == "notar"
    assert "notar" in v.domain_stopwords
    assert v.catalog_path and "notari" in v.catalog_path


def test_generic_vertical_from_unknown_keyword():
    v = load_vertical("kvetinárstvo")
    # neznáme odvetvie -> generický vertical, kľúčové slovo je stopword
    assert "kvetinarstvo" in v.domain_stopwords
    assert v.queries("Nitra")  # dotazy sa vygenerujú


def test_domain_guess_uses_name_not_industry_word():
    """Pri notárovi má doména vychádzať z priezviska, nie zo slova 'notar'."""
    v = load_vertical("notár")
    c = Company(name="Notársky úrad JUDr. Ľubomír Vlha")
    doms = guess_domains(c, v.domain_stopwords)
    assert any("vlha" in d for d in doms)
    assert all(not d.startswith("notar.") for d in doms)


def test_domain_guess_pc_vertical():
    v = load_vertical("servis počítačov")
    c = Company(name="Agharta Computers")
    doms = guess_domains(c, v.domain_stopwords)
    assert any("agharta" in d for d in doms)
