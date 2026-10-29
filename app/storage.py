"""Tiny JSON database saved on Google Drive, so nothing is lost when Colab restarts."""
import json
import threading
import time
import uuid

from .config import DB_FILE, ensure_dirs

_lock = threading.Lock()
DEFAULT = {
    "images": [],          # {id, path, w, h, category, subject, source, at}
    "posts": {},           # image_id -> {headline, cta, caption, hashtags, rendered}
    "biodata": [],         # {id, photo, details, rendered, opts, at}
    "headlines": [],       # last 200 headlines, never repeat
    "used_names": [],      # {name, at}
    "settings": {"brand_on": True, "brand_name": "Apna Connection", "footer": "", "post_type": "Normal",
                 "instruction": "", "format": "png", "bio_brand_on": True},
}


def uid() -> str:
    return uuid.uuid4().hex[:12] + hex(int(time.time()))[2:]


def load() -> dict:
    ensure_dirs()
    with _lock:
        if not DB_FILE.exists():
            return json.loads(json.dumps(DEFAULT))
        try:
            data = json.loads(DB_FILE.read_text("utf-8"))
        except Exception:
            data = {}
    for k, v in DEFAULT.items():
        data.setdefault(k, json.loads(json.dumps(v)))
    for k, v in DEFAULT["settings"].items():
        data["settings"].setdefault(k, v)
    return data


def save(data: dict) -> None:
    ensure_dirs()
    with _lock:
        tmp = DB_FILE.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, ensure_ascii=False, indent=1), "utf-8")
        tmp.replace(DB_FILE)


def update(fn):
    data = load()
    out = fn(data)
    save(data)
    return out


def push_headline(h: str):
    h = h.strip()
    if not h:
        return

    def f(d):
        d["headlines"] = [h] + [x for x in d["headlines"] if x != h]
        d["headlines"] = d["headlines"][:200]
    update(f)
