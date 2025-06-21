"""
Reel Riot MVP  —  versión sin MoviePy
Descarga el meme top del día y lo sube a tu Instagram.
Nota: los vídeos horizontales se subirán tal cual (sin recorte 9:16).
"""

import os, tempfile, praw, requests
from instagrapi import Client

# ───── 1) Credenciales guardadas como secrets ──────────────────────────────
IG_USER  = os.environ["IG_USERNAME"]
IG_PASS  = os.environ["IG_PASSWORD"]
REDDIT_ID  = os.environ["REDDIT_CLIENT_ID"]
REDDIT_SEC = os.environ["REDDIT_SECRET"]

# ───── 2) Conexión a Reddit ───────────────────────────────────────────────
reddit = praw.Reddit(
    client_id=REDDIT_ID,
    client_secret=REDDIT_SEC,
    user_agent="reelriot_mvp/0.1 by reelriottv"      # ← pon tu usuario de Reddit
)

subs = ["dankmemes", "me_irl", "wholesomememes"]
post = next(reddit.subreddit("+".join(subs)).top(time_filter="day", limit=1))

url   = post.url
title = post.title[:2200]                            # máx. 2 200 caracteres

# ───── 3) Descarga temporal del archivo ───────────────────────────────────
with tempfile.TemporaryDirectory() as tmp:
    fname = os.path.join(tmp, url.split("/")[-1].split("?")[0])
    r = requests.get(url, timeout=20)
    r.raise_for_status()
    open(fname, "wb").write(r.content)

    # ───── 4) Login IG y publicación ──────────────────────────────────────
    ig = Client()
    ig.login(IG_USER, IG_PASS)

    if fname.lower().endswith((".jpg", ".jpeg", ".png", ".gif")):
        ig.photo_upload(path=fname, caption=title)
    else:                                             # mp4 / mov / etc.
        ig.video_upload(path=fname, caption=title)
