"""
Reel Riot MVP – login con sesión persistente
(no MoviePy)
"""

import os, json, tempfile, requests, praw
from instagrapi import Client

IG_USER   = os.environ["IG_USERNAME"]
IG_PASS   = os.environ["IG_PASSWORD"]
REDDIT_ID = os.environ["REDDIT_CLIENT_ID"]
REDDIT_SEC = os.environ["REDDIT_SECRET"]

reddit = praw.Reddit(
    client_id=REDDIT_ID,
    client_secret=REDDIT_SEC,
    user_agent="reelriot_mvp/0.1 by reelriottv"
)
post = next(reddit.subreddit("dankmemes+me_irl+wholesomememes").top("day", limit=1))
url, title = post.url, post.title[:2200]

with tempfile.TemporaryDirectory() as tmp:
    fname = os.path.join(tmp, url.split("/")[-1].split("?")[0])
    requests.get(url, timeout=20).raise_for_status()
    open(fname, "wb").write(requests.get(url, timeout=20).content)

    ig = Client()
    # ─── carga la sesión ───
    session_json = os.environ.get("IG_SESSION")
    if not session_json:
        raise RuntimeError("El secret IG_SESSION falta: pega tu ig_session.json completo.")

    ig.load_settings(json.loads(session_json))
    ig.login(IG_USER, IG_PASS)     # no pedirá códigos

    if fname.lower().endswith((".jpg", ".jpeg", ".png", ".gif")):
        ig.photo_upload(fname, caption=title)
    else:
        ig.video_upload(fname, caption=title)
