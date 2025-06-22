"""
Reel Riot MVP – publica un Reel al día.

Prioridad de fuentes
====================
1. YouTube **Shorts Trending** (Top US, vía Piped API)  < 90 s.
2. Subreddits de vídeo: videos, Unexpected, PublicFreakout, reels…
   – si solo hay imagen, se crea un loop MP4 de 3 s.

Secrets requeridos en GitHub Actions
------------------------------------
IG_USERNAME  IG_PASSWORD  IG_SESSION
REDDIT_CLIENT_ID  REDDIT_SECRET
"""

import os, json, random, tempfile, pathlib, subprocess, requests, praw
from instagrapi import Client
from moviepy.editor import VideoFileClip, ImageClip

# ─────────────── CONFIG ──────────────────────────────────────────────────
IG_USER   = os.environ["IG_USERNAME"]
IG_PASS   = os.environ["IG_PASSWORD"]
IG_SESS   = os.environ["IG_SESSION"]
REDDIT_ID = os.environ["REDDIT_CLIENT_ID"]
REDDIT_SEC= os.environ["REDDIT_SECRET"]

TMP = tempfile.mkdtemp()

# ─────────────── UTIL 9:16 ───────────────────────────────────────────────

def verticalize(path_in: str) -> str:
    """Si el vídeo es horizontal, recórtalo a 9:16 (centro)."""
    if not path_in.endswith(".mp4"):
        return path_in
    clip = VideoFileClip(path_in)
    w, h = clip.size
    if h >= w:  # ya vertical
        return path_in
    new_h = w * 16 // 9
    clip = (clip.resize(height=new_h)
                .crop(x_center=w // 2, width=w,
                      y1=(new_h - h) // 2, y2=(new_h + h) // 2))
    out = pathlib.Path(TMP, "vertical.mp4")
    clip.write_videofile(str(out), audio_codec="aac", logger=None)
    return str(out)

# ─────────────── 1. YouTube Shorts via Piped ─────────────────────────────

def fetch_shorts() -> str | None:
    """Descarga el primer Short trending US (< 90 s)."""
    try:
        resp = requests.get("https://piped.video/api/trending?region=US")
        resp.raise_for_status()
        videos = resp.json()
    except Exception:
        return None
    # filtra shorts (<90 s) y con campo "url"
    shorts = [v for v in videos if v.get("duration", 10_000) < 90 and v.get("short", False)]
    if not shorts:
        return None
    vid = random.choice(shorts)  # algo de variedad
    url = "https://www.youtube.com" + vid["url"]
    out = pathlib.Path(TMP, "short.mp4")
    if subprocess.run(["yt-dlp", "-o", str(out), url]).returncode == 0 and out.exists():
        return str(out)
    return None

# ─────────────── 2. Reddit vídeo o imagen ───────────────────────────────
SUBS = (
    "videos+Unexpected+PublicFreakout+reels+Instagramreels+TikTokCringe+"
    "dankmemes+me_irl+wholesomememes"
)

def fetch_reddit() -> str | None:
    reddit = praw.Reddit(
        client_id=REDDIT_ID,
        client_secret=REDDIT_SEC,
        user_agent="reelriot_mvp/shorts",
    )
    for post in reddit.subreddit(SUBS).top(time_filter="day", limit=25):
        url = post.media["reddit_video"]["fallback_url"] if post.is_video else post.url
        ext = ".mp4" if post.is_video else os.path.splitext(url.split("?")[0])[1]
        if ext.lower() not in {".mp4", ".jpg", ".jpeg", ".png"}:
            continue
        fname = pathlib.Path(TMP, f"reddit{ext}")
        try:
            r = requests.get(url, timeout=30); r.raise_for_status()
            fname.write_bytes(r.content)
            return str(fname)
        except Exception:
            continue
    return None

# ─────────────── 3. Selecciona recurso ──────────────────────────────────
resource = fetch_shorts() or fetch_reddit()
if resource is None:
    raise RuntimeError("Sin vídeos: Shorts y Reddit fallaron")

# Si es imagen → haz loop 3 s en MP4
autoloop = False
if resource.lower().endswith((".jpg", ".jpeg", ".png")):
    clip = ImageClip(resource).set_duration(3).resize(height=1920)
    out = pathlib.Path(TMP, "loop.mp4")
    clip.write_videofile(str(out), fps=24, audio=False, logger=None)
    resource, autoloop = str(out), True

# recorte vertical si procede
resource = verticalize(resource)

# ─────────────── 4. Login IG y subir ─────────────────────────────────────
ig = Client(); ig.set_settings(json.loads(IG_SESS)); ig.login(IG_USER, IG_PASS)

CAPTION = (
    "🤣 Daily chaos 🚀\n"
    "➡️ Follow @reelriot.tv for more\n"
    "#funny #viral #meme #reelriot #scrolllaughrepeat #riotmemes"
)

ig.video_upload(resource, caption=CAPTION)
print("✅ Publicado:", pathlib.Path(resource).name, "(loop)" if autoloop else "")
