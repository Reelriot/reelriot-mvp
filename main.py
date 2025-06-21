"""
Reel Riot MVP — main.py definitivo
Versión mínima viable (sin MoviePy) con sesión persistente de Instagram.

Flujo:
1. Toma el top-day de 3 subreddits.
2. Descarga la imagen o vídeo.
3. Carga la sesión guardada en el secret IG_SESSION para evitar retos.
4. Publica el meme en tu cuenta de Instagram.
"""

import os
import json
import tempfile
import requests
import praw
from instagrapi import Client

# ───── 1. Credenciales desde secrets ───────────────────────────────────────
IG_USER   = os.environ["IG_USERNAME"]        # tu usuario IG (sin @)
IG_PASS   = os.environ["IG_PASSWORD"]        # tu contraseña IG
REDDIT_ID = os.environ["REDDIT_CLIENT_ID"]   # client_id de la app Reddit
REDDIT_SEC = os.environ["REDDIT_SECRET"]     # secret de la app Reddit

# ───── 2. Conexión a Reddit ───────────────────────────────────────────────
reddit = praw.Reddit(
    client_id=REDDIT_ID,
    client_secret=REDDIT_SEC,
    user_agent="reelriot_mvp/0.1 by reelriottv"   # ← cambia si tu user Reddit es otro
)

subreddits = ["dankmemes", "me_irl", "wholesomememes"]
post = next(reddit.subreddit("+".join(subreddits)).top(time_filter="day", limit=1))

url   = post.url
title = post.title[:2200]                      # máximo permitido por IG

# ───── 3. Descarga temporal del archivo ───────────────────────────────────
with tempfile.TemporaryDirectory() as tmpdir:
    fname = os.path.join(tmpdir, url.split("/")[-1].split("?")[0])
    r = requests.get(url, timeout=20)
    r.raise_for_status()
    open(fname, "wb").write(r.content)

    # ───── 4. Login IG con sesión persistente ─────────────────────────────
    ig = Client()

    session_json = os.environ.get("IG_SESSION")  # secret con el JSON de sesión
    if session_json:
        try:
            ig.load_settings(json.loads(session_json))
        except json.JSONDecodeError:
            # Si el JSON está mal formateado, continúa sin él
            pass

    # Intenta iniciar sesión; si la sesión es válida, no habrá retos
    ig.login(IG_USER, IG_PASS)

    # ───── 5. Publicación ────────────────────────────────────────────────
    if fname.lower().endswith((".jpg", ".jpeg", ".png", ".gif")):
        ig.photo_upload(fname, caption=title)
    else:                                       # vídeo mp4 / mov / etc.
        ig.video_upload(fname, caption=title)
