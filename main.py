"""
Reel Riot – vídeo primero; si no hay, convierte imagen a Reel loop 3 s
"""

import os, json, tempfile, pathlib, subprocess, requests, praw
from instagrapi import Client
from moviepy.editor import VideoFileClip, ImageClip

IG_USER = os.environ["IG_USERNAME"]
IG_PASS = os.environ["IG_PASSWORD"]
REDDIT_ID = os.environ["REDDIT_CLIENT_ID"]
REDDIT_SEC= os.environ["REDDIT_SECRET"]
SESSION  = os.environ["IG_SESSION"]

TMP = tempfile.mkdtemp()

# ─── helper verticalize ────────────────────────────────────────────────────
def verticalize(path_in):
    if not path_in.endswith(".mp4"):
        return path_in
    clip = VideoFileClip(path_in)
    w, h = clip.size
    if h >= w:
        return path_in
    new_h = w * 16 // 9
    clip = (clip.resize(height=new_h)
                .crop(x_center=w//2, width=w,
                      y1=(new_h-h)//2, y2=(new_h+h)//2))
    out = pathlib.Path(TMP, "vertical.mp4")
    clip.write_videofile(str(out), audio_codec="aac", logger=None)   # ← str()
    return str(out)                                                  # ← str()

# ─── TikTok (opcional) ────────────────────────────────────────────────────
def fetch_tiktok():
    jj = pathlib.Path("tiktok.json")
    if not jj.exists():
        return None
    data = [json.loads(l) for l in jj.read_text().splitlines() if l.strip()]
    if not data:
        return None
    url = data[0]["url"]
    out = pathlib.Path(TMP, "tiktok.mp4")
    if subprocess.run(["yt-dlp", "-o", str(out), url]).returncode != 0:  # ← str()
        return None
    return str(out)

# ─── Reddit vídeo o imagen ────────────────────────────────────────────────
SUBS = "videos+Unexpected+PublicFreakout+reels+Instagramreels+TikTokCringe+dankmemes+me_irl+wholesomememes"

def fetch_reddit():
    reddit = praw.Reddit(client_id=REDDIT_ID,
                         client_secret=REDDIT_SEC,
                         user_agent="reelriot_mvp/0.5")
    for post in reddit.subreddit(SUBS).top(time_filter="day", limit=20):
        url = post.url
        if post.is_video:
            url = post.media["reddit_video"]["fallback_url"]
            ext = ".mp4"
        else:
            if not url.endswith((".jpg", ".jpeg", ".png")):
                continue
            ext = "." + url.split(".")[-1].split("?")[0]
        fname = pathlib.Path(TMP, f"reddit{ext}")
        r = requests.get(url, timeout=30); r.raise_for_status()
        fname.write_bytes(r.content)
        return str(fname)
    return None

# ─── 1. decide recurso ────────────────────────────────────────────────────
resource = fetch_tiktok() or fetch_reddit()
if resource is None:
    raise RuntimeError("No se encontró contenido (TikTok y Reddit vacíos)")

# ─── 2. si es imagen, loop 3 s mp4 ────────────────────────────────────────
if resource.endswith((".jpg", ".jpeg", ".png")):
    clip = ImageClip(resource).set_duration(3).resize(height=1920)
    out = pathlib.Path(TMP, "image_loop.mp4")
    clip.write_videofile(str(out), fps=24, audio=False, logger=None)   # ← str()
    resource = str(out)

# ─── 3. recorte vertical si necesita ──────────────────────────────────────
resource = verticalize(resource)

# ─── 4. login IG y subir ──────────────────────────────────────────────────
ig = Client(); ig.set_settings(json.loads(SESSION)); ig.login(IG_USER, IG_PASS)

CAPTION = ("🤣 Daily chaos 🚀\n"
           "➡️ Follow @reelriot.tv for more\n"
           "#funny #viral #meme #reelriot #scrolllaughrepeat #riotmemes")

ig.video_upload(resource, caption=CAPTION)
print("✅ Publicado:", resource)
