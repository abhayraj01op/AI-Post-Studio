"""Image prompts: real-looking Indian rishta photos, every face different, never any text.

Important: SDXL does NOT understand "no X" in the positive prompt — writing "no sindoor"
actually ADDS sindoor. Sindoor and mangalsutra stay ONLY in NEGATIVE; an optional small bindi is allowed.
"""
import random

from .config import age_range

# Face identity is built from many independent traits -> thousands of different faces.
FACE_SHAPE = ["oval face", "round face", "square jaw", "heart-shaped face", "long narrow face", "diamond face"]
SKIN = ["wheatish skin", "dusky brown skin", "light brown skin", "fair skin", "deep brown skin", "olive skin"]
EYES = ["big expressive eyes", "small almond eyes", "deep-set eyes", "hooded eyes", "slightly droopy eyes"]
NOSE = ["sharp nose", "broad nose", "small button nose", "long straight nose", "slightly hooked nose"]
MARKS = ["a small mole on the cheek", "light freckles", "dimples", "a slightly crooked smile", "thick eyebrows",
         "thin eyebrows", "a beauty spot near the lips", "laugh lines", "a warm bright smile", ""]
BUILD = ["slim build", "average build", "slightly chubby", "athletic build", "petite"]
REGION = ["Punjabi", "Rajasthani", "Bihari", "Marathi", "Gujarati", "Bengali", "Uttar Pradesh", "Haryanvi",
          "Madhya Pradesh", "Uttarakhand", "Jharkhand", "Delhi", "Tamil", "Telugu", "Kannada", "Malayali",
          "Assamese", "Odia", "Kashmiri", "Konkani"]
HAIR_F = ["long hair in a simple braid", "shoulder-length open hair", "hair tied in a low bun", "wavy hair in a ponytail",
          "straight long open hair", "curly hair tied back"]
HAIR_M = ["short neat haircut", "side-parted hair", "slightly curly short hair", "short hair with light stubble",
          "neat hair with a trimmed beard", "clean-shaven with short hair", "receding hairline, short hair"]

# Hands-safe poses only (hands hidden / relaxed) -> far fewer broken fingers.
POSES = [
    "standing straight facing camera with a soft smile, arms relaxed at sides",
    "seated on a chair, hands resting in lap, looking at camera",
    "standing with body slightly turned, face to camera, arms relaxed",
    "standing with hands behind back, gentle smile",
    "laughing naturally while looking slightly away",
    "standing near a wall, relaxed posture",
    "sitting on steps, hands on knees, smiling",
    "standing with arms loosely folded, confident smile",
    "looking over the shoulder at camera",
    "turning head towards camera, soft expression",
]
COUPLE_POSES = [
    "standing side by side, shoulders touching, both smiling at camera",
    "standing close, his arm around her shoulder, both looking at camera",
    "walking together side by side, smiling at each other",
    "sitting together on a bench, smiling at camera",
]
ANGLES = ["eye-level shot", "slightly low angle", "slightly high angle", "three-quarter view from the left",
          "three-quarter view from the right"]
PLACES = [
    "a leafy park in an Indian city", "a rooftop terrace at golden hour", "an old haveli courtyard",
    "a home balcony with plants", "a small-town street with pastel walls", "a cafe corner by a window",
    "a mustard field", "a college campus lawn", "a living room with warm lamps", "a photo studio with a grey backdrop",
    "a garden with flowering bushes", "a marble-floored hall with curtains", "a front gate of a family home",
    "a lakeside walkway", "a staircase in an old building", "a terrace with a city skyline behind",
]
LIGHT = ["soft morning daylight", "warm golden-hour sunlight", "overcast diffused light",
         "window light from the side", "open shade on a sunny day"]
# Garments described as properly worn so the model doesn't melt fabric.
OUTFITS_F = ["a well-fitted cotton salwar kameez with a neatly draped dupatta", "a neatly draped plain saree",
             "a straight kurta with palazzo trousers and dupatta", "a long anarkali kurta", "a white chikankari kurta with palazzo",
             "a simple cotton kurta with leggings", "a printed cotton kurta with leggings"]
OUTFITS_M = ["a well-fitted linen kurta and pyjama", "a pressed formal shirt and trousers",
             "a cotton kurta with trousers", "a neat shirt and trousers", "a nehru jacket over a kurta",
             "a checked shirt and trousers", "a plain blazer over a shirt"]
OLD_SAREE = ["a simple cotton saree", "a plain printed saree", "a light silk saree"]
AGES_YOUNG = [28, 29, 30, 31, 32, 33, 34]
AGES_RE = [35, 37, 39, 41, 43, 45, 47]

NEGATIVE = (
    # forbidden on everyone
    "sindoor, vermilion in hair parting, red powder in hair parting, mangalsutra, "
    "bridal jewellery, heavy jewellery, nose ring, maang tikka, bridal makeup, wedding dress, lehenga, "
    # quality
    "text, letters, words, watermark, logo, caption, signature, numbers, cartoon, anime, illustration, 3d render, "
    "cgi, painting, doll, plastic skin, airbrushed, waxy skin, deformed face, asymmetrical eyes, cross-eyed, "
    "extra fingers, fused fingers, missing fingers, mutated hands, bad hands, extra limbs, extra arms, "
    "melted clothes, torn clothes, malformed clothing, duplicate person, twins, same face, blurry, lowres, "
    "jpeg artifacts, oversaturated, overexposed, bollywood actor, celebrity, beauty filter, nsfw, "
    # body parts must be whole and clean
    "blurry face, blurry eyes, soft focus, out of focus, motion blur, low detail, smeared fabric, merged eyes, missing eye, distorted nose, missing nose, melted face, "
    "deformed hands, missing hand, extra hand, fused bodies, merged people, cut off head, cut off feet, "
    "extra legs, missing legs, long neck, bad anatomy, disfigured, poorly drawn face, ugly, unattractive"
)

# ---- Class look: Normal / Middle / High class -> kapde, jagah, background alag ----
CLASS_LOOK = {
    "Normal": dict(
        tone="simple everyday",
        f=["a cotton salwar suit with dupatta", "a neatly draped printed cotton saree", "a simple kurta with leggings",
           "a plain kurta with palazzo trousers", "a bandhani print salwar suit", "a cotton anarkali kurta"],
        m=["a checked shirt and trousers", "a simple formal shirt and trousers", "a cotton kurta pyjama",
           "a half-sleeve shirt and trousers", "a simple kurta with trousers"],
        places=["a small-town street with pastel walls", "a village courtyard with neem tree", "a terrace with water tank",
                "a local temple steps (no religious marks on people)", "a mustard field", "a home courtyard with plants",
                "a small park with benches", "a home doorway with colourful walls"]),
    "Middle class": dict(
        tone="neat well-dressed middle-class",
        f=["a well-fitted chikankari kurta with palazzo", "a saree neatly draped", "a long anarkali kurta",
           "a straight kurta with palazzo trousers and dupatta", "a tasteful indo-western kurta set", "a pastel salwar suit with organza dupatta"],
        m=["a pressed formal shirt and trousers", "a neat polo shirt and trousers", "a linen kurta and trousers",
           "a pressed shirt and trousers", "a nehru jacket over a kurta"],
        places=["a home balcony with plants", "a cafe corner by a window", "a city park with trees", "a college campus lawn",
                "a living room with warm lamps", "a lakeside walkway", "a society garden", "a clean mall corridor"]),
    "High class": dict(
        tone="elegant affluent, premium styling",
        f=["an elegant silk saree with tasteful embroidery", "a refined embroidered salwar suit", "a chic indo-western kurta with palazzo",
           "a stylish silk kurta set with dupatta", "a refined Indian co-ord kurta set", "a luxury pastel anarkali kurta suit"],
        m=["a tailored formal suit", "a refined bandhgala", "a crisp white shirt with blazer", "a well-cut sherwani-style kurta",
           "a smart blazer over a kurta"],
        places=["a luxury hotel lobby", "a rooftop lounge at golden hour", "a modern villa garden", "a fine-dining restaurant",
                "a marble-floored hall with chandelier", "a heritage palace courtyard", "a luxury car showroom",
                "a resort garden with a clear view"]),
}
CLASS_KEYS = list(CLASS_LOOK)


def look(cls: str) -> dict:
    if cls == "Bold":
        base = CLASS_LOOK["Middle class"].copy()
        base.update(
            tone="tasteful confident editorial, polished but realistic",
            f=["a jewel-tone silk kurta set with a neatly draped dupatta", "an elegant deep-colour saree, modest styling",
               "a structured indowestern kurta set with subtle earrings", "a well-tailored festive salwar suit with tasteful embroidery"],
        )
        return base
    return CLASS_LOOK.get(cls) or CLASS_LOOK[random.choice(CLASS_KEYS)]


_decks: dict[int, list] = {}


def draw(a: list):
    """Cycles through a shuffled list so values don't repeat until all are used."""
    d = _decks.get(id(a))
    if not d:
        d = a[:]
        random.shuffle(d)
        _decks[id(a)] = d
    return d.pop()


# ---- Face identity: these traits change the skull/flesh, which is what really makes faces differ ----
WEIGHT = ["slim", "fit", "average weight", "slightly curvy", "healthy build with full cheeks", "lean"]
JAW = ["narrow pointed chin", "defined jawline", "soft rounded jaw", "high cheekbones", "prominent chin", "broad cheekbones"]
LIPS = ["thin lips", "full lips", "wide smile", "small mouth", "soft pink lips"]
FOREHEAD = ["broad forehead", "small forehead", "high forehead", "low hairline"]
EARS = ["", "", "small ears", ""]
GLASSES = ["thin metal-frame spectacles", "black rectangular spectacles", "", "", "", "", ""]
BEARD = ["full black beard", "short stubble", "thick moustache, no beard", "clean-shaven", "goatee",
         "salt-and-pepper stubble", "light patchy beard"]
TONE_W = [1.15, 1.2, 1.25, 1.3]


def _identity(gender: str, age: int) -> str:
    """Short, weighted, front-loaded identity text (SDXL reads the first ~75 tokens best)."""
    f = gender == "woman"
    bits = [f"{age} years old", draw(WEIGHT), draw(FACE_SHAPE), draw(JAW), draw(SKIN), draw(EYES), draw(NOSE),
            draw(LIPS), draw(FOREHEAD), draw(MARKS), draw(EARS), random.choice(GLASSES)]
    if not f:
        bits.append(draw(BEARD))
    bits = [b for b in bits if b]
    return f"({', '.join(bits)}:{random.choice(TONE_W)})"


def person(gender: str, age: int, lk: dict | None = None) -> tuple[str, str]:
    """Returns (scene text for this person, identity text used for face mixing + face fix)."""
    f = gender == "woman"
    lk = lk or look("Mix")
    ident = _identity(gender, age)
    hair = draw(HAIR_F if f else HAIR_M)
    outfit = draw(lk["f"] if f else lk["m"])
    clean = ", optional small bindi, natural hair parting, natural light makeup, tasteful small earrings" if f else ", well-groomed"
    authenticity = ("an ordinary Indian woman with authentic Indian facial features and natural Indian skin tone variation; "
                    "everyday matrimonial portrait, not a fashion model, not Western-looking" if f else
                    "an ordinary Indian man with authentic Indian facial features and natural Indian skin tone variation; "
                    "everyday matrimonial portrait, not a fashion model, not Western-looking")
    return (f"{authenticity}, {draw(REGION)} Indian {gender} {ident}, {hair}{clean}, wearing {outfit}", ident)


def _job(scene: str, ident_a: str, ident_b: str | None, face: str, full: bool = False) -> dict:
    neg = NEGATIVE + (", close-up, half body, cropped legs, cut off at knees, out of frame" if full else "")
    return {"scene": scene, "ident_a": ident_a, "ident_b": ident_b, "face": face, "neg": neg}


FULL = ("full-length wide shot, the ENTIRE body visible from the top of the head down to the shoes, feet and shoes "
        "clearly visible on the ground, camera 4 meters away, subject small enough to fit fully in frame with space around")
HALF = "medium shot, framed from the waist up, both hands relaxed"


def build_image_prompt(category: str, subject: str, full: bool, extra: str, cls: str = "Mix",
                       reference: str = "", avoid: str = "") -> dict:
    """Returns a job dict for comfy.generate: scene prompt + two identities that get blended
    at a random ratio -> a brand-new face every time (fixes 'sab mein same face')."""
    lo, hi = age_range(category)
    af, am = random.randint(lo, hi), random.randint(lo, hi)
    lk = look(cls)
    pose = draw(POSES)
    g = None
    if subject == "Couple":
        (w, wi), (m, mi) = person("woman", af, lk), person("man", am, lk)
        who, ident, face = f"a couple, two separate people: {w}; and {m}", None, f"{wi}, {mi}"
        pose = draw(COUPLE_POSES)
    elif subject in ("Female", "Male"):
        g = "woman" if subject == "Female" else "man"
        who, ident = person(g, af if g == "woman" else am, lk)
        face = ident
    elif subject == "BetiMaa":
        d, ident = person("woman", af, lk)
        who = (f"{d}, standing with her mother, a {af + random.randint(22, 28)}-year-old graceful Indian woman "
               f"with a few grey hairs, optional small bindi, natural hair parting, wearing {draw(OLD_SAREE)}")
        face, g = ident, "woman"
        pose = "standing side by side, smiling at camera"
    else:
        s_, ident = person("man", am, lk)
        who = (f"{s_}, with his elderly mother, a {am + random.randint(25, 30)}-year-old graceful Indian woman "
               f"with grey hair, optional small bindi, natural hair parting, wearing {draw(OLD_SAREE)}")
        face, g = ident, "man"
        pose = "standing side by side, both smiling"
    if full:
        pose = pose.replace("seated on a chair, ", "standing, ").replace("sitting on steps, hands on knees", "standing on steps")
    composition = (FULL + ". " if full else HALF + ". ")
    if subject == "Female":
        composition += "Portrait framing: keep her entire head, hairline, and chin inside the image, with space above her head. Both eyes open, naturally aligned, sharp and clear, looking near the camera. Face is unobstructed and in focus. Crisp focus across face, clothing and fabric texture. "
    scene = " ".join(p for p in [
        composition + f"RAW photo of {who}.",
        f"{pose}. {draw(ANGLES)}, {FULL if full else HALF}. Location: {draw(lk['places'])}, {draw(LIGHT)}.",
        f"{lk['tone']} look, natural Indian people, clothes neatly worn, faces sharp and clear, crisp fabric detail and natural skin texture.",
        "Canon EOS R5, 50mm f/2.8, sharp eyes, detailed natural skin texture, real photograph.",
        extra.strip()[:300],
        f"Follow these saved visual reference notes: {reference.strip()[:500]}" if reference.strip() else "",
    ] if p)
    ident_b = _identity(g, af if g == "woman" else am) if g else None
    face_safe = ", closed eyes, missing eye, extra eye, merged eyes, cross-eyed, asymmetrical eyes, looking away, head cropped, hair cropped, forehead cut off, chin cut off, blurred face"
    job = _job(scene, ident or "", ident_b, f"RAW close-up photo of an attractive Indian {g or 'person'}, {face}, "
                "detailed natural skin, sharp clear eyes, beautiful", full)
    if subject == "Female":
        job["neg"] += face_safe
    if avoid.strip():
        job["neg"] += ", " + avoid.strip()[:500]
    return job


def build_portrait_prompt(gender: str, age: int, community: str, state: str, remarriage: bool,
                          full: bool = False, cls: str = "Mix", reference: str = "", avoid: str = "") -> dict:
    g = "woman" if gender == "Female" else "man"
    lk = look(cls)
    desc, ident = person(g, age, lk)
    region = state if state and state != "All" else draw(REGION)
    community_hint = f"The selected biodata community is {community}; show an ordinary, respectful person without assuming one fixed appearance or costume." if community and community != "All" else ""
    portrait_neg = NEGATIVE + ", closed eyes, missing eye, extra eye, merged eyes, cross-eyed, asymmetrical eyes, looking away, head cropped, hair cropped, forehead cut off, chin cut off, blurred face"
    quality = "crisp, evenly focused face, eyes, clothing and fabric weave; realistic skin texture; clear unobtrusive background with balanced natural depth"
    clothing = "tasteful everyday Indian matrimonial clothing, neatly worn, modest and well-fitted, realistic fabric folds; an optional small bindi is acceptable, but the hair parting is natural"
    if full:
        scene = (f"{FULL}. RAW photo of {desc}, from {region}, standing with both hands visible and relaxed naturally at their sides; if hands are visible, each has five distinct natural fingers, correctly separated and naturally proportioned. {community_hint} {clothing}. {f'Saved reference notes: {reference.strip()[:500]}' if reference.strip() else ''} {random.choice(ANGLES)}. "
                 f"Location: {draw(lk['places'])}, {random.choice(LIGHT)}. {lk['tone']} look. "
                 "Keep the entire head including hairline and chin inside frame, with space above the head. Both eyes open, aligned, sharp and unobstructed, looking near the camera. "
                 f"{quality}. Canon EOS R5 50mm, detailed natural skin, real photograph.")
        job = {**_job(scene, ident, _identity(g, age), f"RAW close-up photo of an attractive Indian {g}, {ident}, both eyes open and aligned, sharp clear eyes", True), "neg": portrait_neg + ", close-up, half body, cropped legs, cut off at knees, out of frame"}
        if avoid.strip():
            job["neg"] += ", " + avoid.strip()[:500]
        return job
    bg = draw(["plain softly lit home wall", "simple grey studio backdrop", "home wall with a few plants", "quiet garden with clear visible foliage", "living room with simple curtains", "clean terrace with distant buildings"])
    framing = ("medium portrait from mid-torso upward, both shoulders and upper body clearly visible, full head and chin visible inside frame, "
               "comfortable space above hair, face not filling the frame, centered natural composition")
    scene = (f"RAW amateur matrimonial profile photo, {framing} of {desc}, from {region}. Keep the face moderately sized, approximately one-third of the image height, with the upper torso visible. {community_hint} {clothing}. {f'Saved reference notes: {reference.strip()[:500]}' if reference.strip() else ''} "
            f"{random.choice(['gentle smile facing camera', 'soft smile, head slightly tilted', 'calm confident look', 'warm natural smile'])}, "
            f"{random.choice(['straight-on eye-level portrait', 'slight three-quarter view, both eyes visible'])}, mid-torso portrait framing, hands out of frame. Both eyes open, naturally aligned and looking toward camera; both eyebrows, nose, mouth, hairline, and chin complete and unobstructed. Face is the sharp focal point, not cropped. Background: {bg}, clear but understated. {random.choice(LIGHT)}. "
            f"Indian matrimonial profile photo, natural camera perspective, sharp eyes and fabric texture, realistic Indian features, balanced natural face, unretouched, authentic everyday person, not a beauty model. {quality}")
    job = {**_job(scene, ident, _identity(g, age), f"RAW close-up photo of an ordinary Indian {g}, {ident}, both eyes open and aligned, clear sharp eyes, full hairline and chin visible, "
                "real skin texture with pores, unretouched"), "neg": portrait_neg + ", extreme close-up, face fills the frame, oversized face crop, tight headshot crop"}
    if avoid.strip():
        job["neg"] += ", " + avoid.strip()[:500]
    return job
