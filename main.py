"""
Reel Riot MVP – ahora con TikTok trending
"""

import os, json, tempfile, pathlib, subprocess, requests, praw
from instagrapi import Client
from moviepy.editor import VideoFileClip  # recorte vertical (opcional)

# ─── secrets ───────────────────────────────────────────────────────────────
IG_USER   = os.environ["IG_USERNAME"]
IG_PASS   = os.environ["IG_PASSWORD"]
REDDIT_ID = os.environ["REDDIT_CLIENT_ID"]
REDDIT_SEC = os.environ["REDDIT_SECRET"]
SESSION   = os.environ["IG_SESSION"]

TMP = tempfile.mkdtemp()

# ─── helper: recorte 9:16 si es horizontal ────────────────────────────────
def verticalize(path_in):
    clip = VideoFileClip(path_in)
    w, h = clip.size
    if h >= w:
        return path_in  # ya es vertical
    new_h = w * 16 // 9
    clip = (clip.resize(height=new_h)
                .crop(x_center=w//2, width=w,
                      y1=(new_h-h)//2, y2=(new_h+h)//2))
    out = path_in.replace(".mp4", "_9x16.mp4")
    clip.write_videofile(out, audio_codec="aac", logger=None)
    return out

# ─── 1.  TikTok trending JSON (si existe) ──────────────────────────────────
def fetch_tiktok():
    tt_json = pathlib.Path("tiktok.json")
    if not tt_json.exists():
        return None
    data = [json.loads(line) for line in tt_json.read_text().splitlines()]
    # ordena por like_count (digg_count) descendente
    data.sort(key=lambda d: d.get("digg_count", 0), reverse=True)
    if not data:
        return None
    url = data[0]["download_addr"] or data[0]["url"]
    out = pathlib.Path(TMP, "tiktok.mp4")
    subprocess.run(["yt-dlp", "-o", out, url], check=True)
    return str(out)

# ─── 2.  Reddit fallback (lo que ya tenías) ───────────────────────────────
def fetch_reddit():
    reddit = praw.Reddit(
        client_id=REDDIT_ID,
        client_secret=REDDIT_SEC,
        user_agent="reelriot_mvp/0.2"
    )
    post = next(reddit.subreddit("dankmemes+me_irl+wholesomememes")
                      .top(time_filter="day", limit=1))
    r = requests.get(post.url, timeout=20); r.raise_for_status()
    ext = post.url.split(".")[-1].split("?")[0]
    fname = pathlib.Path(TMP, f"reddit.{ext}")
    fname.write_bytes(r.content)
    return str(fname)

# ─── 3.  Decide la fuente ─────────────────────────────────────────────────
clip_path = fetch_tiktok() or fetch_reddit()
clip_path = verticalize(clip_path)

# ─── 4.  Login IG y publicar ──────────────────────────────────────────────
ig = Client()
ig.set_settings(json.loads(SESSION))
ig.login(IG_USER, IG_PASS)

CAPTION = ("🤣 Daily chaos 🚀\n"
           "➡️ Follow @reelriot.tv for more\n"
           "#funny #viral #meme #reelriot #scrolllaughrepeat #riotmemes")

ig.video_upload(clip_path, caption=CAPTION)
