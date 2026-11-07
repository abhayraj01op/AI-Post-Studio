"""Image prompts: real-looking Indian rishta photos, every face different, never any text.

Important: SDXL does NOT understand "no X" in the positive prompt — writing "no sindoor"
actually ADDS sindoor. So forbidden things (bindi, sindoor, mangalsutra...) live ONLY in NEGATIVE.
"""
import random

# Face identity is built from many independent traits -> thousands of different faces.
FACE_SHAPE = ["oval face", "round face", "square jaw", "heart-shaped face", "long narrow face", "diamond face"]
SKIN = ["wheatish skin", "dusky brown skin", "light brown skin", "fair skin", "deep brown skin", "olive skin"]
EYES = ["big expressive eyes", "small almond eyes", "deep-set eyes", "hooded eyes", "slightly droopy eyes"]
NOSE = ["sharp nose", "broad nose", "small button nose", "long straight nose", "slightly hooked nose"]
MARKS = ["a small mole on the cheek", "light freckles", "dimples", "a slightly crooked smile", "thick eyebrows",
         "thin eyebrows", "faint acne marks", "laugh lines", "a gap in the front teeth", ""]
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
             "a fitted designer kurti", "a printed cotton kurta with leggings", "an elegant georgette saree",
             "a short kurti with dupatta on one shoulder"]
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
    "jpeg artifacts, oversaturated, overexposed, fashion model, supermodel, bollywood actor, celebrity, "
    "beauty filter, nsfw, nude, cleavage, "
    # v6: wrong ethnicity / wrong clothes seen in user photos
    "african, african american, black woman, latina, hispanic, caucasian, european, east asian, western woman, "
    "hoodie, hood, hood over head, headscarf, hijab, burqa, head covered, dupatta on head, jacket, coat, pregnant, belly, "
    # v6: eyes + framing
    "lazy eye, mismatched eyes, uneven eyes, different eye sizes, squint, strabismus, wonky eyes, dead eyes, "
    "blurry eyes, extreme close-up, cropped head, forehead cut off, face cut off, motion blur, out of focus, grainy"
)

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
WEIGHT = ["very slim with a thin face", "slim", "average weight", "slightly chubby with full cheeks",
          "chubby with a double chin", "heavy-set with a round fleshy face"]
JAW = ["narrow pointed chin", "wide square jaw", "soft rounded jaw", "receding chin", "prominent chin", "broad cheekbones"]
LIPS = ["thin lips", "full lips", "wide mouth", "small mouth", "uneven lips"]
FOREHEAD = ["broad forehead", "small forehead", "high forehead", "low hairline"]
EARS = ["slightly big ears", "small ears", "ears sticking out a little", ""]
GLASSES = ["thin metal-frame spectacles", "black rectangular spectacles", "", "", "", "", ""]
BEARD = ["full black beard", "short stubble", "thick moustache, no beard", "clean-shaven", "goatee",
         "salt-and-pepper stubble", "light patchy beard"]
TONE_W = [1.15, 1.2, 1.25, 1.3]


# v6: pleasant, clearly North/Central-Indian female traits (no odd features that made faces ugly/foreign)
F_WEIGHT = ["slim", "slim", "average weight", "slightly curvy", "petite"]
F_FACE = ["oval face", "soft round face", "heart-shaped face", "long oval face"]
F_SKIN = ["wheatish Indian skin", "light brown Indian skin", "fair wheatish skin", "warm medium-brown Indian skin"]
F_EYES = ["big dark brown eyes with kajal", "almond-shaped dark eyes", "large expressive brown eyes", "soft dark eyes"]
F_NOSE = ["small straight nose", "sharp straight nose", "small rounded nose"]
F_LIPS = ["full lips", "soft natural lips", "medium lips with a gentle smile"]
F_MARKS = ["a small mole on the cheek", "dimples", "light freckles", "", "", ""]
LOOKS = {
    "Simple": "simple homely look, minimal makeup",
    "Attractive": "attractive pretty look, light makeup, kajal, soft pink lipstick, well-groomed glossy hair",
    "Bold": "bold confident glamorous look, smoky kajal eyes, bold lipstick, styled open hair, stylish fitted outfit, confident gaze",
}
INDIAN_F = "(beautiful Indian woman, desi South Asian face, Indian features, black hair:1.3)"
INDIAN_M = "(handsome Indian man, desi South Asian face, Indian features, black hair:1.3)"


def _identity(gender: str, age: int) -> str:
    """Short, weighted, front-loaded identity text (SDXL reads the first ~75 tokens best)."""
    f = gender == "woman"
    if f:
        bits = [f"{age} years old", draw(F_WEIGHT), draw(F_FACE), draw(F_SKIN), draw(F_EYES), draw(F_NOSE),
                draw(F_LIPS), draw(F_MARKS), random.choice(GLASSES)]
        bits = [b for b in bits if b]
        return f"({', '.join(bits)}:1.15)"
    bits = [f"{age} years old", draw(WEIGHT), draw(FACE_SHAPE), draw(JAW), draw(SKIN), draw(EYES), draw(NOSE),
            draw(LIPS), draw(FOREHEAD), draw(MARKS), draw(EARS), random.choice(GLASSES)]
    if not f:
        bits.append(draw(BEARD))
    bits = [b for b in bits if b]
    return f"({', '.join(bits)}:{random.choice(TONE_W)})"


def person(gender: str, age: int, look: str = "Attractive") -> tuple[str, str]:
    """Returns (scene text for this person, identity text used for face mixing + face fix)."""
    f = gender == "woman"
    ident = f"{INDIAN_F if f else INDIAN_M}, {_identity(gender, age)}"
    hair = draw(HAIR_F if f else HAIR_M)
    outfit = draw(OUTFITS_F if f else OUTFITS_M)
    lk = LOOKS.get(look, LOOKS["Attractive"])
    clean = f", {lk}, hair uncovered, clean forehead, small stud earrings" if f else ""
    return (f"{draw(REGION)} Indian {gender} {ident}, {hair}{clean}, wearing {outfit}", ident)


def _job(scene: str, ident_a: str, ident_b: str | None, face: str) -> dict:
    return {"scene": scene, "ident_a": ident_a, "ident_b": ident_b, "face": face}


def build_image_prompt(category: str, subject: str, full: bool, extra: str, look: str = "Attractive") -> dict:
    """Returns a job dict for comfy.generate: scene prompt + two identities that get blended
    at a random ratio -> a brand-new face every time (fixes 'sab mein same face')."""
    re_ = category == "Remarriage"
    af = random.choice(AGES_RE if re_ else AGES_YOUNG)
    am = random.choice(AGES_RE if re_ else AGES_YOUNG)
    pose = draw(POSES)
    g = None
    if subject == "Couple":
        (w, wi), (m, mi) = person("woman", af, look), person("man", am)
        who, ident, face = f"a couple: {w}; and {m}", None, f"{wi}, {mi}"
        pose = draw(COUPLE_POSES)
    elif subject in ("Female", "Male"):
        g = "woman" if subject == "Female" else "man"
        who, ident = person(g, af if g == "woman" else am, look)
        face = ident
    elif subject == "BetiMaa":
        d, ident = person("woman", af, look)
        who = (f"{d}, standing with her mother, a {random.choice([50, 53, 56])}-year-old Indian woman "
               f"with a few grey hairs, clean bare forehead, wearing {draw(OLD_SAREE)}")
        face, g = ident, "woman"
        pose = "standing side by side, smiling at camera"
    else:
        s, ident = person("man", am)
        who = (f"{s}, with his elderly mother, a {random.choice([62, 66, 70])}-year-old Indian woman "
               f"with grey hair, clean bare forehead, wearing {draw(OLD_SAREE)}")
        face, g = ident, "man"
        pose = "standing side by side, both smiling"
    framing = "full-body shot, head to feet visible" if full else "medium shot, framed from the waist up"
    scene = " ".join(p for p in [
        f"Professional DSLR photo of {who}.",
        f"{pose}. {draw(ANGLES)}, {framing}. {draw(PLACES)}, {draw(LIGHT)}.",
        "Decent rishta family photo, clothes neatly worn, faces in the middle of the frame.",
        "Canon EOS R5, 85mm f/2.0, tack sharp focus on face, symmetrical well-defined eyes looking at camera, detailed iris, natural skin texture, high detail, 8k.",
        extra.strip()[:300],
    ] if p)
    # second, unrelated identity of the same gender/age to blend with (only for single-person faces)
    ident_b = _identity(g, af if g == "woman" else am) if g else None
    return _job(scene, ident or "", ident_b, f"RAW close-up photo of an ordinary Indian {g or 'person'}, {face}, "
                "detailed symmetrical eyes, sharp iris, natural skin texture, beautiful face")


def build_portrait_prompt(gender: str, age: int, community: str, state: str, remarriage: bool, look: str = "Attractive") -> dict:
    g = "woman" if gender == "Female" else "man"
    desc, ident = person(g, age, look)
    bg = draw(["plain softly lit home wall", "blurred garden", "simple grey studio backdrop", "balcony with plants, blurred",
               "living room with curtains, blurred", "office lobby, blurred", "terrace at sunset, blurred"])
    scene = (f"Professional DSLR portrait photo of {desc}, from {state}. "
            f"{random.choice(['gentle smile facing camera', 'soft smile, head slightly tilted', 'calm confident look', 'warm natural smile'])}, "
            "eye-level shot, medium shot from waist up, whole head and hair visible with empty space above the head, face in upper-middle of frame, "
            f"hands out of frame. Background: {bg}. {random.choice(LIGHT)}. "
            "Canon EOS R5 85mm f/2.0, tack sharp focus on face, symmetrical well-defined eyes looking at camera, detailed iris, natural skin texture, high detail.")
    return _job(scene, ident, _identity(g, age), f"RAW close-up photo of an ordinary Indian {g}, {ident}, "
                "detailed symmetrical eyes, sharp iris, natural skin texture, beautiful face")
