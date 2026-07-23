# Prospector — hľadanie firiem bez webu / so starým webom

Nástroj, ktorý hľadá firmy na Slovensku, ktoré **nemajú vlastný web** alebo majú
**veľmi zastaraný web** — teda ideálnych kandidátov na moderný redesign, ktorý im
vieme ponúknuť.

**Funguje pre ĽUBOVOĽNÉ odvetvie.** Zadáš kľúčové slovo (`--keyword`) — napr.
`"servis počítačov"`, `notár`, `autoservis`, `kaderníctvo` — a nástroj preň
hľadá firmy a overuje ich weby. Odvetvie riadi:

- **stopwords** pri hádaní domény (aby doména vychádzala z rozlišujúcej časti
  názvu — priezviska notára, značky servisu — nie zo slova odvetvia),
- **kategóriu** v katalógu (atlasfiriem/info-*.sk),
- **vyhľadávacie dotazy** pre search zdroj.

Odvetvia sú v `data/verticals.json` (presety: pc-servis, notar, autoservis,
kadernictvo). Pre neznáme kľúčové slovo sa vyrobí **generický** vertical — takže
nástroj beží pre čokoľvek, len s presnejšími výsledkami pre nakonfigurované
odvetvia (nový preset = pár riadkov do JSON).

Bloky väčšieho systému:

1. **Prospecting + overovanie** ← *tento nástroj* (zber firiem → verifikácia webu → CSV)
2. **Approval workflow** ← *hotové* (v CSV vyplníš `approved=yes/no` → fronta schválených)
3. Generátor demo stránky (moderný one-page web na oslovenie) — spustí sa až na pokyn

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

# PC servisy — offline nad ručne overeným seed datasetom (11 firiem) -> CSV
python -m prospector.cli --keyword "servis počítačov" --source seed --offline \
    --out out/pc.csv

# Notári — demo seed offline (iné odvetvie, ten istý nástroj)
python -m prospector.cli --keyword notár --source seed \
    --seed-file data/seed_notar.json --offline --out out/notari.csv

# Ľubovoľné odvetvie ONLINE cez vyhľadávací zdroj (net + provider)
python -m prospector.cli --keyword "kaderníctvo" --source search \
    --location Nitra --location Levice \
    --search-url "https://provider/search?q={query}" --leads-only --out out/kad.csv

# Katalóg atlasfiriem pre okres (kategória sa berie z verticalu)
python -m prospector.cli --keyword notár --source atlasfiriem --okres nitra \
    --okres-id 111 --strany 2 --out out/notari_nitra.csv
```

### Prepínače

- `--keyword` — **odvetvie / kľúčové slovo** (napr. `notár`). Default `firma`.
- `--source {seed,atlasfiriem,search}` — zdroj (viackrát), default `seed`.
- `--offline` — bez sieťových volaní (DNS/HTTP). Vhodné pri obmedzenej egress
  policy (živé scrapovanie potom spusti tam, kde je prístup na net).
- `--leads-only` — do výstupu len leady (bez webu / starý web).
- `--seed-file` — vlastný JSON dataset pre seed zdroj.
- `--location` — lokalita pre search zdroj (viackrát).
- `--search-url` — šablóna URL vyhľadávača/providera (`{query}` placeholder).
- `--okres`, `--okres-id`, `--strany` — parametre katalógového zdroja.

## Zdroje dát

| zdroj | vstup | poznámka |
|-------|-------|----------|
| `seed` | JSON (`data/seed_*.json`) | ručne overené firmy, funguje offline |
| `atlasfiriem` | okres + kategória z verticalu | scraper katalógu, potrebuje net |
| `search` | kľúčové slovo + lokality | keyword-driven, konfigurovateľný provider, potrebuje net |

Nové odvetvie pridáš do `data/verticals.json`; nové firmy do `data/seed_*.json`
(rovnaký formát), alebo ich necháš nájsť zdrojom `atlasfiriem` / `search`.

## Poznámka k sieti / overovaniu

Živé scrapovanie katalógov a HTTP kontrola webov vyžadujú prístup na internet.
V izolovaných prostrediach (napr. egress policy) sú tieto hosty blokované —
vtedy použi `--offline` (pracuje nad seed dátami), a plný beh spusti v prostredí
s prístupom na net. `100%` istotu „firma nemá web" nakoniec potvrdí človek
(FB „O firme" / WHOIS) — nástroj dodá zoradený zoznam s odôvodnenou istotou.

## Approval workflow (blok 2)

Do vygenerovaného CSV pribudol **prvý stĺpec `approved`** (prázdny). Postup:

```bash
# 1) vygeneruj leady
python -m prospector.cli --keyword "servis počítačov" --source seed --offline --out out/pc.csv

# 2) v out/pc.csv vyplň stĺpec 'approved' = yes / no (prázdne = nerozhodnuté)
#    yes/áno/1/ok = schválené,  no/nie/0 = zamietnuté

# 3) sprav frontu schválených
python -m prospector.approve --in out/pc.csv --out out/approved.csv --queue out/queue.json
```

Approve krok:

- rozdelí firmy na **schválené / zamietnuté / čakajúce** a vypíše počty,
- zapíše iba schválené firmy do `--out` CSV,
- zapíše **generation queue** (`--queue` JSON) — vstup pre blok 3,
- pri každej schválenej rozlíši **„nový web"** (`status=none`, firma web nemá)
  vs. **„redesign"** (`status=outdated`, starý web).

> ⚠ Tento krok **negeneruje** žiadny web. Len pripraví zoznam schválených firiem.
> Tvorba webu (blok 3) je samostatná a spustí sa **až na výslovný pokyn**.

## Testy

```bash
python -m pytest tests/ -q
```
