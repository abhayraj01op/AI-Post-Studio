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
    """Keep a full-body photo intact on a quiet solid background; do not blur the photo."""
    img = img.convert("RGB")
    bg = Image.new("RGB", (w, h), CREAM)
    s = min(w / img.width, h / img.height)
    fg = img.resize((round(img.width * s), round(img.height * s)), Image.Resampling.LANCZOS)
    bg.paste(fg, ((w - fg.width) // 2, (h - fg.height) // 2))
    return bg


def load_existing_photo(path) -> Image.Image:
    """Load the selected photo without altering its pixels or generating a replacement."""
    with Image.open(path) as source:
        return source.convert("RGB").copy()


def fit_photo(img: Image.Image, w: int, h: int, full: bool) -> Image.Image:
    """Keep full-body images uncropped whenever a cover crop would remove meaningful framing."""
    if not full:
        return fit_cover(img, w, h)
    ratio_loss = abs((img.width / img.height) - (w / h)) / (w / h)
    return fit_cover(img, w, h, 0.5) if ratio_loss < 0.03 else fit_contain_blur(img, w, h)


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


def _fit_wrapped(draw, text, weight, start_size, max_w, max_lines, min_size=22):
    """Shrink text until every word fits; never silently discard overflow lines."""
    size = start_size
    while size >= min_size:
        f = font(weight, size)
        lines = wrap(draw, str(text or ""), f, max_w)
        if len(lines) <= max_lines:
            return f, lines
        size -= 2
    f = font(weight, min_size)
    return f, wrap(draw, str(text or ""), f, max_w)


def render_post(img: Image.Image, headline: str, cta: str, brand_on: bool, brand_name: str, footer: str) -> Image.Image:
    img = img.convert("RGBA")
    W, H = img.size
    pad = int(W * 0.07)
    d = ImageDraw.Draw(img)
    brand = bool(brand_on and (brand_name or "").strip())
    hf, hl = _fit_wrapped(d, headline, "800", int(min(W * 0.066, H * 0.05)), W - pad * 2, 3, 26)
    hs = hf.size
    bf = font("700", max(22, int(W * 0.03))) if brand else None
    top_h = int(pad * 1.2 + len(hl) * hs * 1.22 + (W * 0.05 if brand else 0))
    top_h = min(int(H * 0.34), max(int(H * 0.16), top_h))
    img.alpha_composite(_gradient(W, int(top_h * 1.35), 215, 0), (0, 0))
    y = int(pad * 0.65)
    d = ImageDraw.Draw(img)
    if brand:
        d.text((W / 2, y), f"• {brand_name} •", font=bf, fill=MARIGOLD, anchor="mt")
        y += int(W * 0.05)
    shadow = Image.new("RGBA", img.size, (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    yy = y
    line_gap = int(hs * 1.22)
    for line in hl:
        sd.text((W / 2 + 2, yy + 3), line, font=hf, fill=(0, 0, 0, 170), anchor="mt")
        yy += line_gap
    img.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(5)))
    d = ImageDraw.Draw(img)
    for line in hl:
        d.text((W / 2, y), line, font=hf, fill=WHITE, anchor="mt")
        y += line_gap

    cf, cl = _fit_wrapped(d, cta, "700", int(min(W * 0.042, H * 0.032)), W - pad * 3, 2, 22)
    cs = cf.size
    fh = int(W * 0.045) if (footer or "").strip() else 0
    ch = int(len(cl) * cs * 1.25 + cs * 0.9)
    bh = int(ch + fh + pad * 1.4)
    bottom_h = min(int(H * 0.25), max(int(H * 0.12), int(bh * 1.2)))
    img.alpha_composite(_gradient(W, bottom_h, 0, 230), (0, H - bottom_h))
    d = ImageDraw.Draw(img)
    cw = min(W - pad * 2, int(max(d.textlength(line, font=cf) for line in cl) + cs * 1.8))
    cy = int(H - pad * 0.8 - fh - ch)
    d.rounded_rectangle(((W - cw) // 2, cy, (W + cw) // 2, cy + ch), radius=max(12, int(ch / 2.4)), fill=MARIGOLD)
    for i, line in enumerate(cl):
        d.text((W / 2, cy + cs * 0.42 + i * cs * 1.25), line, font=cf, fill=INK, anchor="mt")
    if fh:
        ff, fl = _fit_wrapped(d, footer, "500", int(W * 0.028), W - pad * 2, 1, 18)
        d.text((W / 2, H - pad * 0.8 - fh + W * 0.012), " ".join(fl), font=ff, fill=CREAM, anchor="mt")
    return img.convert("RGB")


def render_biodata(photo: Image.Image, b: dict, brand_on: bool, brand_name: str) -> Image.Image:
    L = LABELS["en" if b.get("lang", "").startswith("Hinglish") else "hi"]
    full = b.get("photo_type") == "Full photo"
    W, PH = 1080, (1200 if full else 900)
    # Measure all text first. Canvas grows with content; nothing is clipped to a fixed height.
    scratch = Image.new("RGB", (W, 100), CREAM)
    sd = ImageDraw.Draw(scratch)
    title = str(b.get("name_roman", "") if L is LABELS["en"] else b.get("name_hindi", ""))
    name_f, name_lines = _fit_wrapped(sd, title, "800", 64, W - 120, 2, 34)
    meta = f"{b.get('age', '')} {L['yrs']}  •  {b.get('height', '')}  •  {b.get('community', '')}"
    meta_f, meta_lines = _fit_wrapped(sd, meta, "500", 34, W - 120, 2, 24)
    rows = [(L["edu"], b.get("education", "")), (L["job"], b.get("job", "")),
            (L["city"], f"{b.get('city', '')}, {b.get('state', '')}"),
            (L["status"], b.get("marital_status", ""))]
    if b.get("children") and b.get("children") not in ("—", "-", "None"):
        rows.append((L["kids"], b["children"]))
    rows.append((L["fam"], b.get("family", "")))
    kf, vf = font("700", 32), font("500", 32)
    row_lines = [(k, wrap(sd, str(v), vf, W - 390) or [""]) for k, v in rows]
    exp = wrap(sd, str(b.get("expectations", "")), vf, W - 180) or [""]
    # Prevent absurdly tall text from malformed model output while keeping all normal content.
    row_lines = [(k, lines[:8]) for k, lines in row_lines]
    exp = exp[:10]
    content_h = 54 + len(name_lines) * 72 + 24 + len(meta_lines) * 46 + 28
    content_h += sum(max(1, len(lines)) * 44 + 20 for _, lines in row_lines)
    content_h += 35 + 78 + len(exp) * 44 + 42
    H = max(PH + content_h, 1720 if not full else 2020)
    c = Image.new("RGB", (W, H), CREAM)
    c.paste(fit_contain_blur(photo.convert("RGB"), W, PH), (0, 0))
    d = ImageDraw.Draw(c)
    d.rectangle((0, PH, W, PH + 14), fill=MAROON)
    d.rectangle((0, PH + 14, W, PH + 20), fill=MARIGOLD)
    if brand_on and (brand_name or "").strip():
        bf = font("700", 34)
        bw = min(W - 60, int(d.textlength(brand_name, font=bf) + 64))
        d.rounded_rectangle((30, 30, 30 + bw, 94), radius=32, fill=MAROON)
        d.text((30 + bw / 2, 62), brand_name, font=bf, fill=CREAM, anchor="mm")
    y = PH + 45
    for line in name_lines:
        d.text((60, y), line, font=name_f, fill=MAROON)
        y += 72
    y += 15
    for line in meta_lines:
        d.text((60, y), line, font=meta_f, fill=INK)
        y += 46
    y += 15
    for k, lines in row_lines:
        d.text((60, y), f"{k}:", font=kf, fill=MAROON)
        for i, line in enumerate(lines):
            d.text((320, y + i * 44), line, font=vf, fill=INK)
        y += max(1, len(lines)) * 44 + 20
    y += 15
    box_h = 75 + len(exp) * 44
    d.rounded_rectangle((40, y, W - 40, y + box_h), radius=24, fill=(255, 236, 190), outline=MARIGOLD, width=3)
    d.text((70, y + 18), L["want"], font=kf, fill=MAROON)
    for i, line in enumerate(exp):
        d.text((70, y + 68 + i * 44), line, font=vf, fill=INK)
    return c

