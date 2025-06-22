"""
Reel Riot MVP   ·   Publica 1 Reel al día.

Prioridad de fuentes
--------------------
1. YouTube Shorts Trending (API pública de Piped) · vertical, ≤ 60 s
2. Reddit vídeo (varios subs).  Si solo hay imagen → loop 3 s.

Requiere secrets:
  IG_USERNAME  IG_PASSWORD  IG_SESSION
  REDDIT_CLIENT_ID  REDDIT_SECRET
"""

import os, json, random, tempfile, pathlib, subprocess, requests, praw
from instagrapi import Client
from moviepy.editor import VideoFileClip, ImageClip

# ──────────────────────────── SECRETS ─────────────────────────────────────
IG_USER  = os.environ["IG_USERNAME"]
IG_PASS  = os.environ["IG_PASSWORD"]
SESSION  = os.environ["IG_SESSION"]
RID      = os.environ["REDDIT_CLIENT_ID"]
RSEC     = os.environ["REDDIT_SECRET"]

TMP = tempfile.mkdtemp()
POSTED_FILE = pathlib.Path("posted.json")   # para no repetir IDs
posted_ids: set[str] = set()
if POSTED_FILE.exists():
    posted_ids = set(json.loads(POSTED_FILE.read_text()))

# ─────────────────────────── UTILS ────────────────────────────────────────
def verticalize(path_in: str) -> str:
    """Recorta horizontal a 9:16 conservando centro."""
    if not path_in.endswith(".mp4"):
        return path_in
    clip = VideoFileClip(path_in)
    w, h = clip.size
    if h >= w:
        return path_in
    new_h = w * 16 // 9
    clip = (clip.resize(height=new_h)
                .crop(x_center=w//2, width=w,
                      y1=(new_h-h)//2, y2=(new_h+h)//2))
    out = pathlib.Path(TMP, "vertical.mp4")
    clip.write_videofile(str(out), audio_codec="aac", logger=None)
    return str(out)

def mark_posted(pid: str):
    posted_ids.add(pid)
    POSTED_FILE.write_text(json.dumps(list(posted_ids)))
    # commit rápido; si push falla no es crítico
    subprocess.run(["git", "add", str(POSTED_FILE)])
    subprocess.run(["git", "commit", "-m", f"bot: mark {pid}"], check=False)
    subprocess.run(["git", "push"], check=False)

# ───────────────────── 1. YT Shorts Trending (Piped) ─────────────────────
def fetch_shorts(max_trials=10) -> str | None:
    api = "https://piped.video/api/trending?region=US&category=SHORTS"
    try:
        entries = requests.get(api, timeout=20).json()
    except Exception as e:
        print("⚠️  Piped API error:", e)
        return None

    random.shuffle(entries)
    for i, entry in enumerate(entries):
        if i >= max_trials:
            break
        url = entry["url"]            # /watch?v=ID
        out = pathlib.Path(TMP, "short.mp4")
        code = subprocess.run(
            ["yt-dlp", "-q", "-o", str(out), url]
        ).returncode
        if code == 0 and out.exists():
            print("✅  Short OK:", url)
            return str(out)
    return None

# ────────────────────── 2. Reddit vídeo / imagen ─────────────────────────
SUBS = ("videos+Unexpected+PublicFreakout+reels+Instagramreels+TikTokCringe+"
        "dankmemes+me_irl+wholesomememes")

def fetch_reddit() -> str | None:
    reddit = praw.Reddit(client_id=RID, client_secret=RSEC,
                         user_agent="reelriot/0.6")
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

# ──────────────────────── Selector ───────────────────────────────────────
resource = fetch_shorts() or fetch_reddit()
if resource is None:
    raise RuntimeError("🔴  No Shorts ni Reddit vídeo/imagen disponibles")

# imagen → mp4 loop 3 s
if resource.endswith((".jpg", ".jpeg", ".png")):
    clip = ImageClip(resource).set_duration(3).resize(height=1920)
    out = pathlib.Path(TMP, "loop.mp4")
    clip.write_videofile(str(out), fps=24, audio=False, logger=None)
    resource = str(out)

resource = verticalize(resource)

# ─────────────────────── Publicar en IG ───────────────────────────────────
ig = Client(); ig.set_settings(json.loads(SESSION)); ig.login(IG_USER, IG_PASS)

CAPTION = ("🤣 Daily chaos 🚀\n"
           "➡️ Follow @reelriot.tv for more\n"
           "#funny #viral #meme #reelriot #scrolllaughrepeat #riotmemes")

ig.video_upload(resource, caption=CAPTION)
print("🎉 Publicado:", resource)
