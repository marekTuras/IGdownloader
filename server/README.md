# 🖥️ Backend API — download + skutočný prvý frame

Malý web server, ktorý stiahne IG/TikTok video (`yt-dlp`) a vyextrahuje
**reálny prvý snímok videa — frame 0** (`ffmpeg`). Slúži ako backend pre
iOS Skratku, aby aj na mobile vznikal **presný** prvý frame (nie cover).

## Endpointy

| Metóda | Cesta            | Popis                                                        |
|--------|------------------|--------------------------------------------------------------|
| GET    | `/health`        | stav servera + dostupnosť yt-dlp/ffmpeg                       |
| POST   | `/process`       | telo `{"url": "..."}` → `{"id","video_url","frame_url"}`      |
| GET    | `/files/{name}`  | servuje stiahnuté video (.mp4) alebo prvý frame (.first.png)  |

Príklad:

```bash
curl -X POST https://TVOJ-SERVER/process \
  -H 'Content-Type: application/json' \
  -d '{"url":"https://www.instagram.com/reel/Cxxxxxxxxxx/"}'
# -> {"id":"Cxxxx","video_url":"https://TVOJ-SERVER/files/Cxxxx.mp4",
#     "frame_url":"https://TVOJ-SERVER/files/Cxxxx.first.png"}
```

## Konfigurácia (env premenné)

| Premenná           | Default            | Popis                                                  |
|--------------------|--------------------|--------------------------------------------------------|
| `BASE_URL`         | *(prázdne)*        | verejná URL servera; vloží sa do `video_url`/`frame_url`. Nastav na napr. `https://moj-server.app`. |
| `API_TOKEN`        | *(prázdne)*        | ak je nastavený, klient musí poslať hlavičku `X-API-Token`. **Odporúčané**, nech ti server nikto nezneužije. |
| `DATA_DIR`         | `/tmp/igdownloader`| kam sa ukladajú súbory (v Dockeri `/data`).            |
| `FILE_TTL_SECONDS` | `3600`             | po akom čase sa staré súbory zmažú.                    |
| `PORT`             | `8000`             | port (Render/Railway/Fly ho nastavujú automaticky).    |

> **Bezpečnosť:** server prijíma len `instagram.com` / `tiktok.com` odkazy
> (ochrana proti SSRF). Pri verejnom nasadení **vždy nastav `API_TOKEN`**.

## Lokálne spustenie

```bash
cd server
pip install -r requirements.txt        # + ffmpeg v systéme (apt install ffmpeg)
export BASE_URL=http://127.0.0.1:8000
uvicorn app:app --host 0.0.0.0 --port 8000
```

## Docker

```bash
cd server
docker build -t igdownloader .
docker run -p 8000:8000 \
  -e BASE_URL=https://moj-server.app \
  -e API_TOKEN=tajny-token \
  igdownloader
```

## Nasadenie na internet (aby to šlo z iPhone)

Server potrebuje **otvorený prístup na instagram.com/tiktok.com** a verejnú HTTPS
URL. Možnosti:

- **Render / Railway / Fly.io** — nahraj repo, použijú `server/Dockerfile`.
  Nastav env `BASE_URL` (na pridelenú doménu) a `API_TOKEN`.
- **Vlastný VPS** (napr. Hetzner, DigitalOcean): `docker run ...` + reverzná proxy
  (Caddy/Nginx) s HTTPS.
- **Domáci server** + Cloudflare Tunnel / Tailscale Funnel pre verejnú HTTPS URL.

Po nasadení over: `curl https://TVOJ-SERVER/health` → `{"status":"ok", ...}`.

Ďalej nakonfiguruj iOS Skratku podľa
[`../mobile/ios-shortcut/NAVOD.md`](../mobile/ios-shortcut/NAVOD.md) (sekcia
„Verzia so serverom — skutočný prvý frame").
