"""Light extra tools (no GPU, no AI): multi-size export, watermark, weekly plan, leads list."""
import csv
import random
import time
import zipfile
from datetime import date, timedelta

from PIL import Image, ImageDraw, ImageFont

from . import storage
from .config import DATA, FONTS_DIR, POST_TYPES

EXPORT_DIR = DATA / "exports"
PLATFORMS = {
    "Instagram post (1080x1080)": (1080, 1080),
    "Instagram portrait (1080x1350)": (1080, 1350),
    "WhatsApp Status / Reel (1080x1920)": (1080, 1920),
    "Facebook post (1200x630)": (1200, 630),
}
DAYS = ["Somvar", "Mangalvar", "Budhvar", "Guruvar", "Shukravar", "Shanivar", "Ravivar"]
TIMES = ["Subah 9 baje", "Dopahar 1 baje", "Shaam 7 baje", "Raat 9 baje"]
LEAD_STATUS = ["Naya", "Baat chal rahi", "Biodata bheja", "Meeting fix", "Rishta pakka", "Band"]


def _font(size):
    for f in sorted(FONTS_DIR.glob("*.ttf")):
        try:
            return ImageFont.truetype(str(f), size)
        except Exception:
            continue
    try:
        return ImageFont.load_default(size)
    except TypeError:
        return ImageFont.load_default()


def _sources(ids, all_items):
    db = storage.load()
    out = []
    for iid, p in db["posts"].items():
        if (all_items or iid in (ids or [])) and p.get("rendered"):
            out.append((iid, p["rendered"]))
    for b in db["biodata"]:
        if (all_items or b["id"] in (ids or [])) and b.get("rendered"):
            out.append((b["id"], b["rendered"]))
    return out


def all_ids():
    db = storage.load()
    return [i for i, p in db["posts"].items() if p.get("rendered")] + [b["id"] for b in db["biodata"] if b.get("rendered")]


def fit_pad(img: Image.Image, w: int, h: int) -> Image.Image:
    """Poori post bina kaate fit; bachi jagah usi photo ka dhundhla background."""
    img = img.convert("RGB")
    bg = img.copy()
    s = max(w / bg.width, h / bg.height)
    bg = bg.resize((int(bg.width * s) + 1, int(bg.height * s) + 1)).crop((0, 0, w, h))
    from PIL import ImageFilter
    bg = bg.filter(ImageFilter.GaussianBlur(28))
    s = min(w / img.width, h / img.height)
    fg = img.resize((max(1, int(img.width * s)), max(1, int(img.height * s))), Image.LANCZOS)
    bg.paste(fg, ((w - fg.width) // 2, (h - fg.height) // 2))
    return bg


def watermark(img: Image.Image, number: str, logo_path, pos: str, opacity: int) -> Image.Image:
    img = img.convert("RGBA")
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    a = int(255 * max(10, min(100, opacity)) / 100)
    pad = img.width // 40
    x_right = pos.endswith("right")
    y_bottom = pos.startswith("Neeche")
    items = []
    if logo_path:
        try:
            lg = Image.open(logo_path).convert("RGBA")
            lw = img.width // 7
            lg = lg.resize((lw, max(1, int(lg.height * lw / lg.width))))
            lg.putalpha(lg.getchannel("A").point(lambda v: v * a // 255))
            items.append(("logo", lg))
        except Exception:
            pass
    if number and number.strip():
        items.append(("text", "WhatsApp: " + number.strip()))
    font = _font(max(18, img.width // 32))
    y = pad
    heights = []
    for kind, v in items:
        heights.append(v.height if kind == "logo" else d.textbbox((0, 0), v, font=font)[3] + pad // 2)
    if y_bottom:
        y = img.height - pad - sum(heights) - pad // 2 * len(items)
    for (kind, v), hh in zip(items, heights):
        if kind == "logo":
            x = img.width - pad - v.width if x_right else pad
            layer.alpha_composite(v, (x, y))
        else:
            tw = d.textbbox((0, 0), v, font=font)[2]
            x = img.width - pad - tw - pad // 2 if x_right else pad
            d.rounded_rectangle((x - pad // 3, y - pad // 4, x + tw + pad // 3, y + hh), radius=pad // 2, fill=(0, 0, 0, a // 2))
            d.text((x, y), v, font=font, fill=(255, 255, 255, a))
        y += hh + pad // 2
    return Image.alpha_composite(img, layer).convert("RGB")


def export_all(ids, all_items, platforms, number, logo, pos, opacity, use_wm):
    src = _sources(ids, all_items)
    if not src:
        return "<p style='color:#b91c1c'>Koi post/biodata chunein (ya 'Sab' tick karein).</p>", None, []
    if not platforms:
        return "<p style='color:#b91c1c'>Kam se kam ek size chunein.</p>", None, []
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    z = DATA / f"exports_{time.strftime('%Y%m%d_%H%M%S')}.zip"
    shown = []
    with zipfile.ZipFile(z, "w") as zf:
        for iid, path in src:
            base = Image.open(path)
            for pl in platforms:
                w, h = PLATFORMS[pl]
                out = fit_pad(base, w, h)
                if use_wm:
                    out = watermark(out, number or "", logo, pos, int(opacity))
                name = f"{iid}_{w}x{h}.jpg"
                p = EXPORT_DIR / name
                out.save(p, quality=92)
                zf.write(p, name)
                if len(shown) < 24:
                    shown.append((str(p), f"{iid} • {w}x{h}"))
    return f"<p style='color:#7a1f1a;font-weight:600'>{len(src)} item × {len(platforms)} size taiyaar. Zip neeche hai.</p>", str(z), shown


def weekly_plan(start: str, per_day: int):
    try:
        d0 = date.fromisoformat((start or "").strip())
    except Exception:
        d0 = date.today()
    types = list(POST_TYPES.values())
    random.shuffle(types)
    rows, k = [], 0
    for i in range(7):
        dt = d0 + timedelta(days=i)
        for t in random.sample(TIMES, min(int(per_day), len(TIMES))):
            kind = "Biodata post" if (i + k) % 4 == 3 else types[k % len(types)]
            rows.append([dt.isoformat(), DAYS[dt.weekday()], t, kind, ""])
            k += 1
    rows.sort(key=lambda r: (r[0], TIMES.index(r[2])))
    storage.update(lambda d: d.__setitem__("plan", rows))
    return rows


def load_plan():
    return storage.load().get("plan") or []


def save_plan(rows):
    data = rows.values.tolist() if hasattr(rows, "values") else (rows or [])
    storage.update(lambda d: d.__setitem__("plan", data))
    return "<p style='color:#7a1f1a;font-weight:600'>Plan save ho gaya.</p>"


LEAD_COLS = ["Date", "Naam", "Phone", "Kahan se", "Kaunsa biodata bheja", "Status", "Note"]


def leads_rows():
    return [[l.get(c, "") for c in LEAD_COLS] for l in storage.load().get("leads", [])]


def add_lead(name, phone, source, bio, status, note):
    if not (name or "").strip() and not (phone or "").strip():
        return "<p style='color:#b91c1c'>Naam ya phone likhein.</p>", leads_rows()
    rec = dict(zip(LEAD_COLS, [time.strftime("%Y-%m-%d"), name or "", phone or "", source or "", ", ".join(bio or []), status, note or ""]))
    storage.update(lambda d: d.setdefault("leads", []).insert(0, rec))
    return "<p style='color:#7a1f1a;font-weight:600'>Lead jud gaya.</p>", leads_rows()


def save_leads(rows):
    data = rows.values.tolist() if hasattr(rows, "values") else (rows or [])
    recs = [dict(zip(LEAD_COLS, [str(x) for x in r])) for r in data if any(str(x).strip() for x in r)]
    storage.update(lambda d: d.__setitem__("leads", recs))
    return "<p style='color:#7a1f1a;font-weight:600'>Leads save ho gaye.</p>", leads_rows()


def leads_csv():
    p = DATA / f"leads_{time.strftime('%Y%m%d_%H%M')}.csv"
    with open(p, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(LEAD_COLS)
        w.writerows(leads_rows())
    return str(p)
