import csv
from pathlib import Path

from prospector.pipeline import dedupe, run, summary, write_csv
from prospector.models import Company
from prospector.sources.atlasfiriem import parse_listing

FIX = Path(__file__).parent / "fixtures"


def test_dedupe_by_name_and_city():
    a = Company(name="ABC PC", city="Nitra")
    b = Company(name="abc  pc", city="nitra")
    c = Company(name="ABC PC", city="Košice")
    out = dedupe([a, b, c])
    assert len(out) == 2


def test_run_seed_offline_produces_leads(tmp_path):
    companies = run(["seed"], online=False)
    assert len(companies) >= 11
    leads = [c for c in companies if c.status.is_lead]
    # offline: 9 firiem bez webu + MK PC (starý index.php?id= web).
    # Agharta má živý web -> offline ostáva 'unknown' (poctivé, treba online).
    assert len(leads) >= 10
    # žiadna seed firma nesmie byť klasifikovaná ako 'modern'
    assert all(c.status.value != "modern" for c in companies)

    out = write_csv(companies, tmp_path / "leads.csv")
    rows = list(csv.DictReader(out.open(encoding="utf-8")))
    assert len(rows) == len(companies)
    assert "is_lead" in rows[0]

    s = summary(companies)
    assert s["total"] == len(companies)


def test_parse_listing_extracts_and_flags_website():
    html = (FIX / "katalog_listing.html").read_text(encoding="utf-8")
    companies = parse_listing(html)
    by_name = {c.name: c for c in companies}

    assert "ABC PC Servis" in by_name
    # ABC nemá vlastný web
    assert by_name["ABC PC Servis"].website is None
    # XYZ má vlastný web
    assert by_name["XYZ Computers"].website == "https://xyzcomputers.sk"
    # FB only -> facebook nie je "vlastný web"
    assert by_name["FB Only Servis"].website is None
