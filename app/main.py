"""AI Post Studio (Colab + ComfyUI edition). UI text in Hinglish.
Run:  python -m app.main   (the notebook does this for you)"""
import random
import time
import zipfile

import gradio as gr
from PIL import Image

from . import comfy, names, storage, textgen
from .config import (ALL_STATES_LABEL, BIODATA_DIR, CATEGORIES, COMMUNITIES, DATA, IMAGES_DIR, MARITAL,
                     POST_TYPES, POSTS_DIR, SIZES, STATE_WEIGHTS, STATES, SUBJECTS, ensure_dirs)
from .prompts import build_image_prompt, build_portrait_prompt
from .render import fit_cover, render_biodata, render_post

ensure_dirs()


def red(msg: str) -> str:
    return f"<p style='color:#b91c1c;font-weight:600'>{msg}</p>" if msg else ""


def ok(msg: str) -> str:
    return f"<p style='color:#7a1f1a;font-weight:600'>{msg}</p>"


def pick_state() -> str:
    items = list(STATE_WEIGHTS.items())
    return random.choices([s for s, _ in items], weights=[w for _, w in items])[0]


# ---------------- Images ----------------
def image_gallery():
    db = storage.load()
    return [(i["path"], f"{i['id']} • {i['category']} • {i['subject']}") for i in db["images"]]


def image_ids():
    return [i["id"] for i in storage.load()["images"]]


def make_images(category, subject_label, count, photo, size, extra):
    subject = next(k for k, v in SUBJECTS.items() if v == subject_label)
    w, h, gw, gh = SIZES[size]
    done = failed = 0
    err = ""
    count = int(count)
    for n in range(count):  # strictly one at a time
        yield f"Ban rahi hain {done}/{count}…", red(err), image_gallery()
        try:
            img = comfy.generate(build_image_prompt(category, subject, photo == "Full photo", extra or ""), gw, gh)
            img = fit_cover(img, w, h)
            iid = storage.uid()
            path = IMAGES_DIR / f"{iid}.jpg"
            img.save(path, quality=93)
            storage.update(lambda d: d["images"].insert(0, {
                "id": iid, "path": str(path), "w": w, "h": h, "category": category, "subject": subject,
                "source": "ai", "at": time.time()}))
            done += 1
        except Exception as e:
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
            "source": "upload", "at": time.time()}))
    return image_gallery(), gr.update(choices=image_ids())


def delete_image(iid):
    def f(d):
        d["images"] = [i for i in d["images"] if i["id"] != iid]
        d["posts"].pop(iid, None)
    storage.update(f)
    return image_gallery(), gr.update(choices=image_ids(), value=None)


# ---------------- Posts ----------------
def save_settings(post_type_label, instruction, brand_on, brand_name, footer, fmt):
    pt = next(k for k, v in POST_TYPES.items() if v == post_type_label)

    def f(d):
        d["settings"].update(post_type=pt, instruction=instruction or "", brand_on=bool(brand_on),
                             brand_name=(brand_name or "").strip(), footer=footer or "", format=fmt)
    storage.update(f)


def post_gallery():
    db = storage.load()
    return [(p["rendered"], f"{iid}\n{p['headline']}") for iid, p in db["posts"].items() if p.get("rendered")]


def make_one_post(img_rec, s):
    db = storage.load()
    brand = s["brand_name"] if s["brand_on"] else ""
    t = textgen.post_text(s["post_type"], s["instruction"], img_rec["category"], img_rec["subject"], db["headlines"], brand)
    storage.push_headline(t["headline"])
    out = render_post(Image.open(img_rec["path"]), t["headline"], t["cta"], s["brand_on"], s["brand_name"], s["footer"])
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
            err = f"Post fail: {e}"
    yield f"Ho gaya {len(todo)} post", red(err), post_gallery()


def edit_post(iid, headline, cta, caption, hashtags):
    db = storage.load()
    rec = next((i for i in db["images"] if i["id"] == iid), None)
    if not rec:
        return red("Pehle image ID chunein"), post_gallery()
    s = db["settings"]
    t = {"headline": headline, "cta": cta, "caption": caption, "hashtags": hashtags}
    out = render_post(Image.open(rec["path"]), headline, cta, s["brand_on"], s["brand_name"], s["footer"])
    path = POSTS_DIR / f"{iid}.{'jpg' if s['format'] == 'jpg' else 'png'}"
    out.save(path, quality=93)
    (POSTS_DIR / f"{iid}.txt").write_text(f"{caption}\n\n{hashtags}", "utf-8")
    t["rendered"] = str(path)
    storage.update(lambda d: d["posts"].__setitem__(iid, t))
    storage.push_headline(headline)
    return ok("Image par add ho gaya"), post_gallery()


def load_post(iid):
    p = storage.load()["posts"].get(iid or "", {})
    return p.get("headline", ""), p.get("cta", ""), p.get("caption", ""), p.get("hashtags", "")


def images_and_posts(category, subject_label, count, photo, size, extra, *settings):
    """One click: N images, then their posts."""
    before = set(image_ids())
    for status, e, gal in make_images(category, subject_label, count, photo, size, extra):
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


def make_one_bio(o, bid=None):
    db = storage.load()
    used = names.prune(db["used_names"])
    blocked = lambda n: names.is_blocked(n, used)
    brand = db["settings"]["brand_name"] if db["settings"]["bio_brand_on"] else ""
    det = textgen.biodata(o, names.recent(used), brand, blocked)
    gender = "Female" if o["type"] == "Gharjamai" else o["gender"]
    photo = comfy.generate(build_portrait_prompt(gender, det["age"], o["community"], o["state"], o["type"] == "Remarriage"), 896, 1120)
    bid = bid or storage.uid()
    ppath = BIODATA_DIR / f"{bid}_photo.jpg"
    photo.save(ppath, quality=93)
    out = render_biodata(photo, det, db["settings"]["bio_brand_on"], db["settings"]["brand_name"])
    rpath = BIODATA_DIR / f"{bid}.png"
    out.save(rpath)
    (BIODATA_DIR / f"{bid}.txt").write_text(f"{det['caption']}\n\n{det['hashtags']}", "utf-8")

    def f(d):
        d["used_names"] = names.prune(d["used_names"]) + [{"name": det["name_roman"], "at": time.time()}]
        rec = {"id": bid, "photo": str(ppath), "details": det, "rendered": str(rpath), "opts": o, "at": time.time()}
        d["biodata"] = [rec] + [b for b in d["biodata"] if b["id"] != bid]
    storage.update(f)


def make_biodata(btype, statuses, children, gender, state, community, full_name, letters, instruction, count, brand_on):
    storage.update(lambda d: d["settings"].__setitem__("bio_brand_on", bool(brand_on)))
    err = ""
    count = int(count)
    for n in range(count):
        yield f"Biodata ban raha {n}/{count}…", red(err), bio_gallery()
        o = {"type": btype, "statuses": statuses or [], "children": children, "gender": gender,
             "state": pick_state() if state == ALL_STATES_LABEL else state,
             "community": random.choice(COMMUNITIES) if community == ALL_STATES_LABEL else community,
             "full_name": bool(full_name), "letters": (letters or "")[:10], "instruction": (instruction or "")[:500]}
        try:
            make_one_bio(o)
        except Exception as e:
            err = f"Biodata fail: {e}"
            if "chal nahi raha" in str(e):
                break
    yield f"Ho gaya {count}", red(err), bio_gallery()


def bio_edit(bid, name_hi, age):
    db = storage.load()
    b = next((x for x in db["biodata"] if x["id"] == bid), None)
    if not b:
        return red("ID chunein"), bio_gallery()
    b["details"]["name_hindi"] = name_hi or b["details"]["name_hindi"]
    b["details"]["age"] = int(age or b["details"]["age"])
    out = render_biodata(Image.open(b["photo"]), b["details"], db["settings"]["bio_brand_on"], db["settings"]["brand_name"])
    out.save(b["rendered"])

    def f(d):
        for x in d["biodata"]:
            if x["id"] == bid:
                x["details"] = b["details"]
    storage.update(f)
    return ok("Update ho gaya"), bio_gallery()


def bio_regen(bid):
    b = next((x for x in storage.load()["biodata"] if x["id"] == bid), None)
    if not b:
        return red("ID chunein"), bio_gallery()
    try:
        make_one_bio(b["opts"], bid)  # keeps the same instruction/options
        return ok("Naya ban gaya"), bio_gallery()
    except Exception as e:
        return red(str(e)), bio_gallery()


def bio_delete(bid):
    storage.update(lambda d: d.__setitem__("biodata", [x for x in d["biodata"] if x["id"] != bid]))
    return bio_gallery(), gr.update(choices=bio_ids(), value=None)


# ---------------- UI ----------------
CSS = """
.gradio-container{background:#fbf4e6;font-family:'Mukta',sans-serif}
h1,h2,h3{font-family:'Fraunces',serif;color:#7a1f1a}
button.primary{background:linear-gradient(90deg,#7a1f1a,#c2410c)!important;color:#fff!important}
"""
HEAD = "<link href='https://fonts.googleapis.com/css2?family=Fraunces:wght@700&family=Mukta:wght@400;700&display=swap' rel='stylesheet'>"


def build():
    s = storage.load()["settings"]
    with gr.Blocks(css=CSS, head=HEAD, title="AI Post Studio") as ui:
        gr.Markdown("# AI Post Studio\nImages → Posts → Biodata. Sab kuch aapki Google Drive mein save hota hai.")
        with gr.Accordion("Post settings (brand, post type)", open=False):
            post_type = gr.Dropdown(list(POST_TYPES.values()), value=POST_TYPES[s["post_type"]], label="Post type")
            instruction = gr.Textbox(label="Apni baat (optional)", value=s["instruction"], max_lines=3)
            brand_on = gr.Checkbox(label="Brand name dikhaye", value=s["brand_on"])
            brand_name = gr.Textbox(label="Brand ka naam", value=s["brand_name"])
            footer = gr.Textbox(label="Footer (jaise WhatsApp number)", value=s["footer"])
            fmt = gr.Radio(["png", "jpg"], value=s["format"], label="Download format")
        settings = [post_type, instruction, brand_on, brand_name, footer, fmt]

        with gr.Tab("1. Images banao"):
            with gr.Row():
                with gr.Column(scale=1):
                    category = gr.Dropdown(CATEGORIES, value="Marriage", label="Category")
                    subject = gr.Dropdown(list(SUBJECTS.values()), value="Couple", label="Kiski photo")
                    count = gr.Radio([1, 10, 20, 30], value=1, label="Kitni images")
                    photo = gr.Radio(["Half photo", "Full photo"], value="Half photo", label="Photo")
                    size = gr.Dropdown(list(SIZES), value="1080x1350 (Portrait)", label="Size")
                    extra = gr.Textbox(label="Apni baat likhein (optional)", max_lines=3,
                                       placeholder="jaise 'red kurta, garden mein, haste hue'")
                    go = gr.Button("Images banao", variant="primary")
                    go_all = gr.Button("Images + Posts ek saath banao", variant="primary")
                    status = gr.Markdown()
                    err = gr.HTML()
                    up = gr.File(label="Apni photo upload", file_count="multiple", file_types=["image"])
                    del_id = gr.Dropdown(image_ids(), label="Image delete karein (ID)")
                    del_btn = gr.Button("Delete")
                with gr.Column(scale=2):
                    gallery = gr.Gallery(image_gallery(), label="Aapki images", columns=3, height=800)

        with gr.Tab("2. Posts banao"):
            with gr.Row():
                with gr.Column(scale=1):
                    only_new = gr.Checkbox(label="Sirf nayi images ke post", value=True)
                    pgo = gr.Button("Saari images ke post banao", variant="primary")
                    pstatus = gr.Markdown()
                    perr = gr.HTML()
                    gr.Markdown("### Post edit karein")
                    pid = gr.Dropdown(image_ids(), label="Image ID")
                    eh = gr.Textbox(label="Headline (Hindi)")
                    ec = gr.Textbox(label="CTA")
                    ecap = gr.Textbox(label="Caption", lines=3)
                    etag = gr.Textbox(label="Hashtags")
                    eadd = gr.Button("Image par add karo")
                    pzip = gr.Button("Saare posts ZIP download")
                    pfile = gr.File(label="ZIP")
                with gr.Column(scale=2):
                    pgallery = gr.Gallery(post_gallery(), label="Posts", columns=3, height=800)

        with gr.Tab("3. Biodata banao"):
            with gr.Row():
                with gr.Column(scale=1):
                    btype = gr.Radio(["Marriage", "Remarriage", "Gharjamai"], value="Marriage", label="Type")
                    statuses = gr.CheckboxGroup(MARITAL, label="Status (Remarriage)")
                    children = gr.Radio(["Any", "Yes", "No"], value="Any", label="Bachche (Remarriage)")
                    gender = gr.Radio(["Female", "Male"], value="Female", label="Gender")
                    state = gr.Dropdown([ALL_STATES_LABEL] + STATES, value=ALL_STATES_LABEL, label="State")
                    community = gr.Dropdown([ALL_STATES_LABEL] + COMMUNITIES, value=ALL_STATES_LABEL, label="Community")
                    full_name = gr.Checkbox(label="Poora naam (surname ke saath)")
                    letters = gr.Textbox(label="Naam in letters se shuru (optional)", max_lines=1)
                    binst = gr.Textbox(label="Apni baat (optional)", max_lines=3)
                    bcount = gr.Radio([1, 5, 10, 20], value=1, label="Kitne biodata")
                    bbrand = gr.Checkbox(label="Brand name dikhaye", value=s["bio_brand_on"])
                    bgo = gr.Button("Biodata banao", variant="primary")
                    bstatus = gr.Markdown()
                    berr = gr.HTML()
                    gr.Markdown("### Card edit")
                    bid = gr.Dropdown(bio_ids(), label="Biodata ID")
                    bname = gr.Textbox(label="Naam (Hindi)")
                    bage = gr.Number(label="Umar", precision=0)
                    with gr.Row():
                        bsave = gr.Button("Save")
                        bregen = gr.Button("Regenerate")
                        bdel = gr.Button("Delete")
                    bzip = gr.Button("Saare biodata ZIP download")
                    bfile = gr.File(label="ZIP")
                with gr.Column(scale=2):
                    bgallery = gr.Gallery(bio_gallery(), label="Biodata", columns=2, height=900)

        refresh_ids = lambda: (gr.update(choices=image_ids()), gr.update(choices=image_ids()))
        go.click(make_images, [category, subject, count, photo, size, extra], [status, err, gallery]).then(refresh_ids, None, [del_id, pid])
        go_all.click(images_and_posts, [category, subject, count, photo, size, extra, *settings],
                     [status, err, gallery, pgallery]).then(refresh_ids, None, [del_id, pid])
        up.upload(upload_images, [up, size], [gallery, del_id])
        del_btn.click(delete_image, del_id, [gallery, del_id])
        pgo.click(make_posts, [only_new, *settings], [pstatus, perr, pgallery])
        pid.change(load_post, pid, [eh, ec, ecap, etag])
        eadd.click(edit_post, [pid, eh, ec, ecap, etag], [perr, pgallery])
        pzip.click(lambda: zip_folder(POSTS_DIR, "posts"), None, pfile)
        bgo.click(make_biodata, [btype, statuses, children, gender, state, community, full_name, letters, binst, bcount, bbrand],
                  [bstatus, berr, bgallery]).then(lambda: gr.update(choices=bio_ids()), None, bid)
        bsave.click(bio_edit, [bid, bname, bage], [berr, bgallery])
        bregen.click(bio_regen, bid, [berr, bgallery])
        bdel.click(bio_delete, bid, [bgallery, bid])
        bzip.click(lambda: zip_folder(BIODATA_DIR, "biodata"), None, bfile)
    return ui


if __name__ == "__main__":
    build().queue(default_concurrency_limit=1).launch(share=True, allowed_paths=[str(DATA)])
