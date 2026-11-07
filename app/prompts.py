"""Image prompts: real-looking Indian rishta photos, every face different, never any text.

Important: SDXL does NOT understand "no X" in the positive prompt — writing "no sindoor"
actually ADDS sindoor. So forbidden things (bindi, sindoor, mangalsutra...) live ONLY in NEGATIVE.
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
          "Madhya Pradesh", "Uttarakhand", "Jharkhand", "Delhi"]
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
OUTFITS_F = ["a well-fitted cotton salwar kameez with a neatly draped dupatta", "a neatly draped plain pastel saree",
             "a straight kurti with jeans", "a long anarkali kurta", "a white chikankari kurta with palazzo",
             "a casual top and jeans", "a printed cotton kurta with leggings"]
OUTFITS_M = ["a well-fitted linen kurta and pyjama", "a pressed formal shirt and trousers", "a polo t-shirt and jeans",
             "a denim shirt and chinos", "a nehru jacket over a kurta", "a checked shirt and jeans", "a plain blazer over a shirt"]
OLD_SAREE = ["a simple cotton saree", "a plain printed saree", "a light silk saree"]
AGES_YOUNG = [28, 29, 30, 31, 32, 33, 34]
AGES_RE = [35, 37, 39, 41, 43, 45, 47]

NEGATIVE = (
    # forbidden on everyone
    "bindi, sindoor, forehead dot, red dot on forehead, tilak, kumkum, red hair parting, mangalsutra, "
    "bridal jewellery, heavy jewellery, nose ring, maang tikka, bridal makeup, wedding dress, lehenga, "
    # quality
    "text, letters, words, watermark, logo, caption, signature, numbers, cartoon, anime, illustration, 3d render, "
    "cgi, painting, doll, plastic skin, airbrushed, waxy skin, deformed face, asymmetrical eyes, cross-eyed, "
    "extra fingers, fused fingers, missing fingers, mutated hands, bad hands, extra limbs, extra arms, "
    "melted clothes, torn clothes, malformed clothing, duplicate person, twins, same face, blurry, lowres, "
    "jpeg artifacts, oversaturated, overexposed, bollywood actor, celebrity, beauty filter, nsfw, "
    # body parts must be whole and clean
    "blurry face, blurry eyes, merged eyes, missing eye, distorted nose, missing nose, melted face, "
    "deformed hands, missing hand, extra hand, fused bodies, merged people, cut off head, cut off feet, "
    "extra legs, missing legs, long neck, bad anatomy, disfigured, poorly drawn face, ugly, unattractive"
)

# ---- Class look: Normal / Middle / High class -> kapde, jagah, background alag ----
CLASS_LOOK = {
    "Normal": dict(
        tone="simple everyday",
        f=["a cotton salwar suit with dupatta", "a printed cotton saree", "a simple kurti with leggings",
           "a plain kurta with jeans", "a bandhani print suit", "a cotton anarkali"],
        m=["a checked shirt and trousers", "a plain t-shirt and jeans", "a cotton kurta pyjama",
           "a half-sleeve shirt and jeans", "a simple formal shirt"],
        places=["a small-town street with pastel walls", "a village courtyard with neem tree", "a terrace with water tank",
                "a local temple steps (no religious marks on people)", "a mustard field", "a home courtyard with plants",
                "a small park with benches", "a home doorway with colourful walls"]),
    "Middle class": dict(
        tone="neat well-dressed middle-class",
        f=["a well-fitted chikankari kurta with palazzo", "a georgette saree neatly draped", "a long anarkali kurta",
           "a straight kurti with jeans and stole", "a smart top and jeans", "a pastel suit with organza dupatta"],
        m=["a pressed formal shirt and trousers", "a polo t-shirt and chinos", "a linen kurta and jeans",
           "a denim shirt and chinos", "a nehru jacket over a kurta"],
        places=["a home balcony with plants", "a cafe corner by a window", "a city park with trees", "a college campus lawn",
                "a living room with warm lamps", "a lakeside walkway", "a society garden", "a mall corridor, softly blurred"]),
    "High class": dict(
        tone="elegant affluent, premium styling",
        f=["an elegant designer silk saree", "a designer embroidered suit", "a chic western dress with blazer",
           "a stylish indo-western kurta set", "a satin co-ord set", "a luxury pastel lehenga-style skirt and blouse"],
        m=["a tailored navy suit", "a designer bandhgala", "a crisp white shirt with blazer", "a luxury sherwani-style kurta",
           "a smart casual blazer and turtleneck"],
        places=["a luxury hotel lobby", "a rooftop lounge at golden hour", "a modern villa garden", "a fine-dining restaurant",
                "a marble-floored hall with chandelier", "a heritage palace courtyard", "a luxury car showroom, blurred",
                "a resort poolside, softly blurred"]),
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
    clean = ", clean bare forehead, natural light makeup, tasteful small earrings" if f else ", well-groomed"
    return (f"attractive good-looking {draw(REGION)} Indian {gender} {ident}, {hair}{clean}, wearing {outfit}", ident)


def _job(scene: str, ident_a: str, ident_b: str | None, face: str, full: bool = False) -> dict:
    neg = NEGATIVE + (", close-up, half body, cropped legs, cut off at knees, out of frame" if full else "")
    return {"scene": scene, "ident_a": ident_a, "ident_b": ident_b, "face": face, "neg": neg}


FULL = ("full-length wide shot, the ENTIRE body visible from the top of the head down to the shoes, feet and shoes "
        "clearly visible on the ground, camera 4 meters away, subject small enough to fit fully in frame with space around")
HALF = "medium shot, framed from the waist up, both hands relaxed"


def build_image_prompt(category: str, subject: str, full: bool, extra: str, cls: str = "Mix") -> dict:
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
               f"with a few grey hairs, clean bare forehead, wearing {draw(OLD_SAREE)}")
        face, g = ident, "woman"
        pose = "standing side by side, smiling at camera"
    else:
        s_, ident = person("man", am, lk)
        who = (f"{s_}, with his elderly mother, a {am + random.randint(25, 30)}-year-old graceful Indian woman "
               f"with grey hair, clean bare forehead, wearing {draw(OLD_SAREE)}")
        face, g = ident, "man"
        pose = "standing side by side, both smiling"
    if full:
        pose = pose.replace("seated on a chair, ", "standing, ").replace("sitting on steps, hands on knees", "standing on steps")
    composition = (FULL + ". " if full else HALF + ". ")
    if subject == "Female":
        composition += "Portrait framing: keep her entire head, hairline, and chin inside the image, with space above her head. Both eyes open, naturally aligned, sharp and clear, looking near the camera. Face is unobstructed, centered, and fills about one third of a portrait frame. "
    scene = " ".join(p for p in [
        composition + f"RAW photo of {who}.",
        f"{pose}. {draw(ANGLES)}, {FULL if full else HALF}. Location: {draw(lk['places'])}, {draw(LIGHT)}.",
        f"{lk['tone']} look, beautiful attractive natural people, clothes neatly worn, faces sharp and clear.",
        "Canon EOS R5, 50mm f/2.8, sharp eyes, detailed natural skin texture, real photograph.",
        extra.strip()[:300],
    ] if p)
    ident_b = _identity(g, af if g == "woman" else am) if g else None
    return _job(scene, ident or "", ident_b, f"RAW close-up photo of an attractive Indian {g or 'person'}, {face}, "
                "detailed natural skin, sharp clear eyes, beautiful", full)


def build_portrait_prompt(gender: str, age: int, community: str, state: str, remarriage: bool,
                          full: bool = False, cls: str = "Mix") -> dict:
    g = "woman" if gender == "Female" else "man"
    lk = look(cls)
    desc, ident = person(g, age, lk)
    portrait_neg = NEGATIVE + (", closed eyes, missing eye, extra eye, merged eyes, cross-eyed, asymmetrical eyes, "
                               "looking away, head cropped, hair cropped, forehead cut off, chin cut off, blurred face")
    if full:
        scene = (f"{FULL}. RAW photo of {desc}, from {state}, standing, arms relaxed. {random.choice(ANGLES)}. "
                 f"Location: {draw(lk['places'])}, {random.choice(LIGHT)}. {lk['tone']} look. "
                 "Keep the entire head including hairline and chin inside frame, with space above the head. Both eyes are open, aligned, sharp and unobstructed. Face is clearly visible and in focus. "
                 "Canon EOS R5 50mm, sharp eyes, detailed natural skin, real photograph.")
        return {**_job(scene, ident, _identity(g, age), f"RAW close-up photo of an attractive Indian {g}, {ident}, both eyes open and aligned, sharp clear eyes", True), "neg": portrait_neg + ", close-up, half body, cropped legs, cut off at knees, out of frame"}
    bg = draw(["plain softly lit home wall", "blurred garden", "simple grey studio backdrop", "balcony with plants, blurred",
               "living room with curtains, blurred", "office lobby, blurred", "terrace at sunset, blurred"])
    framing = "medium close portrait, from upper chest to above hair, full head and chin visible, comfortable space above head, centered composition" 
    scene = (f"RAW amateur matrimonial profile photo, {framing} of {desc}, from {state}. "
            f"{random.choice(['gentle smile facing camera', 'soft smile, head slightly tilted', 'calm confident look', 'warm natural smile'])}, "
            f"{random.choice(['straight-on eye-level portrait', 'slight three-quarter view, both eyes visible'])}, chest-up framing, hands out of frame. Both eyes open, naturally aligned, clear and sharp, looking toward camera; both eyebrows, nose, mouth, hairline, and chin complete and unobstructed. Face is the sharp focal point, not cropped. Background: {bg}. {random.choice(LIGHT)}. "
            "Indian matrimonial profile photo, Canon EOS R5 85mm f/2.0, sharp eyes, real skin texture with pores, realistic Indian features, balanced natural face, unretouched, authentic everyday woman, not a beauty model.")
    return {**_job(scene, ident, _identity(g, age), f"RAW close-up photo of an ordinary Indian {g}, {ident}, both eyes open and aligned, clear sharp eyes, full hairline and chin visible, "
                "real skin texture with pores, unretouched"), "neg": portrait_neg}
