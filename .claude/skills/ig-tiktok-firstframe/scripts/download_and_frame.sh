#!/usr/bin/env bash
#
# download_and_frame.sh — stiahne IG/TikTok video a vygeneruje jeho prvý frame.
#
# Použitie:
#   download_and_frame.sh <URL> [OUTPUT_DIR]
#
# - <URL>        : odkaz na Instagram alebo TikTok video (reel, post, video)
# - [OUTPUT_DIR] : voliteľný cieľový priečinok (default: ./downloads)
#
# Výstup (do OUTPUT_DIR):
#   <id>.<ext>        — stiahnuté video
#   <id>.first.png    — prvý frame videa
#
set -euo pipefail

URL="${1:-}"
OUT_DIR="${2:-downloads}"

if [[ -z "$URL" ]]; then
  echo "CHYBA: chýba URL." >&2
  echo "Použitie: download_and_frame.sh <URL> [OUTPUT_DIR]" >&2
  exit 2
fi

# --- Závislosti -------------------------------------------------------------
ensure_deps() {
  if ! command -v yt-dlp >/dev/null 2>&1; then
    echo ">> Inštalujem yt-dlp..." >&2
    pip3 install --quiet --upgrade yt-dlp >&2
  fi
  if ! command -v ffmpeg >/dev/null 2>&1; then
    echo ">> Inštalujem ffmpeg..." >&2
    if command -v apt-get >/dev/null 2>&1; then
      apt-get update -qq >&2 || true
      apt-get install -y -qq ffmpeg >&2
    else
      echo "CHYBA: ffmpeg nie je nainštalovaný a apt-get nie je dostupný." >&2
      exit 1
    fi
  fi
}

ensure_deps

mkdir -p "$OUT_DIR"

# --- Stiahnutie videa -------------------------------------------------------
# %(id)s zabezpečí stabilný, jedinečný názov súboru.
echo ">> Sťahujem video: $URL" >&2
yt-dlp \
  --no-playlist \
  --no-warnings \
  --restrict-filenames \
  -f "mp4/bestvideo*+bestaudio/best" \
  --merge-output-format mp4 \
  -o "${OUT_DIR}/%(id)s.%(ext)s" \
  "$URL" >&2

# Nájdeme práve stiahnutý súbor (najnovší video súbor v priečinku).
VIDEO_FILE="$(yt-dlp --no-playlist --no-warnings --restrict-filenames \
  -f "mp4/bestvideo*+bestaudio/best" --merge-output-format mp4 \
  -o "${OUT_DIR}/%(id)s.%(ext)s" --print filename --no-download "$URL" 2>/dev/null || true)"

# Fallback: ak --print zlyhá, vezmeme najnovší súbor v priečinku.
if [[ -z "${VIDEO_FILE:-}" || ! -f "$VIDEO_FILE" ]]; then
  VIDEO_FILE="$(ls -t "${OUT_DIR}"/*.* 2>/dev/null | grep -viE '\.first\.png$' | head -n1 || true)"
fi

if [[ -z "${VIDEO_FILE:-}" || ! -f "$VIDEO_FILE" ]]; then
  echo "CHYBA: stiahnuté video sa nepodarilo nájsť." >&2
  exit 1
fi

echo ">> Video uložené: $VIDEO_FILE" >&2

# --- Prvý frame -------------------------------------------------------------
BASE="${VIDEO_FILE%.*}"
FRAME_FILE="${BASE}.first.png"

echo ">> Generujem prvý frame..." >&2
ffmpeg -y -loglevel error -i "$VIDEO_FILE" -vf "select=eq(n\,0)" -vframes 1 "$FRAME_FILE"

if [[ ! -f "$FRAME_FILE" ]]; then
  echo "CHYBA: prvý frame sa nepodarilo vygenerovať." >&2
  exit 1
fi

echo ">> Prvý frame uložený: $FRAME_FILE" >&2

# Strojovo čitateľný výstup na stdout (posledné dva riadky).
echo "VIDEO=$VIDEO_FILE"
echo "FRAME=$FRAME_FILE"
