"""Image prompts: real-looking Indian rishta photos, varied poses/backgrounds, never any text."""
import random

FACES = [
    "oval face with a slightly sharp nose", "round face with soft cheeks", "square jaw and thick eyebrows",
    "heart-shaped face with a small chin", "long face with high cheekbones", "wheatish skin with light freckles",
    "dusky skin and deep-set eyes", "fair skin with a tiny mole near the lip", "medium brown skin and dimples",
    "slightly asymmetrical smile and broad nose", "almond eyes and a narrow nose", "wide forehead and thin lips",
]
POSES = [
    "classic matrimonial profile pose, standing straight facing camera with a soft smile",
    "seated on a chair, hands in lap, looking at camera", "standing beside a pillar, one hand resting on it",
    "standing with body slightly turned, face to camera", "sitting on a sofa edge, relaxed smile",
    "laughing naturally while looking slightly away", "leaning on a wall with arms relaxed",
    "walking mid-step, candid", "sitting on steps, elbows on knees", "adjusting dupatta or sleeve, caught mid-moment",
    "standing with hands folded, gentle smile", "looking over the shoulder", "holding a cup of chai",
    "resting chin on hand", "turning head towards camera, soft expression",
]
ANGLES = [
    "eye-level shot", "slightly low angle", "slightly high angle", "three-quarter view from the left",
    "three-quarter view from the right", "side angle", "over-the-shoulder framing",
]
PLACES = [
    "a leafy park in an Indian city", "a rooftop terrace at golden hour", "an old haveli courtyard",
    "a busy local market with soft bokeh", "a home balcony with plants", "a small-town street with pastel walls",
    "a cafe corner by a window", "a temple-side ghat at morning", "a mustard field in Punjab",
    "a college campus lawn", "a living room with warm lamps", "a photo studio with a soft grey backdrop",
    "a garden with flowering bushes", "a marble-floored hall with curtains", "a front gate of a family home",
    "a lakeside walkway", "a staircase in an old building", "a terrace with a city skyline behind",
]
LIGHT = ["soft morning daylight", "warm golden-hour sunlight", "overcast diffused light",
         "window light from the side", "open shade on a sunny day"]
OUTFITS_F = ["cotton salwar suit", "simple pastel saree", "kurti with jeans", "anarkali kurta",
             "plain chikankari kurta", "casual top and jeans"]
OUTFITS_M = ["linen kurta", "formal shirt", "casual polo t-shirt", "denim shirt", "nehru jacket over kurta", "checked shirt"]
AGES_YOUNG = [28, 29, 30, 31, 32, 33]
AGES_RE = [35, 37, 39, 41, 43, 45]

NEGATIVE = (
    "text, letters, words, watermark, logo, caption, signature, numbers, cartoon, anime, illustration, 3d render, "
    "cgi, painting, plastic skin, airbrushed, deformed face, extra fingers, bad hands, extra limbs, blurry, "
    "lowres, oversaturated, model look, nsfw"
)

_decks: dict[int, list] = {}


def draw(a: list):
    """Cycles through a shuffled list so poses/backgrounds don't repeat until all are used."""
    d = _decks.get(id(a))
    if not d:
        d = a[:]
        random.shuffle(d)
        _decks[id(a)] = d
    return d.pop()


def person(gender: str, age: int) -> str:
    outfit = random.choice(OUTFITS_F if gender == "woman" else OUTFITS_M)
    return f"a {age}-year-old Indian {gender} with {draw(FACES)}, wearing a {outfit}"


def unmarried_rule(remarriage: bool) -> str:
    return ("simple modest look, no bridal jewellery" if remarriage else
            "unmarried woman, no sindoor, no mangalsutra, no bridal jewellery, only small simple earrings")


def build_image_prompt(category: str, subject: str, full: bool, extra: str) -> str:
    re = category == "Remarriage"
    af = random.choice(AGES_RE if re else AGES_YOUNG)
    am = random.choice(AGES_RE if re else AGES_YOUNG)
    if subject == "Couple":
        who = f"{person('woman', af)}, together with {person('man', am)}, a couple standing close and comfortable"
    elif subject == "Female":
        who = person("woman", af)
    elif subject == "Male":
        who = person("man", am)
    elif subject == "BetiMaa":
        who = f"{person('woman', af)} standing with her mother, a {random.choice([48, 52, 55])}-year-old Indian woman in a simple cotton saree, warm bond"
    else:
        who = f"{person('man', am)} with his elderly mother, a {random.choice([62, 66, 70])}-year-old Indian woman with grey hair in a plain saree, caring bond"
    framing = "full-body shot, head to feet visible" if full else "half-body shot, framed from the waist up"
    parts = [
        f"RAW photo, photorealistic candid photograph of {who}.",
        f"Pose: {draw(POSES)}. {draw(ANGLES)}, {framing}.",
        f"Location: {draw(PLACES)}. Lighting: {draw(LIGHT)}.",
        f"neat decent photo Indian families share for {category.lower()} rishta proposals.",
        "faces in the vertical middle of the frame, plain sky or wall at the top and floor at the bottom.",
        unmarried_rule(re) if subject != "Male" else "",
        "shot on full-frame DSLR, 85mm lens, f/1.8, natural skin texture with visible pores, real everyday people.",
        extra.strip()[:300],
    ]
    return " ".join(p for p in parts if p)


def build_portrait_prompt(gender: str, age: int, community: str, state: str, remarriage: bool) -> str:
    g = "woman" if gender == "Female" else "man"
    bg = draw(["plain softly lit home wall", "blurred garden", "simple grey studio backdrop", "balcony with plants, blurred",
               "living room with curtains, blurred", "temple courtyard, blurred", "office lobby, blurred", "terrace at sunset, blurred"])
    rule = unmarried_rule(remarriage) if g == "woman" else ""
    return (f"RAW photo, photorealistic portrait of {person(g, age)}, from {state}, {community} family. "
            f"{random.choice(['gentle smile facing camera', 'soft smile, head slightly tilted', 'calm confident look', 'warm natural smile'])}, "
            f"{random.choice(ANGLES)}, chest-up framing. Background: {bg}. {random.choice(LIGHT)}. {rule}. "
            "DSLR 85mm, natural skin texture, real everyday person, not a model.")
