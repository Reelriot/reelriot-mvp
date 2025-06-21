main.py

"""
Reel Riot MVP
Descarga el meme top del día y lo sube a tu Instagram.
"""

import os, tempfile, praw, requests
from instagrapi import Client
from moviepy.editor import VideoFileClip

# --- 1) Credenciales guardadas en Railway ----------------------------------
IG_USER  = os.environ["IG_USERNAME"]
IG_PASS  = os.environ["IG_PASSWORD"]
REDDIT_ID  = os.environ["REDDIT_CLIENT_ID"]
REDDIT_SEC = os.environ["REDDIT_SECRET"]

# --- 2) Conexión a Reddit ---------------------------------------------------
reddit = praw.Reddit(
    client_id=REDDIT_ID,
    client_secret=REDDIT_SEC,
    # 👉 SUSTITUYE “reelriottv” POR TU USUARIO DE REDDIT
    user_agent="reelriot_mvp/0.1 by reelriottv"
)

# Elegimos subreddits y cogemos el #1 del día
subs = ["dankmemes", "me_irl", "wholesomememes"]
post = next(reddit.subreddit("+".join(subs)).top(time_filter="day", limit=1))

url   = post.url
title = post.title[:2200]          # límite de caracteres IG

# --- 3) Descarga del archivo ------------------------------------------------
with tempfile.TemporaryDirectory() as tmp:
    fname = os.path.join(tmp, url.split("/")[-1].split("?")[0])
    r = requests.get(url, timeout=20)
    open(fname, "wb").write(r.content)

    # Si es vídeo horizontal ⇒ reencuadra vertical 9:16
    if fname.lower().endswith((".mp4", ".mov")):
        clip = VideoFileClip(fname)
        w, h = clip.size
        if h < w:                  # detecta horizontal
            new_h = w * 16 // 9
            clip = (clip
                    .resize(height=new_h)
                    .crop(x_center=w//2, width=w,
                          y1=(new_h-h)//2, y2=(new_h+h)//2))
        out = fname.replace(".", "_9x16.")
        clip.write_videofile(out, audio_codec="aac", logger=None)
        fname = out

    # --- 4) Login IG y publicación -----------------------------------------
    ig = Client()
    ig.login(IG_USER, IG_PASS)
    if fname.lower().endswith((".jpg", ".jpeg", ".png")):
        ig.photo_upload(path=fname, caption=title)
    else:
        ig.video_upload(path=fname, caption=title)
