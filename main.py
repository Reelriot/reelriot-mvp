"""
Reel Riot MVP – publica 1 Reel al día.

Fuentes (prioridad):
1. YouTube Shorts Trending (API pública de Piped) – vertical, ≤ 60 s
2. Reddit vídeo (lista de subs). Si es imagen, genera loop MP4 de 4 s.

Secrets necesarios (GitHub Actions):
  IG_USERNAME  IG_PASSWORD  IG_SESSION
  REDDIT_CLIENT_ID  REDDIT_SECRET
"""

import os, json, random, tempfile, pathlib, subprocess, requests, praw
from instagrapi import Client
from moviepy.editor import VideoFileClip, ImageClip, AudioClip

# ──────────────── credenciales ───────────────────────────────────────────
IG_USER  = os.environ["IG_USERNAME"]
IG_PASS  = os.environ["IG_PASSWORD"]
SESSION  = os.environ["IG_SESSION"]
RID      = os.environ["REDDIT_CLIENT_ID"]
RSEC     = os.environ["REDDIT_SECRET"]

TMP = tempfile.mkdtemp()
POSTED_FILE = pathlib.Path("posted.json")
posted_ids: set[str] = set()
if POSTED_FILE.exists():
    posted_ids = set(json.loads(POSTED_FILE.read_text()))

# ──────────────── utilidades ──────────────────────────────────────────────
def verticalize(path_in: str) -> str:
    """Recorta a 9:16 si es horizontal."""
    if not path_in.endswith(".mp4"):
        return path_in
    clip = VideoFileClip(path_in)
    w, h = clip.size
    if h >= w:      # ya vertical
        return path_in
    new_h = w * 16 // 9
    clip = (clip.resize(height=new_h)
                .crop(x_center=w // 2, width=w,
                      y1=(new_h - h) // 2, y2=(new_h + h) // 2))
    out = pathlib.Path(TMP, "vertical.mp4")
    clip.write_videofile(str(out), audio_codec="aac", logger=None)
    return str(out)

def image_to_loop(img: str, seconds: int = 4) -> str:
    """Convierte imagen en vídeo loop MP4 con audio silencioso."""
    clip = ImageClip(img).set_duration(seconds).resize(height=1920)
    silent = AudioClip(lambda t: 0, duration=seconds).set_fps(44100)
    clip = clip.set_audio(silent)
    out = pathlib.Path(TMP, "loop.mp4")
    clip.write_videofile(str(out), fps=25, codec="libx264",
                         audio_codec="aac", logger=None)
    return str(out)

def mark_posted(pid: str):
    posted_ids.add(pid)
    POSTED_FILE.write_text(json.dumps(list(posted_ids)))

# ──────────────── Shorts trending via Piped ───────────────────────────────
def fetch_shorts(max_trials: int = 10) -> str | None:
    api = "https://piped.video/api/trending?region=US&category=SHORTS"
    try:
        resp = requests.get(api, timeout=20)
        entries = (resp.json() if
                   resp.headers.get("content-type","").startswith("application/json")
                   else [])
    except Exception as e:
        print("⚠️  Piped API error:", e)
        entries = []

    random.shuffle(entries)
    trials = 0
    for entry in entries:
        if trials >= max_trials:
            break
        url = entry["url"]        # /watch?v=ID
        out = pathlib.Path(TMP, "short.mp4")
        code = subprocess.run(["yt-dlp", "-q", "-o", str(out), url]).returncode
        trials += 1
        if code == 0 and out.exists():
            print("✅  Short OK:", url)
            return str(out)
    return None

# ──────────────── Reddit vídeo / imagen ───────────────────────────────────
SUBS = ("videos+Unexpected+PublicFreakout+reels+Instagramreels+"
        "TikTokCringe+dankmemes+me_irl+wholesomememes")

def fetch_reddit() -> str | None:
    reddit = praw.Reddit(client_id=RID, client_secret=RSEC,
                         user_agent="reelriot/0.7")
    hot = list(reddit.subreddit(SUBS).hot(limit=20))
    top = list(reddit.subreddit(SUBS).top(time_filter="day", limit=10))
    candidates = hot + top
    random.shuffle(candidates)

    for post in candidates:
        if post.id in posted_ids:
            continue
        url = post.url
        if post.is_video:
            url = post.media["reddit_video"]["fallback_url"]
            ext = ".mp4"
        elif url.endswith((".jpg", ".jpeg", ".png")):
            ext = "." + url.split(".")[-1].split("?")[0]
        else:
            continue

        fname = pathlib.Path(TMP, f"reddit{ext}")
        try:
            r = requests.get(url, timeout=30); r.raise_for_status()
        except Exception as e:
            print("⚠️  Reddit download fail:", e); continue

        fname.write_bytes(r.content)
        mark_posted(post.id)
        return str(fname)
    return None

# ──────────────── Selección de recurso ───────────────────────────────────
resource = fetch_shorts() or fetch_reddit()
if resource is None:
    raise RuntimeError("🔴  No Shorts ni Reddit adecuados hoy")

# imagen → loop con audio
if resource.endswith((".jpg", ".jpeg", ".png")):
    resource = image_to_loop(resource)

# recorte vertical si hace falta
resource = verticalize(resource)

# ──────────────── Publicar en Instagram ───────────────────────────────────
ig = Client()
ig.set_settings(json.loads(SESSION))
ig.login(IG_USER, IG_PASS)

CAPTION = ("🤣 Daily chaos 🚀\n"
           "➡️ Follow @reelriot.tv for more\n"
           "#funny #viral #meme #reelriot #scrolllaughrepeat #riotmemes")

ig.video_upload(resource, caption=CAPTION)
print("🎉 Publicado:", resource)
