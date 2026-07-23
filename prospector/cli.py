"""CLI pre prospecting nástroj — funguje pre ľubovoľné odvetvie.

Príklady:
  # PC servisy: offline nad ručne overeným seed datasetom -> CSV
  python -m prospector.cli --keyword "servis počítačov" --source seed --offline \
      --out out/pc.csv

  # Notári: seed pre notárov (demo) offline
  python -m prospector.cli --keyword notár --source seed --seed-file data/seed_notar.json \
      --offline --out out/notari.csv

  # Ľubovoľné odvetvie online cez vyhľadávací zdroj (potrebuje net + providera)
  python -m prospector.cli --keyword "kaderníctvo" --source search \
      --location Nitra --location Levice \
      --search-url "https://provider/search?q={query}" --leads-only --out out/kad.csv

  # Katalóg atlasfiriem pre okres
  python -m prospector.cli --keyword notár --source atlasfiriem --okres nitra \
      --okres-id 111 --strany 2 --out out/notari_nitra.csv
"""
from __future__ import annotations

import argparse
import sys

from .pipeline import run, summary, write_csv
from .sources import SOURCES
from .vertical import load_vertical


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="prospector",
        description="Hľadá firmy bez webu / so starým webom v ĽUBOVOĽNOM odvetví "
                    "(zadaj --keyword).",
    )
    p.add_argument("--keyword", default="firma",
                   help='Odvetvie / kľúčové slovo, napr. "notár", "autoservis". '
                        "Určuje stopwords, kategóriu katalógu a dotazy.")
    p.add_argument("--source", action="append", choices=list(SOURCES),
                   help="Zdroj firiem (viackrát). Default: seed.")
    p.add_argument("--out", default="out/leads.csv", help="Cesta k CSV výstupu.")
    p.add_argument("--offline", action="store_true",
                   help="Bez sieťových volaní (DNS/HTTP).")
    p.add_argument("--leads-only", action="store_true",
                   help="Do výstupu len leady (bez webu / starý web).")
    # seed
    p.add_argument("--seed-file", help="Vlastný JSON dataset pre seed zdroj.")
    # search
    p.add_argument("--location", action="append", dest="locations",
                   help="Lokalita pre search zdroj (viackrát).")
    p.add_argument("--search-url",
                   help="Šablóna URL vyhľadávača, napr. https://provider/s?q={query}")
    p.add_argument("--result-selector", default="[class*=result]",
                   help="CSS selektor bloku výsledku (search zdroj).")
    # katalóg
    p.add_argument("--okres", default="michalovce", help="Slug okresu (atlasfiriem).")
    p.add_argument("--okres-id", type=int, default=150, help="ID okresu (atlasfiriem).")
    p.add_argument("--strany", type=int, default=1, help="Počet strán výpisu.")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    sources = args.source or ["seed"]
    vertical = load_vertical(args.keyword)

    opts = {
        "seed_path": args.seed_file,
        "locations": args.locations,
        "search_url_template": args.search_url,
        "result_selector": args.result_selector,
        "okres": args.okres,
        "okres_id": args.okres_id,
        "strany": args.strany,
    }
    companies = run(sources, vertical=vertical, online=not args.offline,
                    leads_only=args.leads_only, opts=opts)
    out_path = write_csv(companies, args.out)
    s = summary(companies)

    print(f"Odvetvie: {vertical.keyword} (label={vertical.label})")
    print(f"Zdroje: {', '.join(sources)}  |  režim: "
          f"{'offline' if args.offline else 'online'}")
    print(f"Firiem spolu: {s['total']}  |  leadov: {s['leads']}")
    print("Podľa stavu:", ", ".join(f"{k}={v}" for k, v in sorted(s['by_status'].items())))
    print(f"CSV zapísané do: {out_path}")

    print("\nTop leady:")
    for c in companies[:15]:
        if not c.status.is_lead:
            continue
        print(f"  [{c.status.value:8}] {c.confidence:.2f}  {c.name} "
              f"({c.city}) web={c.website or '—'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
