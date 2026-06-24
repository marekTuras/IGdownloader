"""
IG/TikTok downloader + first-frame API.

Stiahne Instagram/TikTok video cez yt-dlp a vyextrahuje SKUTOČNÝ prvý snímok
(frame 0) cez ffmpeg. Určené ako backend pre iOS Skratku (Shortcut).

Endpointy:
  GET  /health                  -> {"status": "ok"}
  POST /process   {url}         -> {"id", "video_url", "frame_url"}
  GET  /files/{name}            -> servuje stiahnuté video / frame

Bezpečnosť:
  - Povolené sú len instagram.com / tiktok.com odkazy (proti zneužitiu/SSRF).
  - Voliteľný token cez env API_TOKEN: klient posiela hlavičku  X-API-Token.
"""
import os
import re
import shutil
import subprocess
import time
from pathlib import Path
from urllib.parse import urlparse

from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

# --- Konfigurácia -----------------------------------------------------------
DATA_DIR = Path(os.environ.get("DATA_DIR", "/tmp/igdownloader")).resolve()
DATA_DIR.mkdir(parents=True, exist_ok=True)
API_TOKEN = os.environ.get("API_TOKEN")  # ak je nastavený, vyžaduje sa
BASE_URL = os.environ.get("BASE_URL", "").rstrip("/")  # napr. https://moj-server.app
FILE_TTL_SECONDS = int(os.environ.get("FILE_TTL_SECONDS", "3600"))  # upratovanie

ALLOWED_HOSTS = (
    "instagram.com",
    "instagr.am",
    "tiktok.com",
    "vm.tiktok.com",
    "vt.tiktok.com",
)

app = FastAPI(title="IG/TikTok downloader + first frame")


class ProcessRequest(BaseModel):
    url: str


def _check_token(token: str | None) -> None:
    if API_TOKEN and token != API_TOKEN:
        raise HTTPException(status_code=401, detail="Neplatný alebo chýbajúci API token.")


def _validate_url(url: str) -> None:
    try:
        host = (urlparse(url).hostname or "").lower()
    except Exception:
        raise HTTPException(status_code=400, detail="Neplatná URL.")
    if not host:
        raise HTTPException(status_code=400, detail="Neplatná URL.")
    host = host[4:] if host.startswith("www.") else host
    if not any(host == h or host.endswith("." + h) or host == h for h in ALLOWED_HOSTS):
        raise HTTPException(
            status_code=400,
            detail="Povolené sú len Instagram a TikTok odkazy.",
        )


def _cleanup_old_files() -> None:
    """Zmaže súbory staršie ako TTL, aby disk nerástol donekonečna."""
    now = time.time()
    for p in DATA_DIR.iterdir():
        try:
            if p.is_file() and now - p.stat().st_mtime > FILE_TTL_SECONDS:
                p.unlink()
        except OSError:
            pass


def _run(cmd: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True)


def _download_video(url: str) -> Path:
    """Stiahne video cez yt-dlp, vráti cestu k mp4."""
    out_template = str(DATA_DIR / "%(id)s.%(ext)s")
    cmd = [
        "yt-dlp",
        "--no-playlist",
        "--no-warnings",
        "--restrict-filenames",
        "-f", "mp4/bestvideo*+bestaudio/best",
        "--merge-output-format", "mp4",
        "-o", out_template,
        "--print", "after_move:filepath",
        url,
    ]
    proc = _run(cmd)
    if proc.returncode != 0:
        raise HTTPException(
            status_code=502,
            detail=f"Stiahnutie zlyhalo: {proc.stderr.strip()[-400:] or 'neznáma chyba'}",
        )
    path = proc.stdout.strip().splitlines()[-1].strip() if proc.stdout.strip() else ""
    video = Path(path) if path else None
    if not video or not video.exists():
        # fallback: najnovší mp4 v priečinku
        mp4s = sorted(DATA_DIR.glob("*.mp4"), key=lambda p: p.stat().st_mtime, reverse=True)
        video = mp4s[0] if mp4s else None
    if not video or not video.exists():
        raise HTTPException(status_code=502, detail="Stiahnuté video sa nenašlo.")
    return video


def _extract_first_frame(video: Path) -> Path:
    """Vyextrahuje SKUTOČNÝ prvý snímok (frame 0) cez ffmpeg."""
    frame = video.with_suffix("")
    frame = frame.parent / (frame.name + ".first.png")
    cmd = [
        "ffmpeg", "-y", "-loglevel", "error",
        "-i", str(video),
        "-vf", r"select=eq(n\,0)",
        "-vframes", "1",
        str(frame),
    ]
    proc = _run(cmd)
    if proc.returncode != 0 or not frame.exists():
        raise HTTPException(
            status_code=500,
            detail=f"Extrakcia prvého snímku zlyhala: {proc.stderr.strip()[-300:]}",
        )
    return frame


def _file_url(name: str) -> str:
    return f"{BASE_URL}/files/{name}" if BASE_URL else f"/files/{name}"


@app.get("/health")
def health():
    return {
        "status": "ok",
        "yt_dlp": shutil.which("yt-dlp") is not None,
        "ffmpeg": shutil.which("ffmpeg") is not None,
    }


@app.post("/process")
def process(req: ProcessRequest, x_api_token: str | None = Header(default=None)):
    _check_token(x_api_token)
    _validate_url(req.url)
    _cleanup_old_files()

    video = _download_video(req.url)
    frame = _extract_first_frame(video)

    return {
        "id": video.stem,
        "video_url": _file_url(video.name),
        "frame_url": _file_url(frame.name),
    }


@app.get("/files/{name}")
def get_file(name: str):
    # zamedzí path traversal
    if "/" in name or ".." in name or name.startswith("."):
        raise HTTPException(status_code=400, detail="Neplatný názov súboru.")
    path = (DATA_DIR / name).resolve()
    if not str(path).startswith(str(DATA_DIR)) or not path.is_file():
        raise HTTPException(status_code=404, detail="Súbor sa nenašiel.")
    media = "video/mp4" if path.suffix == ".mp4" else "image/png"
    return FileResponse(path, media_type=media, filename=path.name)
