"""AI Post Studio (Colab + ComfyUI edition). UI text in Hinglish.
Run:  python -m app.main   (the notebook does this for you)"""
import random
import time
import zipfile

import gradio as gr
from PIL import Image

from . import comfy, enhance, names, storage, textgen, tools
from .config import (ALL_STATES_LABEL, BIO_TYPES, BIODATA_DIR, CATEGORIES, CLASSES, COMMUNITIES, DATA, DEFAULT_SUBJECT, IMAGES_DIR,
                     LANGS, MARITAL,
                     POST_TYPES, POSTS_DIR, SIZES, STATE_WEIGHTS, STATES, SUBJECTS, ensure_dirs)
from .prompts import build_image_prompt, build_portrait_prompt
from . import render
from .render import fit_cover, fit_photo, render_biodata, render_post

ensure_dirs()


def red(msg: str) -> str:
    return f"<p style='color:#b91c1c;font-weight:600'>{msg}</p>" if msg else ""


def ok(msg: str) -> str:
    return f"<p style='color:#7a1f1a;font-weight:600'>{msg}</p>"


def add_public_demo_note(caption: str) -> str:
    """Disclosure is kept in the social caption only, never drawn on the image."""
    note = "यह एक डेमो डेटा पर आधारित उदाहरण है। वास्तविक रिश्तों के लिए कमेंट करें।"
    caption = (caption or "").strip()
    if note not in caption:
        caption = f"{caption}\n\n{note}" if caption else note
    return caption


def generate_with_retry(prompt, width: int, height: int, attempts: int = 2):
    """Retry one transient ComfyUI failure; never loop endlessly on a stopped server."""
    last = None
    for attempt in range(attempts):
        try:
            return comfy.generate(prompt, width, height)
        except Exception as exc:
            last = exc
            msg = str(exc).lower()
            if "comfyui chal nahi raha" in msg or "connection refused" in msg:
                raise
            if attempt + 1 < attempts:
                try:
                    comfy.free_memory()
                except Exception:
                    pass
                time.sleep(2)
    raise last


def log_error(area: str, exc: Exception) -> None:
    from .config import DATA
    DATA.mkdir(parents=True, exist_ok=True)
    with (DATA / "error_logs.txt").open("a", encoding="utf-8") as f:
        f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {area}: {type(exc).__name__}: {exc}\n")


def pick_state() -> str:
    items = list(STATE_WEIGHTS.items())
    return random.choices([s for s, _ in items], weights=[w for _, w in items])[0]


def biodata_button_label(count) -> str:
    """Keep the generation action label aligned with the selected profile count."""
    return f"{max(1, int(count))} biodata banao"


# ---------------- Images ----------------
def image_gallery():
    db = storage.load()
    return [(i["path"], f"{i['id']} • {i['category']} • {i['subject']}") for i in db["images"]]


def image_ids():
    return [i["id"] for i in storage.load()["images"]]


def _cls(c):
    return c if c in ("Normal", "Middle class", "High class", "Bold") else "Mix"


def stop_all():
    comfy.interrupt()
    return "⏹ Rok diya gaya. Jo ban chuke the woh save hain."


def make_images(category, subject_label, count, photo, size, extra, cls="Mix"):
    subject = next(k for k, v in SUBJECTS.items() if v == subject_label)
    w, h, gw, gh = SIZES[size]
    done = failed = 0
    err = ""
    count = int(count)
    saved_guidance = storage.load()["settings"]
    for n in range(count):  # strictly one at a time
        yield f"Ban rahi hain {done}/{count}…", red(err), image_gallery()
        try:
            full = photo == "Full photo"
            if full and gh <= gw:  # square: full body ke liye lambi photo banao, phir bina kaate fit
                gw, gh = 896, 1152
            img = generate_with_retry(build_image_prompt(category, subject, full, extra or "", _cls(cls),
                                                          saved_guidance.get("image_reference", ""),
                                                          saved_guidance.get("image_avoid", "")), gw, gh)
            img = fit_photo(img, w, h, full)
            iid = storage.uid()
            path = IMAGES_DIR / f"{iid}.jpg"
            img.save(path, quality=93)
            storage.update(lambda d: d["images"].insert(0, {
                "id": iid, "path": str(path), "w": w, "h": h, "category": category, "subject": subject,
                "source": "ai", "photo_type": photo, "at": time.time()}))
            done += 1
        except Exception as e:
            log_error("image_generation", e)
            failed += 1
            err = f"Image fail hui: {e}"
            if "chal nahi raha" in str(e):
                break  # stop batch on fatal error
    yield f"Ho gaya {done}/{count}" + (f" • {failed} fail" if failed else ""), red(err), image_gallery()


def upload_images(files, size):
    w, h, *_ = SIZES[size]
    for f in files or []:
        img = fit_cover(Image.open(f.name if hasattr(f, "name") else f).convert("RGB"), w, h)
        iid = storage.uid()
        path = IMAGES_DIR / f"{iid}.jpg"
        img.save(path, quality=93)
        storage.update(lambda d: d["images"].insert(0, {
            "id": iid, "path": str(path), "w": w, "h": h, "category": "Upload", "subject": "Unknown",
            "source": "upload", "photo_type": "Half photo", "at": time.time()}))
    return image_gallery(), gr.update(choices=image_ids())


def delete_image(iid):
    def f(d):
        d["images"] = [i for i in d["images"] if i["id"] != iid]
        d["posts"].pop(iid, None)
    storage.update(f)
    return image_gallery(), gr.update(choices=image_ids(), value=None)


# ---------------- Posts ----------------
def save_settings(post_type_label, instruction, brand_on, brand_name, footer, fmt, lang=LANGS[0]):
    pt = next(k for k, v in POST_TYPES.items() if v == post_type_label)

    def f(d):
        d["settings"].update(post_type=pt, instruction=instruction or "", brand_on=bool(brand_on),
                             brand_name=(brand_name or "").strip(), footer=footer or "", format=fmt, lang=lang)
    storage.update(f)


def post_gallery():
    db = storage.load()
    return [(p["rendered"], f"{iid}\n{p['headline']}") for iid, p in db["posts"].items() if p.get("rendered")]


def brand_of(s, key="brand_on") -> str:
    """Brand sirf tab jab tick ON ho AUR naam likha ho. Khali = kahin bhi brand nahi."""
    return (s.get("brand_name") or "").strip() if s.get(key) else ""


def make_one_post(img_rec, s):
    db = storage.load()
    brand = brand_of(s)
    t = textgen.post_text(s["post_type"], s["instruction"], img_rec["category"], img_rec["subject"], db["headlines"],
                          brand, s.get("lang", LANGS[0]))
    t["caption"] = add_public_demo_note(t.get("caption", ""))
    storage.push_headline(t["headline"])
    out = render_post(Image.open(img_rec["path"]), t["headline"], t["cta"], bool(brand_of(s)), brand_of(s), s["footer"])
    ext = "jpg" if s["format"] == "jpg" else "png"
    path = POSTS_DIR / f"{img_rec['id']}.{ext}"
    out.save(path, quality=93)
    (POSTS_DIR / f"{img_rec['id']}.txt").write_text(f"{t['caption']}\n\n{t['hashtags']}", "utf-8")
    t["rendered"] = str(path)
    storage.update(lambda d: d["posts"].__setitem__(img_rec["id"], t))


def make_posts(only_new, *settings):
    save_settings(*settings)
    db = storage.load()
    s = db["settings"]
    todo = [i for i in db["images"] if not (only_new and i["id"] in db["posts"])]
    err = ""
    for n, rec in enumerate(todo):  # one at a time
        yield f"Post ban rahe hain {n}/{len(todo)}…", red(err), post_gallery()
        try:
            make_one_post(rec, s)
        except Exception as e:
            log_error("post_generation", e)
            err = f"Post fail: {e}"
    yield f"Ho gaya {len(todo)} post", red(err), post_gallery()


def edit_post(iid, headline, cta, caption, hashtags):
    caption = add_public_demo_note(caption)
    db = storage.load()
    rec = next((i for i in db["images"] if i["id"] == iid), None)
    if not rec:
        return red("Pehle image ID chunein"), post_gallery()
    s = db["settings"]
    t = {"headline": headline, "cta": cta, "caption": caption, "hashtags": hashtags}
    out = render_post(Image.open(rec["path"]), headline, cta, bool(brand_of(s)), brand_of(s), s["footer"])
    path = POSTS_DIR / f"{iid}.{'jpg' if s['format'] == 'jpg' else 'png'}"
    out.save(path, quality=93)
    (POSTS_DIR / f"{iid}.txt").write_text(f"{caption}\n\n{hashtags}", "utf-8")
    t["rendered"] = str(path)
    storage.update(lambda d: d["posts"].__setitem__(iid, t))
    storage.push_headline(headline)
    return ok("Image par add ho gaya"), post_gallery()


def regen_field(field, iid, headline, cta, caption, hashtags):
    """Sirf ek line (headline/CTA/caption/hashtags) dobara likho."""
    db = storage.load()
    rec = next((i for i in db["images"] if i["id"] == iid), None)
    s = db["settings"]
    cur = {"headline": headline, "cta": cta, "caption": caption, "hashtags": hashtags}
    cat, sub = (rec["category"], rec["subject"]) if rec else ("Marriage", "Couple")
    cur[field] = textgen.post_field(field, s["post_type"], s["instruction"], cat, sub, cur, brand_of(s), s.get("lang", LANGS[0]))
    return cur["headline"], cur["cta"], cur["caption"], cur["hashtags"]


def load_post(iid):
    p = storage.load()["posts"].get(iid or "", {})
    return p.get("headline", ""), p.get("cta", ""), p.get("caption", ""), p.get("hashtags", "")


def quick_make_posts(category="Marriage", subject_label=SUBJECTS[DEFAULT_SUBJECT], size="1080x1350 (Portrait)", cls="Mix (har baar alag)"):
    """One-click 10 fresh AI photos + finished social posts; no prompt entry required."""
    subject = next((k for k, v in SUBJECTS.items() if v == subject_label), DEFAULT_SUBJECT)
    w, h, gw, gh = SIZES.get(size, SIZES["1080x1350 (Portrait)"])
    done = failed = 0
    err = ""
    saved = storage.load()["settings"]
    for n in range(10):
        yield f"10 ready posts: {done}/10 complete • photo + text", red(err), image_gallery(), post_gallery()
        try:
            full = False
            prompt = build_image_prompt(category, subject, full, "", _cls(cls),
                                        saved.get("image_reference", ""), saved.get("image_avoid", ""))
            img = generate_with_retry(prompt, gw, gh)
            img = fit_photo(img, w, h, full)
            iid = storage.uid()
            ipath = IMAGES_DIR / f"{iid}.jpg"
            img.save(ipath, quality=94)
            rec = {"id": iid, "path": str(ipath), "w": w, "h": h, "category": category, "subject": subject,
                   "source": "ai", "photo_type": "Half photo", "at": time.time()}
            storage.update(lambda d, r=rec: d["images"].insert(0, r))
            make_one_post(rec, storage.load()["settings"])
            done += 1
        except Exception as exc:
            log_error("quick_post_batch", exc)
            failed += 1
            err = f"Post {n + 1} fail hua: {exc}"
            if any(x in str(exc).lower() for x in ("chal nahi raha", "connection refused", "timed out", "server")):
                break
    yield f"Quick batch complete: {done}/10 ready" + (f" • {failed} fail" if failed else ""), red(err), image_gallery(), post_gallery()


def images_and_posts(category, subject_label, count, photo, size, extra, cls, *settings):
    """One click: N images, then their posts."""
    before = set(image_ids())
    for status, e, gal in make_images(category, subject_label, count, photo, size, extra, cls):
        yield status, e, gal, post_gallery()
    save_settings(*settings)
    db = storage.load()
    new = [i for i in db["images"] if i["id"] not in before]
    for n, rec in enumerate(new):
        yield f"Post ban rahe hain {n}/{len(new)}…", "", image_gallery(), post_gallery()
        try:
            make_one_post(rec, db["settings"])
        except Exception as ex:
            yield f"Post fail", red(str(ex)), image_gallery(), post_gallery()
    yield f"Ho gaya: {len(new)} image + post", "", image_gallery(), post_gallery()


def zip_folder(folder, name):
    z = DATA / f"{name}_{time.strftime('%Y%m%d_%H%M')}.zip"
    with zipfile.ZipFile(z, "w") as zf:
        for p in folder.iterdir():
            zf.write(p, p.name)
    return str(z)


# ---------------- Biodata ----------------
def bio_gallery():
    return [(b["rendered"], f"{b['id']} • {b['details']['name_roman']}") for b in storage.load()["biodata"] if b.get("rendered")]


def bio_ids():
    return [b["id"] for b in storage.load()["biodata"]]


def make_one_bio(o, bid=None, existing_image_path=None, source_image_id=None):
    db = storage.load()
    used = names.prune(db["used_names"])
    blocked = lambda n: names.is_blocked(n, used)
    brand = brand_of(db["settings"], "bio_brand_on")
    det = textgen.biodata(o, names.recent(used), brand, blocked, db.get("used_bio_details", {}))
    det["caption"] = add_public_demo_note(det.get("caption", ""))
    det["lang"], det["photo_type"] = o.get("lang", LANGS[0]), o.get("photo_type", "Half photo")
    gender = "Female" if o["type"] in ("Gharjamai", "MaaAkeli") else o["gender"]
    full = det["photo_type"] == "Full photo"
    if existing_image_path:
        photo = render.load_existing_photo(existing_image_path)
    else:
        photo = generate_with_retry(build_portrait_prompt(gender, det["age"], o["community"], o["state"], o["type"] == "Remarriage",
                                                     full, o.get("cls", "Mix"), o.get("reference", ""),
                                                     o.get("avoid", "")), 832 if full else 896, 1216 if full else 1120)
    bid = bid or storage.uid()
    ppath = BIODATA_DIR / f"{bid}_photo.jpg"
    photo.save(ppath, quality=93)
    out = render_biodata(photo, det, bool(brand_of(db["settings"], "bio_brand_on")), brand_of(db["settings"], "bio_brand_on"))
    rpath = BIODATA_DIR / f"{bid}.png"
    out.save(rpath)
    (BIODATA_DIR / f"{bid}.txt").write_text(f"{det['caption']}\n\n{det['hashtags']}", "utf-8")

    def f(d):
        d["used_names"] = names.prune(d["used_names"]) + [{"name": det["name_roman"], "at": time.time()}]
        history = d.setdefault("used_bio_details", {"family": [], "expectations": []})
        for field in ("family", "expectations"):
            value = (det.get(field) or "").strip()
            if value and value not in history.setdefault(field, []):
                history[field] = (history[field] + [value])[-1000:]
        rec = {"id": bid, "photo": str(ppath), "details": det, "rendered": str(rpath), "opts": o,
               "source_image_id": source_image_id, "at": time.time()}
        d["biodata"] = [rec] + [b for b in d["biodata"] if b["id"] != bid]
    storage.update(f)


def make_biodata(btype, statuses, children, gender, state, community, full_name, letters, instruction, count, brand_on,
                 photo_type="Half photo", lang=LANGS[0], cls="Mix"):
    storage.update(lambda d: d["settings"].__setitem__("bio_brand_on", bool(brand_on)))
    err = ""
    count = int(count)
    for n in range(count):
        yield f"Biodata ban raha {n}/{count}…", red(err), bio_gallery()
        o = {"type": btype, "statuses": statuses or [], "children": children, "gender": gender,
             "state": pick_state() if state == ALL_STATES_LABEL else state,
             "community": random.choice(COMMUNITIES) if community == ALL_STATES_LABEL else community,
             "full_name": bool(full_name), "letters": (letters or "")[:10], "instruction": (instruction or "")[:500],
             "photo_type": random.choice(["Half photo", "Full photo"]) if photo_type == "Mix" else photo_type,
             "lang": lang, "cls": _cls(cls),
             "reference": storage.load()["settings"].get("image_reference", ""),
             "avoid": storage.load()["settings"].get("image_avoid", "")}
        try:
            make_one_bio(o)
        except Exception as e:
            log_error("biodata_generation", e)
            err = f"Biodata fail: {e}"
            if "chal nahi raha" in str(e):
                break
    yield f"Ho gaya {count}", red(err), bio_gallery()


def quick_make_biodata(btype="Marriage", statuses=None, children="Any", gender="Female", state=ALL_STATES_LABEL,
                       community=ALL_STATES_LABEL, brand_on=False, photo_type="Half photo", lang=LANGS[0], cls="Mix (har baar alag)"):
    """One-click batch of 10 fully fictional profiles with newly generated portraits."""
    yield from make_biodata(btype, statuses, children, gender, state, community, True, "", "", 10,
                            brand_on, photo_type, lang, cls)


def save_image_guidance(reference, avoid):
    def update_settings(data):
        data["settings"]["image_reference"] = (reference or "").strip()[:500]
        data["settings"]["image_avoid"] = (avoid or "").strip()[:500]
    storage.update(update_settings)
    return ok("Reference guidance Drive mein save ho gaya; naye images aur biodata mein use hoga.")


def select_bio_source(evt: gr.SelectData):
    images = storage.load()["images"]
    index = getattr(evt, "index", None)
    if isinstance(index, (tuple, list)):
        index = index[0] if index else None
    if not isinstance(index, int) or index < 0 or index >= len(images):
        return "", "Photo select nahi hui. Images tab ki gallery mein kisi photo par click karein."
    rec = images[index]
    return rec["id"], f"Selected photo: {rec['id']} • {rec.get('category', 'Image')} • {rec.get('subject', 'Unknown')}"


def make_biodata_from_image(image_id, btype, statuses, children, gender, state, community, full_name, letters, instruction,
                            brand_on, lang=LANGS[0], cls="Mix"):
    db = storage.load()
    rec = next((item for item in db["images"] if item["id"] == image_id), None)
    if not rec:
        return "", red("Pehle Images tab mein gallery se photo select karein."), bio_gallery()
    storage.update(lambda data: data["settings"].__setitem__("bio_brand_on", bool(brand_on)))
    settings = storage.load()["settings"]
    o = {"type": btype, "statuses": statuses or [], "children": children, "gender": gender,
         "state": pick_state() if state == ALL_STATES_LABEL else state,
         "community": random.choice(COMMUNITIES) if community == ALL_STATES_LABEL else community,
         "full_name": bool(full_name), "letters": (letters or "")[:10], "instruction": (instruction or "")[:500],
         "photo_type": rec.get("photo_type", "Half photo"), "lang": lang, "cls": _cls(cls),
         "reference": settings.get("image_reference", ""), "avoid": settings.get("image_avoid", "")}
    try:
        make_one_bio(o, existing_image_path=rec["path"], source_image_id=rec["id"])
        return "Biodata isi selected photo se ban gaya.", "", bio_gallery()
    except Exception as exc:
        return "", red(f"Biodata fail: {exc}"), bio_gallery()


def bio_edit(bid, name_hi, name_roman, age, height, education, job, city, state,
             marital_status, family, expectations):
    db = storage.load()
    b = next((x for x in db["biodata"] if x["id"] == bid), None)
    if not b:
        return red("ID chunein"), bio_gallery()
    det = b["details"]
    det.update({
        "name_hindi": name_hi or det.get("name_hindi", ""),
        "name_roman": name_roman or det.get("name_roman", ""),
        "age": max(18, min(80, int(age or det.get("age", 30)))),
        "height": height or det.get("height", ""),
        "education": education or det.get("education", ""),
        "job": job or det.get("job", ""),
        "city": city or det.get("city", ""),
        "state": state or det.get("state", ""),
        "marital_status": marital_status or det.get("marital_status", ""),
        "family": family or det.get("family", ""),
        "expectations": expectations or det.get("expectations", ""),
    })
    det["caption"] = add_public_demo_note(det.get("caption", ""))
    out = render_biodata(Image.open(b["photo"]), det, bool(brand_of(db["settings"], "bio_brand_on")),
                         brand_of(db["settings"], "bio_brand_on"))
    out.save(b["rendered"])
    (BIODATA_DIR / f"{bid}.txt").write_text(f"{det['caption']}\n\n{det['hashtags']}", "utf-8")
    storage.update(lambda d: [x.update(details=det) for x in d["biodata"] if x["id"] == bid])
    _remember_bio_copy(det)
    return ok("Saare biodata fields update ho gaye"), bio_gallery()

def _remember_bio_copy(details):
    def save_copy(data):
        history = data.setdefault("used_bio_details", {"family": [], "expectations": []})
        for field in ("family", "expectations"):
            value = (details.get(field) or "").strip()
            if value and value not in history.setdefault(field, []):
                history[field] = (history[field] + [value])[-1000:]
    storage.update(save_copy)


def bio_regen_field(field, bid):
    """Regenerate just one visible biodata detail while preserving all others."""
    allowed = {"name", "age", "height", "education", "job", "city", "status", "family", "expectations"}
    db = storage.load()
    b = next((item for item in db["biodata"] if item["id"] == bid), None)
    if not b:
        return (red("Pehle biodata ID chunein"), bio_gallery()) + bio_load(bid)
    if field not in allowed:
        return (red("Ye biodata field regenerate nahi ho sakta"), bio_gallery()) + bio_load(bid)
    details = dict(b["details"])
    used = names.prune(db.get("used_names", []))
    brand = brand_of(db["settings"], "bio_brand_on")
    blocked = lambda value: names.is_blocked(value, used)
    if field == "name":
        alternative = textgen.alternate_bio_value(field, str(details.get("name_roman", "")), b["opts"], details, blocked)
        if alternative is None:
            return (red("Naya naam available nahi hai; pehle naam ki shuruati chithi badlein"), bio_gallery()) + bio_load(bid)
        details["name_hindi"], details["name_roman"] = alternative
    elif field in ("family", "expectations"):
        details[field] = textgen.fresh_bio_phrase(field, db.get("used_bio_details", {}),
                                                   details.get("lang", "Hindi"), b["opts"].get("type", "Marriage"),
                                                   details.get(field, ""))
    else:
        key = {"status": "marital_status"}.get(field, field)
        alternative = textgen.alternate_bio_value(field, str(details.get(key, "")), b["opts"], details, blocked)
        if alternative is None:
            return (red("Is profile type ke liye is field ka doosra valid value nahi hai"), bio_gallery()) + bio_load(bid)
        if details.get("lang", "").startswith("Hinglish"):
            alternative = textgen.ROMAN.get(alternative, alternative)
            if field == "height":
                alternative = alternative.replace(" फुट ", " ft ").replace(" इंच", " in")
        details[key] = int(alternative) if field == "age" else alternative
    details["caption"] = add_public_demo_note(details.get("caption", ""))
    out = render_biodata(Image.open(b["photo"]), details, bool(brand_of(db["settings"], "bio_brand_on")),
                         brand_of(db["settings"], "bio_brand_on"))
    out.save(b["rendered"])
    (BIODATA_DIR / f"{bid}.txt").write_text(f"{details['caption']}\n\n{details['hashtags']}", "utf-8")
    def save_field(data):
        for item in data["biodata"]:
            if item["id"] == bid:
                item["details"] = details
        if field == "name":
            data["used_names"] = names.prune(data.get("used_names", [])) + [
                {"name": details["name_roman"], "at": time.time()}]
        history = data.setdefault("used_bio_details", {"family": [], "expectations": []})
        for key in ("family", "expectations"):
            value = (details.get(key) or "").strip()
            if value and value not in history.setdefault(key, []):
                history[key] = (history[key] + [value])[-1000:]
    storage.update(save_field)
    return (ok("Nayi line taiyaar"), bio_gallery()) + bio_load(bid)


def bio_regen(bid):
    db = storage.load()
    b = next((x for x in db["biodata"] if x["id"] == bid), None)
    if not b:
        return red("ID chunein"), bio_gallery()
    try:
        source = next((image for image in db["images"] if image["id"] == b.get("source_image_id")), None)
        existing_photo = source["path"] if source else (b["photo"] if b.get("source_image_id") else None)
        make_one_bio(b["opts"], bid, existing_image_path=existing_photo,
                     source_image_id=b.get("source_image_id"))
        return ok("Naya ban gaya"), bio_gallery()
    except Exception as e:
        return red(str(e)), bio_gallery()


def bio_load(bid):
    b = next((x for x in storage.load()["biodata"] if x["id"] == bid), None)
    if not b:
        return ("", None) + ("",) * 11
    d = b["details"]
    return (d.get("name_hindi", ""), d.get("name_roman", ""), d.get("age"), d.get("height", ""),
            d.get("education", ""), d.get("job", ""), d.get("city", ""), d.get("state", ""),
            d.get("marital_status", ""), d.get("family", ""), d.get("expectations", ""),
            d.get("caption", ""), d.get("hashtags", ""))

def _bio_set_text(bid, caption, hashtags):
    caption = add_public_demo_note(caption)
    def f(d):
        for x in d["biodata"]:
            if x["id"] == bid:
                x["details"]["caption"], x["details"]["hashtags"] = caption, hashtags
    storage.update(f)
    (BIODATA_DIR / f"{bid}.txt").write_text(f"{caption}\n\n{hashtags}", "utf-8")


def bio_save_text(bid, caption, hashtags):
    if not bid:
        return red("ID chunein")
    _bio_set_text(bid, caption, hashtags)
    return ok("Caption/hashtags save ho gaye")


def bio_regen_text(field, bid, caption, hashtags):
    """Sirf caption ya hashtags naye likho; baaki biodata wahi rahe."""
    db = storage.load()
    b = next((x for x in db["biodata"] if x["id"] == bid), None)
    if not b:
        return red("ID chunein"), caption, hashtags
    used = db.get("used_names", [])
    brand = brand_of(db["settings"], "bio_brand_on")
    old = caption if field == "caption" else hashtags
    new = old
    for _ in range(3):
        fresh = textgen.biodata(b["opts"], names.recent(used), brand, lambda n: names.is_blocked(n, used),
                                db.get("used_bio_details", {}))
        new = fresh.get(field, "") or old
        if field == "caption":
            nm = b["details"].get("name_hindi", "")
            new = new.replace(fresh.get("name_hindi", "") or "\0", nm) if nm else new
        if new and new != old:
            break
    if field == "caption":
        caption = add_public_demo_note(new)
    else:
        hashtags = new
    _bio_set_text(bid, caption, hashtags)
    return ok("Naya likh diya"), caption, hashtags


def bio_delete(bid):
    storage.update(lambda d: d.__setitem__("biodata", [x for x in d["biodata"] if x["id"] != bid]))
    return bio_gallery(), gr.update(choices=bio_ids(), value=None)


# ---------------- Enhance ----------------
def _enhance_failure(area, exc, completed, total, gallery_fn):
    log_error(area, exc)
    return red(f"Enhancement ruk gaya ({completed}/{total} complete). Asli wajah: {exc}"), gallery_fn()


def enhance_images(ids, level, all_items, method=enhance.AI_METHOD):
    db = storage.load()
    recs = [i for i in db["images"] if all_items or i["id"] in (ids or [])]
    if not recs:
        return red("Image ID chunein ya 'Sab' tick karein"), image_gallery()
    done = 0
    for r in recs:
        try:
            img, _how = enhance.smart_enhance(Image.open(r["path"]), level, (r["w"], r["h"]), method)
            img.save(r["path"], quality=95, subsampling=0)
            done += 1
        except Exception as exc:
            return _enhance_failure("enhance_images", exc, done, len(recs), image_gallery)
    return ok(f"{done} image enhance ho gayi • {_how}"), image_gallery()


def enhance_posts(ids, level, new_text, all_items, method=enhance.AI_METHOD):
    db = storage.load()
    s = db["settings"]
    recs = [i for i in db["images"] if i["id"] in db["posts"] and (all_items or i["id"] in (ids or []))]
    if not recs:
        return red("Jinka post bana ho, unke ID chunein"), post_gallery()
    done = 0
    for r in recs:
        try:
            img, _how = enhance.smart_enhance(Image.open(r["path"]), level, (r["w"], r["h"]), method)
            if new_text:
                img.save(r["path"], quality=95, subsampling=0)
                make_one_post(r, s)  # fresh, non-repeating headline/caption/hashtags
                done += 1
                continue
            t = storage.load()["posts"][r["id"]]
            out = render_post(img, t["headline"], t["cta"], bool(brand_of(s)), brand_of(s), s["footer"])
            img.save(r["path"], quality=95, subsampling=0)
            out.save(t["rendered"], quality=95, subsampling=0)
            done += 1
        except Exception as exc:
            return _enhance_failure("enhance_posts", exc, done, len(recs), post_gallery)
    return ok(f"{done} post enhance ho gaye • {_how}"), post_gallery()


def enhance_bios(ids, level, new_details, all_items, method=enhance.AI_METHOD, enhance_photo=True):
    db = storage.load()
    recs = [b for b in db["biodata"] if all_items or b["id"] in (ids or [])]
    if not recs:
        return red("Biodata ID chunein"), bio_gallery()
    if not enhance_photo and not new_details:
        return red("Photo enhance ya details regenerate mein se kam se kam ek chunein"), bio_gallery()
    done = 0
    how = "Photo unchanged"
    for b in recs:
        try:
            if enhance_photo:
                photo, how = enhance.smart_enhance(Image.open(b["photo"]), level, method=method)
            else:
                photo = Image.open(b["photo"]).convert("RGB")
            det = b["details"]
            if new_details:
                used = names.prune(storage.load()["used_names"])
                brand = brand_of(db["settings"], "bio_brand_on")
                fresh = textgen.biodata(b["opts"], names.recent(used), brand, lambda n: names.is_blocked(n, used),
                                db.get("used_bio_details", {}))
                keep = {k: det[k] for k in ("name_hindi", "name_roman", "age") if k in det}
                det = {**fresh, **keep, "lang": det.get("lang", LANGS[0]), "photo_type": det.get("photo_type", "Half photo")}  # same person, richer details
            out = render_biodata(photo, det, bool(brand_of(db["settings"], "bio_brand_on")), brand_of(db["settings"], "bio_brand_on"))
            (BIODATA_DIR / f"{b['id']}.txt").write_text(f"{det['caption']}\n\n{det['hashtags']}", "utf-8")
            if enhance_photo:
                photo.save(b["photo"], quality=95, subsampling=0)
            out.save(b["rendered"])

            def f(d, bid=b["id"], det=det):
                for x in d["biodata"]:
                    if x["id"] == bid:
                        x["details"] = det
            storage.update(f)
            if new_details:
                _remember_bio_copy(det)
            done += 1
        except Exception as exc:
            return _enhance_failure("enhance_biodata", exc, done, len(recs), bio_gallery)
    detail = how if enhance_photo else "photo same rakhi"
    return ok(f"{done} biodata enhance ho gaya • {detail}"), bio_gallery()


# ---------------- UI ----------------
CSS = """
.gradio-container{background:#fbf4e6;font-family:'Mukta',sans-serif;max-width:1600px!important;margin:0 auto}
h1,h2,h3{font-family:'Fraunces',serif;color:#7a1f1a}
.gradio-container h1{font-size:2.2rem!important}
.gradio-container .tab-nav{gap:8px;border-bottom:2px solid #ead8c6}
.gradio-container .tab-nav button{font-family:'Mukta',sans-serif;font-weight:700;border-radius:8px 8px 0 0}
.gradio-container .tab-nav button.selected{color:#7a1f1a!important;border-color:#7a1f1a!important}
.gradio-container .block,.gradio-container .form{border-color:#ead8c6!important}
.gradio-container input:focus,.gradio-container textarea:focus,.gradio-container button:focus-visible{border-color:#7a1f1a!important;box-shadow:0 0 0 2px #f2a51655!important}
.gradio-container button.primary{background:#7a1f1a!important;color:#fff!important;border:0!important}
.gradio-container button.primary:hover{background:#962d24!important}
.gradio-container .gallery-item{border-radius:6px;overflow:hidden}
.gradio-container .gallery-item img{object-fit:contain!important;background:#2b1a14}
@media(max-width:640px){.gradio-container{padding:10px!important}.gradio-container h1{font-size:1.75rem!important}.gradio-container .tab-nav{overflow-x:auto;flex-wrap:nowrap}.gradio-container .tab-nav button{white-space:nowrap}}
"""
HEAD = "<link href='https://fonts.googleapis.com/css2?family=Fraunces:wght@700&family=Mukta:wght@400;700&display=swap' rel='stylesheet'>"


def build():
    s = storage.load()["settings"]
    with gr.Blocks(title="AI Post Studio", css=CSS, head=HEAD) as ui:
        gr.Markdown("# AI Post Studio\nImages → Posts → Biodata. Sab kuch aapki Google Drive mein save hota hai.")
        with gr.Accordion("Post settings (brand, post type)", open=False):
            post_type = gr.Dropdown(list(POST_TYPES.values()), value=POST_TYPES[s["post_type"]], label="Post type")
            instruction = gr.Textbox(label="Apni baat (optional)", value=s["instruction"], max_lines=3)
            brand_on = gr.Checkbox(label="Brand name dikhaye", value=s["brand_on"])
            brand_name = gr.Textbox(label="Brand ka naam", value=s["brand_name"])
            footer = gr.Textbox(label="Footer (jaise WhatsApp number)", value=s["footer"])
            fmt = gr.Radio(["png", "jpg"], value=s["format"], label="Download format")
            plang = gr.Radio(LANGS, value=s.get("lang", LANGS[0]), label="Post ki bhasha")
            gr.Markdown("Brand naam **sirf tab** aayega jab tick ON ho aur naam likha ho.")
            gr.Markdown("### Image reference guidance (Drive mein save hoti hai)")
            image_reference = gr.Textbox(label="Reference se kya follow karein", value=s.get("image_reference", ""),
                                         lines=3, max_lines=5, max_length=500,
                                         placeholder="Jaise: Indian matrimonial portrait, natural smile, poora head frame mein, simple saree/kurta")
            image_avoid = gr.Textbox(label="Kin cheezon se bachein", value=s.get("image_avoid", ""),
                                     lines=2, max_lines=4, max_length=500,
                                     placeholder="Comma se alag karein; jaise: sindoor, cropped hairline, bridal jewellery")
            guidance_save = gr.Button("Reference settings save karein")
            guidance_status = gr.HTML()
        settings = [post_type, instruction, brand_on, brand_name, footer, fmt, plang]
        guidance_save.click(save_image_guidance, [image_reference, image_avoid], guidance_status)

        with gr.Tab("1. Images banao"):
            with gr.Row():
                with gr.Column(scale=1):
                    category = gr.Dropdown(CATEGORIES, value="Marriage", label="Category")
                    subject = gr.Dropdown(list(SUBJECTS.values()), value=SUBJECTS[DEFAULT_SUBJECT], label="Kiski photo")
                    count = gr.Radio([1, 10, 20, 30], value=1, label="Kitni images")
                    photo = gr.Radio(["Half photo", "Full photo"], value="Half photo", label="Photo",
                                     info="Half = chest-up portrait. Full = head-to-shoes; full photo ko crop nahi kiya jayega.")
                    cls = gr.Radio(CLASSES, value="Mix (har baar alag)", label="Look (kapde / jagah)")
                    size = gr.Dropdown(list(SIZES), value="1080x1350 (Portrait)", label="Size")
                    extra = gr.Textbox(label="Apni baat likhein (optional)", max_lines=3,
                                       placeholder="jaise 'red kurta, garden mein, haste hue'")
                    go = gr.Button("Images banao", variant="primary")
                    go_all = gr.Button("Images + Posts ek saath banao", variant="primary")
                    stop = gr.Button("⏹ Roko / Cancel", variant="stop")
                    status = gr.Markdown()
                    err = gr.HTML()
                    up = gr.File(label="Apni photo upload", file_count="multiple", file_types=["image"])
                    del_id = gr.Dropdown(image_ids(), label="Image delete karein (ID)")
                    del_btn = gr.Button("Delete")
                with gr.Column(scale=2):
                    gallery = gr.Gallery(image_gallery(), label="Aapki images — biodata ke liye photo select karne click karein", columns=3, height=800, object_fit="contain")

        with gr.Tab("2. Posts banao"):
            with gr.Row():
                with gr.Column(scale=1):
                    only_new = gr.Checkbox(label="Sirf nayi images ke post", value=True)
                    pquick = gr.Button("⚡ 10 naye ready posts banao (photo + Hindi text)", variant="primary")
                    pgo = gr.Button("Maujooda images ke posts banao")
                    pstop = gr.Button("⏹ Roko / Cancel", variant="stop")
                    pstatus = gr.Markdown()
                    perr = gr.HTML()
                    gr.Markdown("Quick button bina prompt likhe 10 fresh portrait + complete post banata hai. Caption mein demo disclosure rahega; image par nahi.")
                    gr.Markdown("### Post edit karein (headline, CTA, caption aur hashtags)")
                    pid = gr.Dropdown(image_ids(), label="Image ID")
                    eh = gr.Textbox(label="Headline")
                    rh = gr.Button("↻ Headline naya", size="sm")
                    ec = gr.Textbox(label="CTA")
                    rc = gr.Button("↻ CTA naya", size="sm")
                    ecap = gr.Textbox(label="Caption", lines=3)
                    rcap = gr.Button("↻ Caption naya", size="sm")
                    etag = gr.Textbox(label="Hashtags")
                    rtag = gr.Button("↻ Hashtags naye", size="sm")
                    eadd = gr.Button("Image par add karo")
                    pzip = gr.Button("Saare posts ZIP download")
                    pfile = gr.File(label="ZIP")
                with gr.Column(scale=2):
                    pgallery = gr.Gallery(post_gallery(), label="Posts", columns=3, height=800, object_fit="contain")

        with gr.Tab("3. Biodata banao"):
            with gr.Row():
                with gr.Column(scale=1):
                    gr.Markdown("### One-click fictional biodata\nDefault settings par seedha button dabayein. Har profile ke liye nayi AI portrait aur randomly generated fictional details banengi. Koi real member data use nahi hota.")
                    selected_bio_source = gr.State("")
                    bio_source_status = gr.Markdown("Abhi koi photo select nahi hui.")
                    btype = gr.Dropdown(BIO_TYPES, value="Marriage", label="Type")
                    bphoto = gr.Radio(["Half photo", "Full photo", "Mix"], value="Half photo", label="Photo",
                                      info="Half = chest-up portrait. Full = poora sharir, bina crop ke.")
                    blang = gr.Radio(LANGS, value=LANGS[0], label="Bhasha")
                    bcls = gr.Radio(CLASSES, value="Mix (har baar alag)", label="Look")
                    statuses = gr.CheckboxGroup(MARITAL, label="Status (Remarriage)")
                    children = gr.Radio(["Any", "Yes", "No"], value="Any", label="Bachche (Remarriage)")
                    gender = gr.Radio(["Female", "Male"], value="Female", label="Gender")
                    state = gr.Dropdown([ALL_STATES_LABEL] + STATES, value=ALL_STATES_LABEL, label="State")
                    community = gr.Dropdown([ALL_STATES_LABEL] + COMMUNITIES, value=ALL_STATES_LABEL, label="Community")
                    full_name = gr.Checkbox(label="Poora naam (surname ke saath)")
                    letters = gr.Textbox(label="Naam in letters se shuru (optional)", max_lines=1)
                    binst = gr.Textbox(label="Apni baat (optional)", max_lines=3)
                    bcount = gr.Radio([1, 5, 10, 20], value=10, label="Kitne biodata")
                    bbrand = gr.Checkbox(label="Brand name dikhaye", value=s["bio_brand_on"])
                    bgo = gr.Button(biodata_button_label(10), variant="primary")
                    bcount.change(lambda n: gr.update(value=biodata_button_label(n)), bcount, bgo)
                    bquick = gr.Button("⚡ 10 biodata — ek click, bina likhe", variant="primary")
                    bsource = gr.Button("Selected photo se biodata banao")
                    bstop = gr.Button("⏹ Roko / Cancel", variant="stop")
                    bstatus = gr.Markdown()
                    berr = gr.HTML()
                    gr.Markdown("### Card edit")
                    bid = gr.Dropdown(bio_ids(), label="Biodata ID")
                    with gr.Row():
                        bname = gr.Textbox(label="Naam (Hindi)")
                        broman = gr.Textbox(label="Name (Roman)")
                        bname_re = gr.Button("↻ Naam naya", size="sm")
                    with gr.Row():
                        bage = gr.Number(label="Umar", precision=0)
                        bage_re = gr.Button("↻ Umar nayi", size="sm")
                    with gr.Row():
                        bheight = gr.Textbox(label="Height")
                        bheight_re = gr.Button("↻ Height nayi", size="sm")
                    with gr.Row():
                        beducation = gr.Textbox(label="Padhai")
                        beducation_re = gr.Button("↻ Padhai nayi", size="sm")
                    with gr.Row():
                        bjob = gr.Textbox(label="Job")
                        bjob_re = gr.Button("↻ Job nayi", size="sm")
                    with gr.Row():
                        bcity = gr.Textbox(label="Shehar")
                        bstate = gr.Textbox(label="State")
                        bcity_re = gr.Button("↻ Shehar naya", size="sm")
                    with gr.Row():
                        bstatus_edit = gr.Textbox(label="Status")
                        bstatus_re = gr.Button("↻ Status naya", size="sm")
                    with gr.Row():
                        bfamily = gr.Textbox(label="Family")
                        bfamily_re = gr.Button("↻ Family nayi", size="sm")
                    with gr.Row():
                        bexpect = gr.Textbox(label="Khaas line", lines=3)
                        bexpect_re = gr.Button("↻ Nayi line", size="sm")
                    with gr.Row():
                        bsave = gr.Button("Save")
                        bregen = gr.Button("Regenerate")
                        bdel = gr.Button("Delete")
                    bcap = gr.Textbox(label="Caption", lines=3)
                    bcap_re = gr.Button("↻ Caption naya", size="sm")
                    btag = gr.Textbox(label="Hashtags")
                    btag_re = gr.Button("↻ Hashtags naye", size="sm")
                    btxt_save = gr.Button("Caption/Hashtags save")
                    bzip = gr.Button("Saare biodata ZIP download")
                    bfile = gr.File(label="ZIP")
                with gr.Column(scale=2):
                    bgallery = gr.Gallery(bio_gallery(), label="Biodata", columns=2, height=900, object_fit="contain")

        with gr.Tab("4. Enhance"):
            gr.Markdown(
                "**AI (ComfyUI):** 4x-UltraSharp upscaling ke baad low-denoise SDXL image refinement. "
                "Notebook setup mein FaceDetailer / hand-detailer nodes aur unke detection models optional roop se download hote hain; "
                "install na ho paayein to app available upscaling/refinement ke saath chalta hai. "
                "Iske liye ComfyUI chalna zaroori hai; error aaye to original image safe rehti hai.\n\n"
                "**Basic (Pillow):** Lanczos resizing, median denoise, auto-contrast, colour aur sharpening; "
                "ye generative AI nahi hai. Basic option khud select karne par hi chalega."
            )
            enhance_status = gr.Markdown(comfy.enhancement_status())
            method = gr.Radio([enhance.AI_METHOD, enhance.BASIC_METHOD], value=enhance.AI_METHOD, label="Enhancement tool")
            level = gr.Radio(list(enhance.LEVELS), value="Normal", label="Enhance kitna")
            with gr.Row():
                with gr.Column():
                    gr.Markdown("### Image enhance")
                    xi = gr.Dropdown(image_ids(), multiselect=True, label="Image IDs")
                    xi_all = gr.Checkbox(label="Sab images")
                    xi_go = gr.Button("Images enhance karo", variant="primary")
                    xi_msg = gr.HTML()
                with gr.Column():
                    gr.Markdown("### Post enhance")
                    xp = gr.Dropdown(image_ids(), multiselect=True, label="Post IDs")
                    xp_all = gr.Checkbox(label="Sab posts")
                    xp_text = gr.Checkbox(label="Text bhi naya aur behtar likho")
                    xp_go = gr.Button("Posts enhance karo", variant="primary")
                    xp_msg = gr.HTML()
                with gr.Column():
                    gr.Markdown("### Biodata enhance")
                    xb = gr.Dropdown(bio_ids(), multiselect=True, label="Biodata IDs")
                    xb_all = gr.Checkbox(label="Sab biodata")
                    xb_photo = gr.Checkbox(label="Photo bhi enhance karo", value=True)
                    xb_det = gr.Checkbox(label="Details bhi poori aur behtar karo (naam/umar wahi)")
                    xb_go = gr.Button("Biodata enhance karo", variant="primary")
                    xb_msg = gr.HTML()
            xrefresh = gr.Button("ID list refresh karo")

        with gr.Tab("5. Extra tools"):
            gr.Markdown("Halke tools: GPU/AI credit nahi lagta, turant chalte hain.")
            with gr.Accordion("Har platform ka size + WhatsApp number / logo watermark", open=True):
                with gr.Row():
                    t_ids = gr.Dropdown(tools.all_ids(), multiselect=True, label="Post / Biodata IDs")
                    t_all = gr.Checkbox(label="Sab posts aur biodata")
                t_pl = gr.CheckboxGroup(list(tools.PLATFORMS), value=list(tools.PLATFORMS)[:3], label="Kaunse size")
                with gr.Row():
                    t_wm = gr.Checkbox(value=True, label="Watermark lagao")
                    t_num = gr.Textbox(label="WhatsApp number", placeholder="98xxxxxxxx")
                    t_logo = gr.Image(type="filepath", label="Logo (optional, PNG)", height=120)
                with gr.Row():
                    t_pos = gr.Radio(["Neeche right", "Neeche left", "Upar right", "Upar left"], value="Neeche right", label="Kahan")
                    t_op = gr.Slider(20, 100, value=80, step=5, label="Kitna gehra (%)")
                with gr.Row():
                    t_go = gr.Button("Sab size banao", variant="primary")
                    t_ref = gr.Button("ID list refresh")
                t_msg = gr.HTML()
                t_file = gr.File(label="Zip download")
                t_gal = gr.Gallery(columns=4, height=360, object_fit="contain")
            with gr.Accordion("Hafte bhar ka post plan", open=False):
                with gr.Row():
                    w_start = gr.Textbox(label="Shuru ki date (YYYY-MM-DD, khali = aaj)")
                    w_per = gr.Slider(1, 4, value=2, step=1, label="Roz kitne post")
                    w_go = gr.Button("Plan banao", variant="primary")
                w_tab = gr.Dataframe(tools.load_plan(), headers=["Date", "Din", "Time", "Post type", "Note"],
                                     interactive=True, wrap=True)
                w_save = gr.Button("Plan save karo")
                w_msg = gr.HTML()
            with gr.Accordion("Leads list (kisne message kiya)", open=False):
                with gr.Row():
                    l_name = gr.Textbox(label="Naam")
                    l_phone = gr.Textbox(label="Phone")
                    l_src = gr.Dropdown(["Instagram", "WhatsApp", "Facebook", "Call", "Other"], value="Instagram", label="Kahan se")
                with gr.Row():
                    l_bio = gr.Dropdown(bio_ids(), multiselect=True, label="Kaunsa biodata bheja")
                    l_st = gr.Dropdown(tools.LEAD_STATUS, value="Naya", label="Status")
                    l_note = gr.Textbox(label="Note")
                l_add = gr.Button("Lead jodo", variant="primary")
                l_msg = gr.HTML()
                l_tab = gr.Dataframe(tools.leads_rows(), headers=tools.LEAD_COLS, interactive=True, wrap=True)
                with gr.Row():
                    l_save = gr.Button("Table ke badlav save karo")
                    l_csv = gr.Button("Excel (CSV) download")
                l_file = gr.File()
            t_go.click(tools.export_all, [t_ids, t_all, t_pl, t_num, t_logo, t_pos, t_op, t_wm], [t_msg, t_file, t_gal])
            t_ref.click(lambda: (gr.update(choices=tools.all_ids()), gr.update(choices=bio_ids())), None, [t_ids, l_bio])
            w_go.click(tools.weekly_plan, [w_start, w_per], w_tab)
            w_save.click(tools.save_plan, w_tab, w_msg)
            l_add.click(tools.add_lead, [l_name, l_phone, l_src, l_bio, l_st, l_note], [l_msg, l_tab])
            l_save.click(tools.save_leads, l_tab, [l_msg, l_tab])
            l_csv.click(tools.leads_csv, None, l_file)

        refresh_ids = lambda: (gr.update(choices=image_ids()), gr.update(choices=image_ids()))
        e1 = go.click(make_images, [category, subject, count, photo, size, extra, cls], [status, err, gallery])
        e1.then(refresh_ids, None, [del_id, pid])
        e2 = go_all.click(images_and_posts, [category, subject, count, photo, size, extra, cls, *settings],
                          [status, err, gallery, pgallery])
        e2.then(refresh_ids, None, [del_id, pid])
        stop.click(stop_all, None, status, cancels=[e1, e2], queue=False).then(refresh_ids, None, [del_id, pid])
        up.upload(upload_images, [up, size], [gallery, del_id])
        del_btn.click(delete_image, del_id, [gallery, del_id])
        epq = pquick.click(quick_make_posts, [category, subject, size, cls], [pstatus, perr, gallery, pgallery]).then(refresh_ids, None, [del_id, pid])
        e3 = pgo.click(make_posts, [only_new, *settings], [pstatus, perr, pgallery])
        pstop.click(stop_all, None, pstatus, cancels=[e3, epq], queue=False)
        fields = [pid, eh, ec, ecap, etag]
        for btn, fld in ((rh, "headline"), (rc, "cta"), (rcap, "caption"), (rtag, "hashtags")):
            btn.click(lambda *a, f=fld: regen_field(f, *a), fields, [eh, ec, ecap, etag])
        pid.change(load_post, pid, [eh, ec, ecap, etag])
        eadd.click(edit_post, [pid, eh, ec, ecap, etag], [perr, pgallery])
        pzip.click(lambda: zip_folder(POSTS_DIR, "posts"), None, pfile)
        e4 = bgo.click(make_biodata, [btype, statuses, children, gender, state, community, full_name, letters, binst, bcount,
                                      bbrand, bphoto, blang, bcls], [bstatus, berr, bgallery])
        ebq = bquick.click(quick_make_biodata, [btype, statuses, children, gender, state, community, bbrand, bphoto, blang, bcls],
                           [bstatus, berr, bgallery])
        gallery.select(select_bio_source, None, [selected_bio_source, bio_source_status])
        bsource.click(make_biodata_from_image, [selected_bio_source, btype, statuses, children, gender, state, community,
                                                full_name, letters, binst, bbrand, blang, bcls],
                      [bstatus, berr, bgallery])
        e4.then(lambda: gr.update(choices=bio_ids()), None, bid)
        bstop.click(stop_all, None, bstatus, cancels=[e4, ebq], queue=False).then(lambda: gr.update(choices=bio_ids()), None, bid)
        bio_fields = [bname, broman, bage, bheight, beducation, bjob, bcity, bstate,
                      bstatus_edit, bfamily, bexpect, bcap, btag]
        bsave.click(bio_edit, [bid, bname, broman, bage, bheight, beducation, bjob, bcity, bstate,
                              bstatus_edit, bfamily, bexpect], [berr, bgallery])
        bid.change(bio_load, bid, bio_fields)
        for button, field in ((bname_re, "name"), (bage_re, "age"), (bheight_re, "height"),
                              (beducation_re, "education"), (bjob_re, "job"), (bcity_re, "city"),
                              (bstatus_re, "status"), (bfamily_re, "family"), (bexpect_re, "expectations")):
            button.click(lambda selected, f=field: bio_regen_field(f, selected), bid,
                         [berr, bgallery, *bio_fields])
        bcap_re.click(lambda i, c, t: bio_regen_text("caption", i, c, t), [bid, bcap, btag], [berr, bcap, btag])
        btag_re.click(lambda i, c, t: bio_regen_text("hashtags", i, c, t), [bid, bcap, btag], [berr, bcap, btag])
        btxt_save.click(bio_save_text, [bid, bcap, btag], berr)
        bregen.click(bio_regen, bid, [berr, bgallery]).then(bio_load, bid, bio_fields)
        bdel.click(bio_delete, bid, [bgallery, bid])
        bzip.click(lambda: zip_folder(BIODATA_DIR, "biodata"), None, bfile)
        xi_go.click(enhance_images, [xi, level, xi_all, method], [xi_msg, gallery])
        xp_go.click(enhance_posts, [xp, level, xp_text, xp_all, method], [xp_msg, pgallery])
        xb_go.click(enhance_bios, [xb, level, xb_det, xb_all, method, xb_photo], [xb_msg, bgallery])
        xrefresh.click(lambda: (gr.update(choices=image_ids()), gr.update(choices=image_ids()), gr.update(choices=bio_ids()), comfy.enhancement_status()), None, [xi, xp, xb, enhance_status])
    return ui


if __name__ == "__main__":
    build().queue(default_concurrency_limit=1).launch(
        share=True, show_api=False, allowed_paths=[str(DATA)], server_name="127.0.0.1", server_port=7860,
        prevent_thread_lock=False,
    )
