"""
Reel Riot MVP  –  login robusto
1. Si hay sesión JSON en IG_SESSION la usa.
2. Si Instagram pide challenge, resuelve con IG_CHALLENGE_CODE.
"""

import os, json, tempfile, requests, praw
from instagrapi import Client
from instagrapi.exceptions import ChallengeRequired, ChallengeResolutionFailed

# ─── secrets ───────────────────────────────────────────────────────────────
IG_USER   = os.environ["IG_USERNAME"]
IG_PASS   = os.environ["IG_PASSWORD"]
REDDIT_ID = os.environ["REDDIT_CLIENT_ID"]
REDDIT_SEC = os.environ["REDDIT_SECRET"]

# ─── Reddit ────────────────────────────────────────────────────────────────
reddit = praw.Reddit(
    client_id=REDDIT_ID,
    client_secret=REDDIT_SEC,
    user_agent="reelriot_mvp/0.1 by reelriottv"
)
post = next(reddit.subreddit("dankmemes+me_irl+wholesomememes").top("day", limit=1))
url, title = post.url, post.title[:2200]

# ─── descarga ──────────────────────────────────────────────────────────────
with tempfile.TemporaryDirectory() as tmp:
    fname = os.path.join(tmp, url.split("/")[-1].split("?")[0])
    requests.get(url, timeout=20).raise_for_status()
    open(fname, "wb").write(requests.get(url, timeout=20).content)

    ig = Client()

    # a) intenta cargar sesión si existe
    sess_json = os.environ.get("IG_SESSION")
    if sess_json:
        try:
            ig.load_settings(json.loads(sess_json))
        except json.JSONDecodeError:
            pass

    # b) login normal (puede lanzar reto)
    try:
        ig.login(IG_USER, IG_PASS)

    except ChallengeRequired:
        code = os.environ.get("IG_CHALLENGE_CODE")
        if not code:
            raise RuntimeError("Añade IG_CHALLENGE_CODE con el código de 6 dígitos.")
        try:
            ig.challenge_resolve_simple(code)
        except ChallengeResolutionFailed:
            raise RuntimeError("Código IG_CHALLENGE_CODE incorrecto o caducado.")

    # ─── publicación ───────────────────────────────────────────────────────
    if fname.lower().endswith((".jpg", ".jpeg", ".png", ".gif")):
        ig.photo_upload(fname, caption=title)
    else:
        ig.video_upload(fname, caption=title)
