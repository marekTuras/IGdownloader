"""CLI approval kroku.

Prečíta CSV so stĺpcom `approved` (yes/no) a zo schválených firiem vyrobí
generation queue (JSON). NEGENERUJE web — to je samostatný krok na výslovný pokyn.

Príklad:
  # 1) vygeneruj leady
  python -m prospector.cli --keyword "servis počítačov" --source seed --offline \
      --out out/pc.csv
  # 2) v out/pc.csv vyplň stĺpec 'approved' = yes/no
  # 3) sprav frontu schválených
  python -m prospector.approve --in out/pc.csv --out out/approved.csv \
      --queue out/queue.json
"""
from __future__ import annotations

import argparse
import csv
import sys

from .approval import process, write_queue
from .models import CSV_FIELDS


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="prospector.approve",
        description="Spracuje approved (yes/no) v CSV a pripraví frontu schválených "
                    "firiem na generovanie webu (generovanie sa NESPUSTÍ).",
    )
    p.add_argument("--in", dest="in_path", required=True,
                   help="Vstupné CSV (výstup pipeline, doplnený o approved).")
    p.add_argument("--out", help="Kam zapísať iba schválené firmy (CSV).")
    p.add_argument("--queue", help="Kam zapísať generation queue (JSON).")
    p.add_argument("--leads-only", action="store_true",
                   help="Zo schválených ponechaj len leady (bez webu / starý web).")
    return p


def _write_csv(companies, path):
    from pathlib import Path
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=CSV_FIELDS, extrasaction="ignore")
        w.writeheader()
        for c in companies:
            w.writerow(c.to_row())


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = process(args.in_path)

    approved = result.approved
    if args.leads_only:
        approved = [c for c in approved if c.status.is_lead]

    s = result.summary
    print(f"Vstup: {args.in_path}")
    print(f"Schválené (yes): {len(approved)}  |  zamietnuté (no): {s['rejected']}  "
          f"|  čakajúce (prázdne): {s['pending']}  |  spolu: {s['total']}")

    if s["pending"]:
        print(f"\n⚠ {s['pending']} firiem ešte nemá vyplnené 'approved' "
              f"(yes/no) — tie sa do fronty nedostanú.")

    if args.out:
        _write_csv(approved, args.out)
        print(f"Schválené firmy -> {args.out}")

    if args.queue:
        qpath = write_queue(approved, args.queue)
        print(f"Generation queue -> {qpath}")

    print("\nSchválené firmy (pripravené na generovanie webu — spustí sa až na pokyn):")
    for c in approved:
        kind = "nový web" if c.status.value == "none" else (
            "redesign" if c.status.value == "outdated" else c.status.value)
        print(f"  [{kind:9}] {c.name} ({c.city})  web={c.website or '—'}")

    if not approved:
        print("  (žiadne schválené firmy — vyplň 'approved=yes' v CSV)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
