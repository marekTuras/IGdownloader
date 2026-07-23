import csv

from prospector.approval import Decision, parse_decision, process, write_queue
from prospector.models import CSV_FIELDS, Company, WebsiteStatus
from prospector.pipeline import run, write_csv


def test_parse_decision_variants():
    assert parse_decision("yes") == Decision.APPROVED
    assert parse_decision("ÁNO") == Decision.APPROVED
    assert parse_decision("1") == Decision.APPROVED
    assert parse_decision("no") == Decision.REJECTED
    assert parse_decision("nie") == Decision.REJECTED
    assert parse_decision("") == Decision.PENDING
    assert parse_decision(None) == Decision.PENDING
    assert parse_decision("neviem") == Decision.PENDING


def _make_csv(tmp_path):
    companies = run(["seed"], online=False)
    path = tmp_path / "leads.csv"
    write_csv(companies, path)
    return path, companies


def test_approved_column_is_first_and_empty(tmp_path):
    path, _ = _make_csv(tmp_path)
    with path.open(encoding="utf-8") as f:
        reader = csv.DictReader(f)
        assert reader.fieldnames[0] == "approved"
        for row in reader:
            assert row["approved"] == ""  # default prázdne


def test_process_filters_yes_no_pending(tmp_path):
    path, companies = _make_csv(tmp_path)
    rows = list(csv.DictReader(path.open(encoding="utf-8")))
    # vyplň rozhodnutia: prvé 3 yes, ďalšie 2 no, zvyšok prázdne
    for i, r in enumerate(rows):
        r["approved"] = "yes" if i < 3 else ("no" if i < 5 else "")
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=CSV_FIELDS, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)

    result = process(path)
    assert result.summary["approved"] == 3
    assert result.summary["rejected"] == 2
    assert result.summary["pending"] == len(rows) - 5


def test_write_queue_contains_approved(tmp_path):
    approved = [
        Company(name="Tabacko", city="Zámutov", status=WebsiteStatus.NONE),
        Company(name="MK PC", city="Slovenský Grob",
                website="https://mkpc.sk/index.php?id=x", status=WebsiteStatus.OUTDATED),
    ]
    qpath = write_queue(approved, tmp_path / "queue.json")
    import json
    data = json.loads(qpath.read_text(encoding="utf-8"))
    assert data["count"] == 2
    names = {c["name"] for c in data["companies"]}
    assert names == {"Tabacko", "MK PC"}
    # status rozlišuje nový web vs. redesign
    kinds = {c["name"]: c["status"] for c in data["companies"]}
    assert kinds["Tabacko"] == "none"
    assert kinds["MK PC"] == "outdated"
