# IGdownloader

Claude Code skill na stiahnutie **Instagram / TikTok** videa z odkazu
a vygenerovanie jeho **prvého frame** (first frame) ako PNG.

## Použitie cez Claude Code

Pošli Claudovi odkaz na IG/TikTok video a požiadaj o stiahnutie + prvý frame.
Claude automaticky spustí skill `ig-tiktok-firstframe`.

## Použitie priamo cez skript

```bash
bash .claude/skills/ig-tiktok-firstframe/scripts/download_and_frame.sh "<URL>" [OUTPUT_DIR]
```

- `<URL>` — odkaz na Instagram alebo TikTok video.
- `[OUTPUT_DIR]` — voliteľný cieľový priečinok (default `downloads`).

Výstup:
- `<id>.mp4` — stiahnuté video
- `<id>.first.png` — prvý frame videa

## Závislosti

- [`yt-dlp`](https://github.com/yt-dlp/yt-dlp) — sťahovanie videa
- [`ffmpeg`](https://ffmpeg.org/) — extrakcia prvého frame

Skript ich v prípade potreby doinštaluje automaticky (`pip3` / `apt-get`).

## Poznámka k sieti

Sťahovanie vyžaduje prístup k doménam `instagram.com` / `tiktok.com`.
V niektorých prostrediach (napr. obmedzená egress policy) môžu byť tieto
domény blokované — vtedy spusti skill v prostredí s prístupom na internet.
