# 📱 iOS Skratka — Stiahni IG/TikTok video + prvý frame

Skratka sa zobrazí v **Share menu** (Zdieľať) priamo v IG/TikTok appke. Po
ťuknutí stiahne **video** aj **prvý frame** do appky **Fotky**.

> **Prečo nie Chrome extension?** Chrome na iOS nepodporuje rozšírenia
> (povoľuje ich len Safari, cez Xcode + Mac). Skratka je na iPhone
> najpraktickejšia a funguje vo všetkých appkách cez tlačidlo Zdieľať.

---

## Dve verzie — vyber si

| | **A) So serverom** *(odporúčané)* | **B) Bez servera** |
|---|---|---|
| **Prvý frame** | ✅ **skutočný frame 0** (`ffmpeg` na serveri) | ⚠️ cover (úvodný obrázok platformy, nie nutne frame 0) |
| **Čo treba** | nasadiť backend z [`../../server`](../../server) | nič navyše |
| **Spoľahlivosť** | vyššia (IG aj TikTok rieši server) | TikTok ok, IG len verejné |

Keďže chceš **skutočný prvý snímok videa**, choď na **verziu A**.

---

## A) Verzia so serverom — skutočný prvý frame ✅

### Predpoklad
Nasadený backend (viď [`../../server/README.md`](../../server/README.md)) s verejnou
HTTPS URL, napr. `https://moj-server.app`, a tokenom `API_TOKEN`.
Over: `curl https://moj-server.app/health` → `{"status":"ok", ...}`.

### Akcie skratky
Appka **Skratky** → **+** → **Pridať akciu**. Pridaj v poradí:

1. **Detaily skratky** (ⓘ) → zapni **Zobraziť v zozname zdieľania**;
   typy vstupu: **URL** a **Text**.

2. **„Získať text zo vstupu"** (Get Text from Input) → **Vstup skratky**.
   *(toto je odkaz na video)*

3. **„Získať obsah URL"** (Get Contents of URL):
   - URL: `https://moj-server.app/process`
   - **Metóda:** `POST`
   - **Hlavičky:** `X-API-Token` = `tvoj-token`  (ak si token nastavil)
   - **Telo požiadavky:** `JSON`
     - kľúč `url` (typ Text) = premenná **Text zo vstupu** z kroku 2
   - *(server vráti slovník s `video_url` a `frame_url`)*

4. **VIDEO:** **„Získať hodnotu zo slovníka"** (Get Dictionary Value),
   kľúč `video_url`, vstup = výsledok z kroku 3.
   → **„Získať obsah URL"** s tým URL
   → **„Uložiť do fotoalbumu"** (Save to Photo Album).

5. **PRVÝ FRAME:** **„Získať hodnotu zo slovníka"**, kľúč `frame_url`,
   vstup = výsledok z kroku 3.
   → **„Získať obsah URL"** s tým URL
   → **„Uložiť do fotoalbumu"**.

6. **„Zobraziť notifikáciu"**: `Hotovo ✅ Video a prvý frame sú vo Fotkách.`

Pomenuj **„Stiahni IG/TikTok"** a ulož. Server vracia presný **frame 0**, takže
to, čo sa uloží, je naozaj prvý snímok videa.

---

## B) Verzia bez servera — jednoduchšia (cover, nie frame 0)

Bez backendu iOS nevie dekódovať snímok z videa, takže ako „prvý frame" sa uloží
**cover** (úvodný obrázok, ktorý vráti platforma). Použi, ak nechceš nasadzovať
server a cover ti stačí.

1. **Detaily skratky** → **Zobraziť v zozname zdieľania**; vstup URL + Text.
2. **„Získať text zo vstupu"** → Vstup skratky.
3. **„Ak"** (If): *Text zo vstupu* **obsahuje** `tiktok`

   **TikTok (vnútri „Ak"):**
   - **„Získať obsah URL"**: `https://www.tikwm.com/api/?hd=1&url=[Text zo vstupu]`
   - **„Získať hodnotu zo slovníka"** `data.play` → **„Získať obsah URL"** → **„Uložiť do fotoalbumu"** *(video)*
   - **„Získať hodnotu zo slovníka"** `data.origin_cover` → **„Získať obsah URL"** → **„Uložiť do fotoalbumu"** *(cover)*

   **Inak (Instagram):**
   - **„Získať obsah URL"** = *Text zo vstupu*
   - **„Nájsť zhodu v texte"** (regex, case-insensitive): `property="og:video" content="([^"]+)"` → **„Získať skupinu"** 1 → **„Nahradiť text"** `&amp;`→`&` → **„Získať obsah URL"** → **„Uložiť do fotoalbumu"** *(video)*
   - to isté s `property="og:image" content="([^"]+)"` → *(cover)*
4. **„Zobraziť notifikáciu"**: `Hotovo ✅`

---

## Použitie

V IG/TikTok appke otvor video → **Zdieľať** → **„Stiahni IG/TikTok"**.
Video aj prvý frame sa uložia do **Fotiek**, na konci príde notifikácia.

## Riešenie problémov

- **Verzia A — chyba 401**: zlý/`chýbajúci` `X-API-Token`, skontroluj hlavičku.
- **Verzia A — chyba 502**: server nestiahol video (súkromné IG / rate limit) —
  skús iný príspevok alebo o chvíľu znova; pozri logy servera.
- **Instagram nestiahne**: príspevok je súkromný/login-only. TikTok ide spoľahlivo.
- **Skratka chýba v Share menu**: *Detaily skratky → Zobraziť v zozname zdieľania*
  + typy vstupu URL a Text.

## Súvisiace

- Backend: [`../../server/`](../../server/) — daj mu odkaz, vráti video + **frame 0**.
- Desktop skill s presným frame 0: `.claude/skills/ig-tiktok-firstframe/`.
