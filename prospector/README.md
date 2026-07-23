# Prospector — hľadanie firiem bez webu / so starým webom

Nástroj, ktorý hľadá firmy (PC servisy a podobné živnosti) na Slovensku, ktoré
**nemajú vlastný web** alebo majú **veľmi zastaraný web** — teda ideálnych
kandidátov na moderný redesign, ktorý im vieme ponúknuť.

Toto je **1. blok** väčšieho systému:

1. **Prospecting + overovanie** ← *tento nástroj* (zber firiem → verifikácia webu → CSV)
2. Approval workflow (ty schváliš / zamietneš kandidátov)
3. Generátor demo stránky (moderný one-page web na oslovenie)

## Ako to funguje

```
zdroje (seed / katalógy) ──▶ dedupe ──▶ verifikácia webu ──▶ zoradenie ──▶ CSV
```

Verifikácia každej firmy:

1. Ak **poznáme vlastný web** → stiahne HTML a klasifikuje `modern` / `outdated`
   (heuristiky: chýbajúci responzívny `viewport`, tabuľkový layout, `<font>`/
   `bgcolor`, Flash, `index.php?id=`, starý copyright rok, staré jQuery…).
2. Ak web **nepoznáme** → skúsi uhádnuť `.sk` doménu z názvu a overiť ju cez DNS.
3. Ak sa nič nenájde → `status = none` (nemá web). Istotu zvyšuje prítomnosť
   len na sociálnych sieťach a **freemail** kontakt (gmail/atlas/centrum…).

Každá firma dostane `status` (`none` / `outdated` / `modern` / `unknown`),
`confidence` (0–1) a `reasons` (prečo).

## Stavy webu

| status | význam | lead? |
|--------|--------|-------|
| `none` | nemá vlastný web (len FB/IG/katalóg) | ✅ |
| `outdated` | má, ale veľmi starý web | ✅ |
| `modern` | má moderný web | ❌ |
| `unknown` | nepodarilo sa zistiť (napr. offline) | ❌ |

## Použitie

```bash
pip install -r prospector/requirements.txt

# Offline nad ručne overeným seed datasetom (11 firiem) -> CSV
python -m prospector.cli --source seed --offline --out out/leads.csv

# Online: scrapni okres z katalógu atlasfiriem a over weby
python -m prospector.cli --source atlasfiriem --okres michalovce --okres-id 150 \
    --strany 2 --leads-only --out out/michalovce.csv
```

### Prepínače

- `--source {seed,atlasfiriem}` — zdroj (dá sa uviesť viackrát), default `seed`.
- `--offline` — bez sieťových volaní (DNS/HTTP). Vhodné v prostredí s obmedzenou
  egress policy (živé scrapovanie potom spusti tam, kde je prístup na net).
- `--leads-only` — do výstupu len leady (bez webu / starý web).
- `--okres`, `--okres-id`, `--strany` — parametre katalógového zdroja.

## Dáta

`data/seed_companies.json` — ručne overený zoznam firiem (kandidátov).
Nové firmy sem môžeš pridávať v rovnakom formáte, alebo ich nechať nascrapovať.

## Poznámka k sieti / overovaniu

Živé scrapovanie katalógov a HTTP kontrola webov vyžadujú prístup na internet.
V izolovaných prostrediach (napr. egress policy) sú tieto hosty blokované —
vtedy použi `--offline` (pracuje nad seed dátami), a plný beh spusti v prostredí
s prístupom na net. `100%` istotu „firma nemá web" nakoniec potvrdí človek
(FB „O firme" / WHOIS) — nástroj dodá zoradený zoznam s odôvodnenou istotou.

## Testy

```bash
python -m pytest tests/ -q
```
