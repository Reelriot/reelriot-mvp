"""
Reel Riot MVP – sube Reel si es vídeo, foto si es imagen
"""

import os, json, tempfile, pathlib, subprocess, requests, praw
from instagrapi import Client
from moviepy.editor import VideoFileClip

IG_USER   = os.environ["IG_USERNAME"]
IG_PASS   = os.environ["IG_PASSWORD"]
REDDIT_ID = os.environ["REDDIT_CLIENT_ID"]
REDDIT_SEC= os.environ["REDDIT_SECRET"]
SESSION   = os.environ["IG_SESSION"]

TMP = tempfile.mkdtemp()

# ─── recorte a 9:16 si es horizontal ──────────────────────────────────────
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
    out = path_in.replace(".mp4", "_9x16.mp4")
    clip.write_videofile(out, audio_codec="aac", logger=None)
    return out

# ─── 1.  TikTok (si existe tiktok.json) ───────────────────────────────────
def fetch_tiktok():
    jj = pathlib.Path("tiktok.json")
    if not jj.exists():
        return None
    data = [json.loads(l) for l in jj.read_text().splitlines() if l.strip()]
    if not data:
        return None
    # yt-dlp flat playlist → entries con 'url'
    url = data[0]["url"]
    out = pathlib.Path(TMP, "tiktok.mp4")
    subprocess.run(["yt-dlp", "-o", out, url], check=True)
    return str(out)

# ─── 2.  Reddit vídeo fallback ────────────────────────────────────────────
def fetch_reddit():
    reddit = praw.Reddit(client_id=REDDIT_ID,
                         client_secret=REDDIT_SEC,
                         user_agent="reelriot_mvp/0.3")
    for post in reddit.subreddit(
        "dankmemes+me_irl+wholesomememes").top(time_filter="day", limit=10):
        if post.is_video:
            url = post.media["reddit_video"]["fallback_url"]
            fname = pathlib.Path(TMP, "reddit.mp4")
            r = requests.get(url, timeout=30); r.raise_for_status()
            fname.write_bytes(r.content)
            return str(fname)
    return None

# ─── 3.  Decide fuente ────────────────────────────────────────────────────
clip = fetch_tiktok() or fetch_reddit()
if clip is None:
    raise RuntimeError("No se encontró vídeo ni en TikTok ni en Reddit")

clip = verticalize(clip)

# ─── 4.  Login IG y publicar ──────────────────────────────────────────────
ig = Client(); ig.set_settings(json.loads(SESSION)); ig.login(IG_USER, IG_PASS)

CAPTION = ("🤣 Daily chaos 🚀\n"
           "➡️ Follow @reelriot.tv for more\n"
           "#funny #viral #meme #reelriot #scrolllaughrepeat #riotmemes")

if clip.endswith(".mp4"):
    ig.video_upload(clip, caption=CAPTION)
else:
    ig.photo_upload(clip, caption=CAPTION)
