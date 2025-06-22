"""
Reel Riot MVP – sesión persistente (sin MoviePy)
"""

import os, json, tempfile, requests, praw
from instagrapi import Client

IG_USER   = os.environ["IG_USERNAME"]
IG_PASS   = os.environ["IG_PASSWORD"]
REDDIT_ID = os.environ["REDDIT_CLIENT_ID"]
REDDIT_SEC = os.environ["REDDIT_SECRET"]

# 1· Reddit: top del día
reddit = praw.Reddit(
    client_id=REDDIT_ID,
    client_secret=REDDIT_SEC,
    user_agent="reelriot_mvp/0.1 by reelriottv"
)
post = next(reddit.subreddit("dankmemes+me_irl+wholesomememes").top(time_filter="day", limit=1))
url, title = post.url, post.title[:2200]

# 2· Descarga
with tempfile.TemporaryDirectory() as tmp:
    fname = os.path.join(tmp, url.split("/")[-1].split("?")[0])
    requests.get(url, timeout=20).raise_for_status()
    open(fname, "wb").write(requests.get(url, timeout=20).content)

    # 3· Instagram con sesión guardada
    ig = Client()
    session_json = os.environ.get("IG_SESSION")
    if not session_json:
        raise RuntimeError("Falta el secret IG_SESSION con tu ig_session.json")

    ig.set_settings(json.loads(session_json))   # ← usa set_settings, no load_settings


    ig.load_settings(json.loads(session_json))
    ig.login(IG_USER, IG_PASS)           # ya no dispara retos

    # 4· Publicar
    if fname.lower().endswith((".jpg", ".jpeg", ".png", ".gif")):
        ig.photo_upload(fname, caption=title)
    else:
        ig.video_upload(fname, caption=title)
