"""Selectable local ComfyUI AI enhancement or explicitly requested Pillow adjustments."""
from PIL import Image, ImageEnhance, ImageFilter, ImageOps

AI_METHOD = "AI (ComfyUI)"
BASIC_METHOD = "Basic (Pillow)"
AI_DESCRIPTION = "ComfyUI AI: 4x-UltraSharp upscaling + low-denoise SDXL refinement; optional FaceDetailer and hand detailer when installed"
BASIC_DESCRIPTION = "Pillow: Lanczos resizing, median denoise, auto contrast, colour, and sharpening; no generative AI"

LEVELS = {
    "Light": dict(contrast=1.03, color=1.03, bright=1.0, sharp=1.15, clarity=60),
    "Normal": dict(contrast=1.08, color=1.08, bright=1.02, sharp=1.3, clarity=90),
    "Strong": dict(contrast=1.13, color=1.12, bright=1.03, sharp=1.5, clarity=120),
}


def _warm(img: Image.Image, amount: float = 0.03) -> Image.Image:
    r, g, b = img.split()
    r = r.point(lambda v: min(255, int(v * (1 + amount))))
    b = b.point(lambda v: int(v * (1 - amount / 2)))
    return Image.merge("RGB", (r, g, b))


def smart_enhance(
    img: Image.Image,
    level: str = "Normal",
    out_size: tuple[int, int] | None = None,
    method: str = AI_METHOD,
) -> tuple[Image.Image, str]:
    """Use AI only when chosen; a ComfyUI failure is surfaced, never hidden by basic edits."""
    if method == BASIC_METHOD:
        return enhance_image(img, level, out_size), BASIC_DESCRIPTION
    if method != AI_METHOD:
        raise ValueError(f"Unknown enhancement method: {method}")
    from . import comfy

    out = comfy.enhance(img.convert("RGB"), level)
    out = enhance_image(out, "Light", out_size, upscale=False)
    return out, AI_DESCRIPTION


def enhance_image(img: Image.Image, level: str = "Normal", out_size: tuple[int, int] | None = None,
                  upscale: bool = True) -> Image.Image:
    p = LEVELS.get(level, LEVELS["Normal"])
    img = img.convert("RGB")
    w, h = out_size or img.size
    big = img.resize((img.width * 2, img.height * 2), Image.LANCZOS) if upscale else img
    if upscale:
        big = big.filter(ImageFilter.MedianFilter(3))           # remove AI noise / jpeg grain
    big = ImageOps.autocontrast(big, cutoff=0.5, preserve_tone=True)
    big = _warm(big)
    big = ImageEnhance.Contrast(big).enhance(p["contrast"])
    big = ImageEnhance.Color(big).enhance(p["color"])
    big = ImageEnhance.Brightness(big).enhance(p["bright"])
    big = big.filter(ImageFilter.UnsharpMask(radius=6, percent=p["clarity"] // 3, threshold=4))  # clarity
    big = big.filter(ImageFilter.UnsharpMask(radius=1.6, percent=p["clarity"], threshold=2))     # detail
    out = big.resize((w, h), Image.LANCZOS)
    return ImageEnhance.Sharpness(out).enhance(p["sharp"])
