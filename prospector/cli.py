"""CLI pre prospecting nástroj.

Príklady:
  # offline nad ručne overeným seed datasetom -> CSV
  python -m prospector.cli --source seed --offline --out out/leads.csv

  # online: scrapni okres Michalovce z atlasfiriem a over weby
  python -m prospector.cli --source atlasfiriem --okres michalovce --okres-id 150 \
      --strany 2 --leads-only --out out/michalovce.csv
"""
from __future__ import annotations

import argparse
import sys

from .pipeline import run, summary, write_csv
from .sources import SOURCES


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="prospector",
        description="Hľadá firmy bez webu / so starým webom (kandidáti na redesign).",
    )
    p.add_argument("--source", action="append", choices=list(SOURCES),
                   help="Zdroj firiem (dá sa uviesť viackrát). Default: seed.")
    p.add_argument("--out", default="out/leads.csv", help="Cesta k CSV výstupu.")
    p.add_argument("--offline", action="store_true",
                   help="Bez sieťových volaní (DNS/HTTP). Užitočné pri egress policy.")
    p.add_argument("--leads-only", action="store_true",
                   help="Do výstupu len leady (bez webu / starý web).")
    # parametre pre katalógové zdroje
    p.add_argument("--okres", default="michalovce", help="Slug okresu (atlasfiriem).")
    p.add_argument("--okres-id", type=int, default=150, help="ID okresu (atlasfiriem).")
    p.add_argument("--strany", type=int, default=1, help="Počet strán výpisu.")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    sources = args.source or ["seed"]
    source_kwargs = {
        "okres_slug": args.okres,
        "okres_id": args.okres_id,
        "strany": args.strany,
    }
    companies = run(sources, online=not args.offline,
                    leads_only=args.leads_only, source_kwargs=source_kwargs)
    out_path = write_csv(companies, args.out)
    s = summary(companies)

    print(f"Zdroje: {', '.join(sources)}  |  režim: "
          f"{'offline' if args.offline else 'online'}")
    print(f"Firiem spolu: {s['total']}  |  leadov: {s['leads']}")
    print("Podľa stavu:", ", ".join(f"{k}={v}" for k, v in sorted(s['by_status'].items())))
    print(f"CSV zapísané do: {out_path}")

    print("\nTop leady:")
    for c in companies[:15]:
        if not c.status.is_lead:
            continue
        web = c.website or "—"
        print(f"  [{c.status.value:8}] {c.confidence:.2f}  {c.name} "
              f"({c.city}) web={web}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
