# 📱 iOS Skratka — Stiahni IG/TikTok video + prvý frame

Návod na zostavenie **Apple Skratky (Shortcut)**, ktorá:

1. sa zobrazí v **Share menu** (Zdieľať) priamo v IG/TikTok appke alebo v prehliadači,
2. stiahne **video** do appky **Fotky**,
3. uloží aj **prvý frame** (úvodný cover snímok videa) do Fotiek,
4. ukáže notifikáciu „Hotovo".

> **Prečo nie Chrome extension?** Chrome na iOS nepodporuje rozšírenia (povoľuje
> ich len Safari, a aj to cez Xcode + Mac). Skratka je na iPhone najpraktickejšia
> a funguje vo všetkých appkách cez tlačidlo Zdieľať.

> **Prvý frame na iOS:** iPhone nemá `ffmpeg`, takže presný „frame 0" sa lokálne
> vytiahnuť nedá. Download služby ale vracajú **cover** (úvodný snímok videa),
> ktorý uložíme ako prvý frame. Na presný frame 0 použi desktop skill v repe.

---

## A. Ako to funguje (logika)

Skratka rozpozná podľa odkazu, či ide o **TikTok** alebo **Instagram**, a podľa
toho zvolí spôsob získania videa a cover obrázka:

| Platforma   | Zdroj videa                                   | Cover / prvý frame            |
|-------------|-----------------------------------------------|-------------------------------|
| **TikTok**  | API `tikwm.com` → `data.play` (bez watermarku)| `data.origin_cover`           |
| **Instagram** | `og:video` meta tag zo stránky príspevku    | `og:image` meta tag           |

TikTok cez API je veľmi spoľahlivý. Instagram funguje pri **verejných**
príspevkoch (súkromné / login-only nemusia vrátiť `og:video`).

---

## B. Zostavenie Skratky (krok za krokom)

Otvor appku **Skratky** → **+** (nová) → **Pridať akciu**. Pridávaj akcie v tomto
poradí (hľadaj ich názvy v hornom vyhľadávaní):

### 1. Vstup zo Share menu
- Hore klikni na názov skratky → **Detaily skratky** (ikona ⓘ) → zapni
  **Zobraziť v zozname zdieľania**.
- Pri „Typy vstupu" nechaj **URL** a **Text**.

### 2. Získaj odkaz z vstupu
- Akcia **„Ak"** nie je hneď potrebná. Najprv pridaj **„Získať text zo vstupu"**
  (Get Text from Input) → nastav na **Vstup skratky** (Shortcut Input).
  Tým máš premennú s URL.

### 3. Vetva podľa platformy — TikTok
Pridaj **„Ak" (If)**:
- **Vstup:** Text zo vstupu
- **Podmienka:** *obsahuje* → `tiktok`

**Vnútri „Ak" (TikTok):**

a) **„Získať obsah URL" (Get Contents of URL)**
   - URL: `https://www.tikwm.com/api/?hd=1&url=[Text zo vstupu]`
     *(premennú „Text zo vstupu" vlož doň tak, že kurzor dáš na koniec a vyberieš ju)*
   - Metóda: **GET**

b) **„Získať hodnotu zo slovníka" (Get Dictionary Value)**
   - Kľúč: `data.play` → toto je URL videa
   - Vstup: výsledok z (a)

c) **„Získať obsah URL"** s URL = výsledok z (b) → stiahne **video** (mp4).

d) **„Uložiť do fotoalbumu" (Save to Photo Album)** → vstup = stiahnuté video.

e) Cover / prvý frame: **„Získať hodnotu zo slovníka"**, kľúč `data.origin_cover`
   (znova zo slovníka z kroku a).

f) **„Získať obsah URL"** s URL = výsledok z (e) → stiahne **cover obrázok**.

g) **„Uložiť do fotoalbumu"** → vstup = cover obrázok.

### 4. Inak (Otherwise) — Instagram
V tej istej „Ak" akcii klikni **„Inak" (Otherwise)**:

a) **„Získať obsah URL"** s URL = **Text zo vstupu** (stránka príspevku).

b) **„Nájsť zhodu v texte" (Match Text)** — video:
   - Vzor (regex, zapni *case insensitive*):
     `property="og:video" content="([^"]+)"`
   - Potom **„Získať skupiny zo zhody" (Get Group from Matched Text)** →
     **Skupina 1** → tým získaš URL videa.

c) **„Nahradiť text" (Replace Text)** na výsledku z (b):
   - Nájsť: `&amp;`  →  Nahradiť: `&`   *(IG escapuje & v URL)*

d) **„Získať obsah URL"** s tým URL → stiahne **video** → **„Uložiť do fotoalbumu"**.

e) Cover / prvý frame: **„Nájsť zhodu v texte"** s regexom
   `property="og:image" content="([^"]+)"` → **Skupina 1** → **„Nahradiť text"**
   (`&amp;`→`&`) → **„Získať obsah URL"** → **„Uložiť do fotoalbumu"**.

### 5. Notifikácia na konci (mimo „Ak")
- **„Zobraziť notifikáciu" (Show Notification)**: text napr.
  `Hotovo ✅ Video a prvý frame sú vo Fotkách.`

Skratku pomenuj napr. **„Stiahni IG/TikTok"** a ulož.

---

## C. Použitie

1. V IG alebo TikTok appke otvor video → **Zdieľať (Share)** → **Skopírovať odkaz**
   alebo rovno vyber svoju skratku **„Stiahni IG/TikTok"** zo zoznamu zdieľania.
2. Skratka stiahne video aj prvý frame do **Fotiek**.

---

## D. Riešenie problémov

- **Instagram nestiahne (prázdne `og:video`)**: príspevok je súkromný alebo IG
  vyžaduje prihlásenie. Skús iný (verejný) príspevok, alebo použi desktop skill.
- **TikTok API nereaguje**: `tikwm.com` má občas rate limit — skús o chvíľu znova.
  Alternatívne nasaď vlastnú inštanciu [cobalt](https://github.com/imputnet/cobalt)
  a v kroku 3a/4 použi jej API endpoint.
- **„Prvý frame" nie je presne frame 0**: cover je úvodný snímok, ktorý vracia
  služba. Na presný frame 0 použi desktop skill (`ffmpeg`).
- **Skratka sa neukáže v Share menu**: skontroluj *Detaily skratky → Zobraziť
  v zozname zdieľania* a typy vstupu URL + Text.

---

## E. Súvisiace

- Desktop verzia s presným prvým frame: skill **`ig-tiktok-firstframe`** v tomto repe
  (`.claude/skills/ig-tiktok-firstframe/`).
