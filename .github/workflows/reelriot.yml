"""
Reel Riot MVP – publica Reels diarios.
Fuentes (en orden de prioridad):
1. YouTube Shorts Trending (< 90 s)
2. Reddit (vídeo MP4). Si solo hay imagen → genera loop de 3 s.

Requisitos de entorno (secrets):
  IG_USERNAME, IG_PASSWORD, IG_SESSION,
  REDDIT_CLIENT_ID, REDDIT_SECRET
"""

import os, json, tempfile, pathlib, subprocess, requests, praw
from instagrapi import Client
from moviepy.editor import VideoFileClip, ImageClip

IG_USER   = os.environ["IG_USERNAME"]
IG_PASS   = os.environ["IG_PASSWORD"]
REDDIT_ID = os.environ["REDDIT_CLIENT_ID"]
REDDIT_SEC= os.environ["REDDIT_SECRET"]
SESSION   = os.environ["IG_SESSION"]

TMP = tempfile.mkdtemp()

# ────────────────── utilidades ───────────────────────────────────────────

def verticalize(path_in: str) -> str:
    """Garantiza que el vídeo sea 9:16; si ya lo es devuelve igual."""
    if not path_in.endswith(".mp4"):
        return path_in
    clip = VideoFileClip(path_in)
    w, h = clip.size
    if h >= w:  # vertical u horizontal rotado
        return path_in
    new_h = w * 16 // 9
    clip = (
        clip.resize(height=new_h)
            .crop(x_center=w // 2, width=w,
                  y1=(new_h - h) // 2, y2=(new_h + h) // 2)
    )
    out = pathlib.Path(TMP, "vertical.mp4")
    clip.write_videofile(str(out), audio_codec="aac", logger=None)
    return str(out)

# ────────────────── Shorts trending ──────────────────────────────────────

def fetch_shorts() -> str | None:
    jj = pathlib.Path("shorts.json")
    if not jj.exists():
        return None
    lines = [l for l in jj.read_text().splitlines() if l.strip()]
    if not lines:
        return None
    data = json.loads(lines[0])            # primer vídeo trending
    url = data.get("url")
    if not url:
        return None
    out = pathlib.Path(TMP, "shorts.mp4")
    if subprocess.run(["yt-dlp", "-o", str(out), url]).returncode != 0:
        return None
    return str(out)

# ────────────────── Reddit fallback ──────────────────────────────────────
SUBS = (
    "videos+Unexpected+PublicFreakout+reels+Instagramreels+TikTokCringe+"
    "dankmemes+me_irl+wholesomememes"
)

def fetch_reddit() -> str | None:
    reddit = praw.Reddit(
        client_id=REDDIT_ID,
        client_secret=REDDIT_SEC,
        user_agent="reelriot_mvp/0.6",
    )
    for post in reddit.subreddit(SUBS).top(time_filter="day", limit=25):
        url = post.url
        if post.is_video:
            url = post.media["reddit_video"]["fallback_url"]
            ext = ".mp4"
        else:
            if not url.lower().endswith((".jpg", ".jpeg", ".png")):
                continue
            ext = "." + url.split(".")[-1].split("?")[0]
        fname = pathlib.Path(TMP, f"reddit{ext}")
        r = requests.get(url, timeout=30)
        r.raise_for_status()
        fname.write_bytes(r.content)
        return str(fname)
    return None

# ────────────────── Preparar recurso ─────────────────────────────────────
resource = fetch_shorts() or fetch_reddit()
if resource is None:
    raise RuntimeError("No se encontró contenido en Shorts ni Reddit")

# si imagen ➜ convertir a mp4 loop 3s vertical
if resource.lower().endswith((".jpg", ".jpeg", ".png")):
    clip = ImageClip(resource).set_duration(3).resize(height=1920)
    out = pathlib.Path(TMP, "image_loop.mp4")
    clip.write_videofile(str(out), fps=24, audio=False, logger=None)
    resource = str(out)

# Asegura 9:16
resource = verticalize(resource)

# ────────────────── Publicar en Instagram ────────────────────────────────
ig = Client()
ig.set_settings(json.loads(SESSION))
ig.login(IG_USER, IG_PASS)

CAPTION = (
    "🤣 Daily chaos 🚀\n"
    "➡️ Follow @reelriot.tv for more\n"
    "#funny #viral #meme #reelriot #scrolllaughrepeat #riotmemes"
)

ig.video_upload(resource, caption=CAPTION)
print("✅ Publicado:", resource)
