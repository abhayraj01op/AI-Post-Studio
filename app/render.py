"""Draws Hindi text on photos with Pillow (+ libraqm for correct Devanagari shaping).
The image model never writes text; all text is drawn here so spelling stays correct."""
from PIL import Image, ImageDraw, ImageFilter, ImageFont, features

from .config import FONTS_DIR

MAROON = (122, 31, 26)
MARIGOLD = (242, 165, 22)
CREAM = (251, 244, 230)
INK = (43, 26, 20)
WHITE = (255, 255, 255)
LAYOUT = ImageFont.Layout.RAQM if features.check("raqm") else ImageFont.Layout.BASIC


def font(weight: str, size: int) -> ImageFont.FreeTypeFont:
    name = {"800": "Mukta-ExtraBold.ttf", "700": "Mukta-Bold.ttf", "500": "Mukta-Medium.ttf"}[weight]
    return ImageFont.truetype(str(FONTS_DIR / name), size, layout_engine=LAYOUT)


def fit_cover(img: Image.Image, w: int, h: int, focus_y: float = 0.35) -> Image.Image:
    s = max(w / img.width, h / img.height)
    nw, nh = round(img.width * s), round(img.height * s)
    img = img.resize((nw, nh), Image.LANCZOS)
    x = (nw - w) // 2
    y = int(max(0, min(nh - h, (nh - h) * focus_y)))
    return img.crop((x, y, x + w, y + h))


def fit_contain_blur(img: Image.Image, w: int, h: int) -> Image.Image:
    """Full photo ko bina kaate fit karo; khali jagah mein usi photo ka blur background."""
    img = img.convert("RGB")
    bg = fit_cover(img, w, h).filter(ImageFilter.GaussianBlur(28))
    s = min(w / img.width, h / img.height)
    fg = img.resize((round(img.width * s), round(img.height * s)), Image.LANCZOS)
    bg.paste(fg, ((w - fg.width) // 2, (h - fg.height) // 2))
    return bg


def fit_photo(img: Image.Image, w: int, h: int, full: bool) -> Image.Image:
    """Full photo: agar crop karne se pair/sir katenge to blur-fit use karo."""
    if not full:
        return fit_cover(img, w, h)
    ratio_loss = abs((img.width / img.height) - (w / h)) / (w / h)
    return fit_cover(img, w, h, 0.5) if ratio_loss < 0.08 else fit_contain_blur(img, w, h)


LABELS = {
    "hi": dict(edu="पढ़ाई", job="जॉब", city="शहर", status="स्टेटस", kids="बच्चे", fam="फैमिली", want="पार्टनर कैसा चाहिए:", yrs="वर्ष"),
    "en": dict(edu="Padhai", job="Job", city="Shehar", status="Status", kids="Bachche", fam="Family", want="Partner kaisa chahiye:", yrs="saal"),
}


def wrap(d: ImageDraw.ImageDraw, text: str, f, max_w: int) -> list[str]:
    lines, line = [], ""
    for word in text.split():
        t = f"{line} {word}".strip()
        if d.textlength(t, font=f) > max_w and line:
            lines.append(line)
            line = word
        else:
            line = t
    if line:
        lines.append(line)
    return lines


def _gradient(w: int, h: int, top_alpha: int, bottom_alpha: int) -> Image.Image:
    g = Image.new("L", (1, h))
    for y in range(h):
        g.putpixel((0, y), int(top_alpha + (bottom_alpha - top_alpha) * y / max(1, h - 1)))
    g = g.resize((w, h))
    layer = Image.new("RGBA", (w, h), (40, 10, 6, 0))
    layer.putalpha(g)
    return layer


def render_post(img: Image.Image, headline: str, cta: str, brand_on: bool, brand_name: str, footer: str) -> Image.Image:
    img = img.convert("RGBA")
    W, H = img.size
    pad = int(W * 0.07)
    d = ImageDraw.Draw(img)
    hs = int(min(W * 0.066, H * 0.05))
    hf = font("800", hs)
    hl = wrap(d, headline, hf, W - pad * 2)[:2]
    brand = bool(brand_on and (brand_name or "").strip())
    band = int(pad * 1.2 + len(hl) * hs * 1.3 + (W * 0.05 if brand else 0))
    img.alpha_composite(_gradient(W, int(band * 1.5), 210, 0), (0, 0))
    y = int(pad * 0.8)
    d = ImageDraw.Draw(img)
    if brand:
        bf = font("700", int(W * 0.03))
        d.text((W / 2, y), f"• {brand_name} •", font=bf, fill=MARIGOLD, anchor="mt")
        y += int(W * 0.05)
    shadow = Image.new("RGBA", img.size, (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    yy = y
    for line in hl:
        sd.text((W / 2 + 2, yy + 3), line, font=hf, fill=(0, 0, 0, 170), anchor="mt")
        yy += int(hs * 1.3)
    img.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(6)))
    d = ImageDraw.Draw(img)
    for line in hl:
        d.text((W / 2, y), line, font=hf, fill=WHITE, anchor="mt")
        y += int(hs * 1.3)

    cs = int(min(W * 0.042, H * 0.032))
    cf = font("700", cs)
    cl = wrap(d, cta, cf, W - pad * 3)[:2]
    fh = int(W * 0.045) if (footer or "").strip() else 0
    ch = int(len(cl) * cs * 1.3 + cs * 0.9)
    bh = int(ch + fh + pad * 1.4)
    img.alpha_composite(_gradient(W, int(bh * 1.2), 0, 225), (0, H - int(bh * 1.2)))
    d = ImageDraw.Draw(img)
    cw = min(W - pad * 2, int(max(d.textlength(l, font=cf) for l in cl) + cs * 1.8))
    cy = int(H - pad * 0.8 - fh - ch)
    d.rounded_rectangle(((W - cw) // 2, cy, (W + cw) // 2, cy + ch), radius=int(ch / 2.4), fill=MARIGOLD)
    for i, line in enumerate(cl):
        d.text((W / 2, cy + cs * 0.45 + i * cs * 1.3), line, font=cf, fill=INK, anchor="mt")
    if fh:
        d.text((W / 2, H - pad * 0.8 - fh + W * 0.012), footer, font=font("500", int(W * 0.028)), fill=CREAM, anchor="mt")
    return img.convert("RGB")


def render_biodata(photo: Image.Image, b: dict, brand_on: bool, brand_name: str) -> Image.Image:
    L = LABELS["en" if b.get("lang", "").startswith("Hinglish") else "hi"]
    full = b.get("photo_type") == "Full photo"
    W, PH = 1080, (1200 if full else 900)
    H = PH + 820
    c = Image.new("RGB", (W, H), CREAM)
    c.paste(fit_contain_blur(photo, W, PH) if full else fit_cover(photo.convert("RGB"), W, PH, 0.25), (0, 0))
    d = ImageDraw.Draw(c)
    d.rectangle((0, PH, W, PH + 14), fill=MAROON)
    d.rectangle((0, PH + 14, W, PH + 20), fill=MARIGOLD)
    if brand_on and (brand_name or "").strip():
        bf = font("700", 34)
        bw = min(W - 60, int(d.textlength(brand_name, font=bf) + 64))
        d.rounded_rectangle((30, 30, 30 + bw, 94), radius=32, fill=MAROON)
        d.text((30 + bw / 2, 62), brand_name, font=bf, fill=CREAM, anchor="mm")
    y = PH + 50
    title = b["name_roman"] if L is LABELS["en"] else b["name_hindi"]
    d.text((60, y), title, font=font("800", 64), fill=MAROON)
    y += 88
    d.text((60, y), f"{b['age']} {L['yrs']}  •  {b['height']}  •  {b['community']}", font=font("500", 34), fill=INK)
    y += 70
    rows = [(L["edu"], b["education"]), (L["job"], b["job"]), (L["city"], f"{b['city']}, {b['state']}"),
            (L["status"], b["marital_status"])]
    if b.get("children") and b["children"] != "—":
        rows.append((L["kids"], b["children"]))
    rows.append((L["fam"], b["family"]))
    kf, vf = font("700", 32), font("500", 32)
    for k, v in rows:
        d.text((60, y), f"{k}:", font=kf, fill=MAROON)
        lines = wrap(d, str(v), vf, W - 380)[:2] or [""]
        for i, l in enumerate(lines):
            d.text((320, y + i * 42), l, font=vf, fill=INK)
        y += len(lines) * 42 + 18
    y += 10
    exp = wrap(d, b["expectations"], vf, W - 180)[:3]
    box = Image.new("RGBA", (W - 80, 70 + len(exp) * 42), (0, 0, 0, 0))
    ImageDraw.Draw(box).rounded_rectangle((0, 0, box.width - 1, box.height - 1), radius=24, fill=(242, 165, 22, 46))
    c.paste(box, (40, y), box)
    d = ImageDraw.Draw(c)
    d.text((70, y + 20), L["want"], font=kf, fill=MAROON)
    for i, l in enumerate(exp):
        d.text((70, y + 64 + i * 42), l, font=vf, fill=INK)
    return c
