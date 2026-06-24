---
name: ig-tiktok-firstframe
description: Stiahne Instagram alebo TikTok video z odkazu a vygeneruje jeho prvý frame (first frame) ako PNG. Použi, keď používateľ pošle IG/TikTok link a chce video stiahnuť a/alebo získať náhľad prvého snímku.
---

# IG / TikTok video downloader + first frame

Tento skill stiahne video z **Instagramu** alebo **TikToku** podľa odkazu
a vygeneruje jeho **prvý frame** ako PNG obrázok.

## Kedy použiť

Použi tento skill, keď používateľ:
- pošle odkaz na IG alebo TikTok video (reel, post, video),
- chce video stiahnuť,
- chce vygenerovať prvý frame / náhľad / thumbnail z prvého snímku.

## Ako to funguje

Skript `scripts/download_and_frame.sh` urobí všetko v jednom kroku:
1. Overí (a v prípade potreby doinštaluje) `yt-dlp` a `ffmpeg`.
2. Stiahne video cez `yt-dlp` do cieľového priečinka.
3. Z videa vyextrahuje prvý frame cez `ffmpeg` (`select=eq(n\,0)`).

## Postup

1. Z používateľovej správy vyber URL videa.
2. Spusti skript s URL (a voliteľne cieľovým priečinkom):

   ```bash
   bash .claude/skills/ig-tiktok-firstframe/scripts/download_and_frame.sh "<URL>" [OUTPUT_DIR]
   ```

   - `<URL>` — odkaz na IG/TikTok video.
   - `[OUTPUT_DIR]` — voliteľné, default `downloads`.

3. Skript na stdout vypíše cesty:
   ```
   VIDEO=<cesta k videu>
   FRAME=<cesta k prvému frame .png>
   ```

4. Použité súbory ukáž používateľovi — prvý frame pošli cez `SendUserFile`
   (je to obrazový deliverable), a uveď, kam sa uložilo video.

## Príklad

```bash
bash .claude/skills/ig-tiktok-firstframe/scripts/download_and_frame.sh \
  "https://www.instagram.com/reel/Cxxxxxxxxxx/" downloads
```

## Poznámky a riešenie problémov

- **Súkromné / vekovo obmedzené videá**: niektoré IG/TikTok videá vyžadujú
  prihlásenie. V takom prípade `yt-dlp` zlyhá; možno bude treba cookies
  (`--cookies-from-browser` alebo súbor cookies). Daj o tom vedieť používateľovi.
- **Rate limiting**: pri viacerých sťahovaniach za sebou môže IG/TikTok dočasne
  blokovať. Skús zopakovať neskôr.
- **Prvý frame je čierny/prázdny**: niektoré videá majú prázdny úvodný snímok.
  Vtedy možno vyextrahovať frame v čase napr. 0.1 s:
  `ffmpeg -y -ss 0.1 -i <video> -vframes 1 <out>.png`.
- Skript je idempotentný — pri opätovnom spustení s rovnakým videom prepíše výstupy.
