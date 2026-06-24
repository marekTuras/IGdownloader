# 📱 iPhone: Stiahni IG/TikTok video + SKUTOČNÝ prvý frame — bez servera

Riešenie, ktoré beží **celé na iPhone** (žiadny server, žiadny Mac) a vytvorí
**reálny prvý snímok videa — frame 0**, nie cover.

Funguje to vďaka appke **a-Shell** (zadarmo v App Store), ktorá vie na telefóne
spustiť `yt-dlp` (stiahnutie) aj `ffmpeg` (frame 0) a integruje sa so Skratkami.

```
IG/TikTok → Zdieľať → Skratka → a-Shell (yt-dlp + ffmpeg) → video + frame 0 → Fotky
```

> **Prečo a-Shell a nie čistá Skratka?** iOS Skratky nevedia dekódovať snímok
> z videa — nemajú žiadnu „extract frame" akciu. Skutočný frame 0 vie spraviť
> jedine `ffmpeg`, a a-Shell ho prináša priamo na iPhone (bez servera).
> *(Chrome extension na iOS neexistuje — rozšírenia povoľuje len Safari.)*

---

## 1) Jednorazová príprava (v appke a-Shell)

1. Nainštaluj **a-Shell** z App Store (zadarmo).
2. Otvor a-Shell a spusti tieto dva príkazy (každý zvlášť, počkaj na dokončenie):

   ```sh
   pip install yt-dlp
   pkg install ffmpeg
   ```

   - `yt-dlp` je čistý Python → v a-Shell sa nainštaluje cez `pip`.
   - `ffmpeg` je WebAssembly balík → nainštaluje sa cez `pkg install`.

3. Over, že to funguje (skús ľubovoľné verejné video):

   ```sh
   cd ~/Documents
   yt-dlp -f mp4/best -o out.mp4 "https://www.tiktok.com/@user/video/123..."
   ffmpeg -y -i out.mp4 -frames:v 1 out.png
   ls -la out.mp4 out.png
   ```

   Ak vznikli `out.mp4` aj `out.png`, hotovo. `-frames:v 1` zapíše **prvý
   dekódovaný snímok = frame 0** (overené, je identický s `select=eq(n\,0)`).

---

## 2) Skratka (Shortcut) — Share menu jedným ťuknutím

Appka **Skratky** → **+** (nová). Pridaj akcie v tomto poradí:

### a) Vstup zo Share menu
- **Detaily skratky** (ⓘ) → zapni **Zobraziť v zozname zdieľania**.
- Typy vstupu: **URL** a **Text**.

### b) Získaj odkaz
- **„Získať text zo vstupu"** (Get Text from Input) → **Vstup skratky**.
  *(toto je odkaz na video)*

### c) Spusti a-Shell (download + frame 0)
- Akcia **„Execute Command"** (z appky **a-Shell** — hľadaj „a-Shell" vo vyhľadávaní akcií).
- Režim: **In App** (nie In Extension — ffmpeg/yt-dlp potrebujú plný režim).
- Do poľa s príkazmi vlož (premennú **Text zo vstupu** vlož na miesto `URL`):

  ```sh
  cd ~/Documents
  rm -f out.mp4 out.png
  yt-dlp --no-playlist --no-warnings -f mp4/best -o out.mp4 "URL"
  ffmpeg -y -i out.mp4 -frames:v 1 out.png
  open shortcuts://
  ```

  - `"URL"` nahraď premennou *Text zo vstupu* (necháš úvodzovky okolo nej).
  - Posledný riadok `open shortcuts://` vráti riadenie späť do Skratky.

### d) Vyzdvihni video a ulož do Fotiek
- Akcia **„Get File"** (a-Shell): cesta súboru `~/Documents/out.mp4`.
- **„Uložiť do fotoalbumu"** (Save to Photo Album) → vstup = výsledok Get File.

### e) Vyzdvihni prvý frame a ulož do Fotiek
- Akcia **„Get File"** (a-Shell): cesta `~/Documents/out.png`.
- **„Uložiť do fotoalbumu"** → vstup = výsledok Get File.

### f) Notifikácia
- **„Zobraziť notifikáciu"**: `Hotovo ✅ Video a prvý frame (frame 0) sú vo Fotkách.`

Skratku pomenuj **„Stiahni IG/TikTok"** a ulož.

---

## 3) Použitie

V IG alebo TikTok appke otvor video → **Zdieľať** → **„Stiahni IG/TikTok"**.
Skratka prepne do a-Shell (stiahne + spraví frame 0), vráti sa a do **Fotiek**
uloží **video** aj **skutočný prvý snímok**.

---

## Riešenie problémov

- **`yt-dlp: command not found`** → spusti `pip install yt-dlp` v a-Shell.
- **`ffmpeg: command not found`** → spusti `pkg install ffmpeg` v a-Shell.
- **Instagram nestiahne** → príspevok je súkromný/login-only. Skús verejný; TikTok ide spoľahlivo.
- **Pomalé** → ffmpeg v a-Shell je WebAssembly; pri dlhších videách to chvíľu trvá. Pre krátke reels/clips je to v pohode.
- **Skratka chýba v Share menu** → *Detaily skratky → Zobraziť v zozname zdieľania* + typy vstupu URL a Text.
- **Skratka sa nevráti z a-Shell** → over, že posledný príkaz je `open shortcuts://`.

## Pomocný skript

Rovnaká logika je aj ako súbor [`../ashell/ig`](../ashell/ig) — môžeš si ho v a-Shell
uložiť do `~/Documents` a v Skratke volať `sh ~/Documents/ig "URL"` namiesto
vkladania príkazov ručne.

## Desktop verzia

Na počítači použi skill `ig-tiktok-firstframe` (`.claude/skills/...`) — `yt-dlp`
+ `ffmpeg` s presným frame 0.
