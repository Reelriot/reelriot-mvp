"""
Reel Riot MVP — login robusto con IG_SESSION y código 6 dígitos
Versión sin MoviePy
"""

import os, json, tempfile, requests, praw
from instagrapi import Client
from instagrapi.exceptions import ChallengeRequired   # <- solo esta

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
    r = requests.get(url, timeout=20); r.raise_for_status()
    open(fname, "wb").write(r.content)

    ig = Client()

    # a) carga sesión JSON si existe
    sess_json = os.environ.get("IG_SESSION")
    if sess_json:
        try:
            ig.load_settings(json.loads(sess_json))
        except json.JSONDecodeError:
            pass

    # b) login (puede disparar reto)
    try:
        ig.login(IG_USER, IG_PASS)

    except ChallengeRequired:
        code = os.environ.get("IG_CHALLENGE_CODE")
        if not code:
            raise RuntimeError(
                "Instagram pide verificación. Añade el secret IG_CHALLENGE_CODE "
                "con el código de 6 dígitos y re-ejecuta el workflow."
            )
        # intenta resolver con el código
        if not ig.challenge_resolve_simple(code):
            raise RuntimeError("El código IG_CHALLENGE_CODE es incorrecto o caducó.")

    # ─── publicación ───────────────────────────────────────────────────────
