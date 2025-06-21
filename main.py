"""
Reel Riot MVP  —  versión sin MoviePy
✓ Baja el meme top del día en Reddit
✓ Lo sube a tu Instagram
✓ Si Instagram pide verificación (challenge), usa el código guardado
"""

import os, tempfile, praw, requests
from instagrapi import Client
from instagrapi.exceptions import ChallengeRequired, ChallengeResolutionFailed

# ───── 1) Credenciales desde secrets ───────────────────────────────────────
IG_USER  = os.environ["IG_USERNAME"]
IG_PASS  = os.environ["IG_PASSWORD"]
REDDIT_ID  = os.environ["REDDIT_CLIENT_ID"]
REDDIT_SEC = os.environ["REDDIT_SECRET"]

# ───── 2) Conexión a Reddit ───────────────────────────────────────────────
reddit = praw.Reddit(
    client_id=REDDIT_ID,
    client_secret=REDDIT_SEC,
    user_agent="reelriot_mvp/0.1 by reelriottv"   # ← tu usuario Reddit
)

subs = ["dankmemes", "me_irl", "wholesomememes"]
post = next(reddit.subreddit("+".join(subs)).top(time_filter="day", limit=1))

url   = post.url
title = post.title[:2200]                         # máx. 2 200 caracteres

# ───── 3) Descarga temporal del archivo ───────────────────────────────────
with tempfile.TemporaryDirectory() as tmp:
    fname = os.path.join(tmp, url.split("/")[-1].split("?")[0])
    r = requests.get(url, timeout=20)
    r.raise_for_status()
    open(fname, "wb").write(r.content)

    # ───── 4) Login IG (con manejo de reto) ───────────────────────────────
    ig = Client()
    try:
        ig.login(IG_USER, IG_PASS)

    except ChallengeRequired:
        code = os.environ.get("IG_CHALLENGE_CODE")
        if not code:
            raise RuntimeError(
                "Instagram pide verificación. Añade el secret IG_CHALLENGE_CODE "
                "con el código de 6 dígitos y vuelve a lanzar el workflow."
            )
        try:
            # envía el código (por email o SMS) - según lo que IG haya elegido
            ig.challenge_resolve(code)
        except ChallengeResolutionFailed:
            raise RuntimeError("El código IG_CHALLENGE_CODE no funcionó. Revísalo.")

    # ───── 5) Publicación ────────────────────────────────────────────────
    if fname.lower().endswith((".jpg", ".jpeg", ".png", ".gif")):
        ig.photo_upload(path=fname, caption=title)
    else:                                         # vídeo mp4 / mov / etc.
        ig.video_upload(path=fname, caption=title)
