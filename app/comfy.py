"""Talks to the local ComfyUI server (started by the notebook). One image at a time.

v5 pipeline (free, fits a Colab T4 without filling RAM/disk):
  identity mix  two random face identities blended at a random ratio (ConditioningAverage)
                -> a face that never existed before; fixes "har photo mein same face"
  pass 1        SDXL photo model, random CFG/sampler per image (more variety)
  pass 2        4x-UltraSharp pixel upscale -> resize 1.4x -> low-denoise re-render (sharp skin/eyes/cloth)
  pass 3        FaceDetailer with the SAME identity text (so the face fix does not pull every face
                back to the model's default face) at low denoise
  VAE           sdxl-vae-fp16-fix (no washed-out / grey images on T4)
Missing optional files (upscaler, VAE, Impact Pack) are skipped automatically.
"""
import io
import json
import os
import random
import time
import urllib.parse
import urllib.request

from PIL import Image

from .config import CHECKPOINT, COMFY_URL, COMFY_OUT
from .prompts import NEGATIVE

UPSCALER = "4x-UltraSharp.pth"
VAE = "sdxl_vae_fp16_fix.safetensors"
_info: dict = {}


def _get(path: str):
    with urllib.request.urlopen(COMFY_URL + path, timeout=30) as r:
        return r.read()


def _post(path: str, data: dict):
    req = urllib.request.Request(COMFY_URL + path, data=json.dumps(data).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()


def _options(node: str, field: str) -> list:
    """List of files ComfyUI sees for a loader node (cached)."""
    key = f"{node}.{field}"
    if key not in _info:
        try:
            j = json.loads(_get(f"/object_info/{node}"))
            _info[key] = j[node]["input"]["required"][field][0]
        except Exception:
            _info[key] = []
    return _info[key]


def face_detailer_ready() -> bool:
    if "face" not in _info:
        try:
            _info["face"] = "FaceDetailer" in json.loads(_get("/object_info/FaceDetailer"))
        except Exception:
            _info["face"] = False
    return _info["face"]


def free_memory():
    """Ask ComfyUI to drop cached models (used after an out-of-memory error)."""
    try:
        _post("/free", {"unload_models": True, "free_memory": True})
    except Exception:
        pass


def _enc(wf: dict, nid: str, text: str):
    wf[nid] = {"class_type": "CLIPTextEncode", "inputs": {"text": text, "clip": ["4", 1]}}
    return [nid, 0]


def workflow(job: dict, w: int, h: int, seed: int) -> dict:
    rnd = random.Random(seed)
    wf: dict = {"4": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": CHECKPOINT}}}
    vae = ["4", 2]
    if VAE in _options("VAELoader", "vae_name"):
        wf["40"] = {"class_type": "VAELoader", "inputs": {"vae_name": VAE}}
        vae = ["40", 0]

    # --- positive = scene + (identity A blended with identity B) ---
    pos = _enc(wf, "6", job["scene"])
    ident = None
    if job.get("ident_a"):
        ident = _enc(wf, "30", job["ident_a"])
        if job.get("ident_b"):
            b = _enc(wf, "31", job["ident_b"])
            wf["32"] = {"class_type": "ConditioningAverage", "inputs": {
                "conditioning_to": ident, "conditioning_from": b,
                "conditioning_to_strength": round(rnd.uniform(0.35, 0.65), 2)}}
            ident = ["32", 0]
        wf["33"] = {"class_type": "ConditioningConcat", "inputs": {"conditioning_to": ident, "conditioning_from": pos}}
        pos = ["33", 0]
    neg = _enc(wf, "7", job.get("neg") or NEGATIVE)

    wf["5"] = {"class_type": "EmptyLatentImage", "inputs": {"width": w, "height": h, "batch_size": 1}}
    wf["3"] = {"class_type": "KSampler", "inputs": {
        "seed": seed, "steps": 30, "cfg": round(rnd.uniform(3.5, 5.5), 1),
        "sampler_name": rnd.choice(["dpmpp_2m_sde", "dpmpp_2m", "dpmpp_sde"]), "scheduler": "karras",
        "denoise": 1.0, "model": ["4", 0], "positive": pos, "negative": neg, "latent_image": ["5", 0]}}

    # --- pass 2: pixel upscale + re-render ---
    hw, hh = (int(w * 1.4) // 8) * 8, (int(h * 1.4) // 8) * 8
    if UPSCALER in _options("UpscaleModelLoader", "model_name"):
        wf["8a"] = {"class_type": "VAEDecode", "inputs": {"samples": ["3", 0], "vae": vae}}
        wf["12"] = {"class_type": "UpscaleModelLoader", "inputs": {"model_name": UPSCALER}}
        wf["13"] = {"class_type": "ImageUpscaleWithModel", "inputs": {"upscale_model": ["12", 0], "image": ["8a", 0]}}
        wf["14"] = {"class_type": "ImageScale", "inputs": {
            "image": ["13", 0], "upscale_method": "lanczos", "width": hw, "height": hh, "crop": "disabled"}}
        wf["10"] = {"class_type": "VAEEncode", "inputs": {"pixels": ["14", 0], "vae": vae}}
        den = 0.33
    else:
        wf["10"] = {"class_type": "LatentUpscale", "inputs": {
            "samples": ["3", 0], "upscale_method": "bislerp", "width": hw, "height": hh, "crop": "disabled"}}
        den = 0.42
    wf["11"] = {"class_type": "KSampler", "inputs": {
        "seed": seed + 1, "steps": 20, "cfg": 4.0, "sampler_name": "dpmpp_2m", "scheduler": "karras",
        "denoise": den, "model": ["4", 0], "positive": pos, "negative": neg, "latent_image": ["10", 0]}}
    wf["8"] = {"class_type": "VAEDecode", "inputs": {"samples": ["11", 0], "vae": vae}}
    wf["9"] = {"class_type": "SaveImage", "inputs": {"filename_prefix": "aps", "images": ["8", 0]}}

    # --- pass 3: face fix that keeps THIS face ---
    if face_detailer_ready():
        fpos = _enc(wf, "22", job.get("face") or job["scene"])
        wf["20"] = {"class_type": "UltralyticsDetectorProvider", "inputs": {"model_name": "bbox/face_yolov8m.pt"}}
        wf["21"] = {"class_type": "FaceDetailer", "inputs": {
            "image": ["8", 0], "model": ["4", 0], "clip": ["4", 1], "vae": vae,
            "positive": fpos, "negative": neg, "bbox_detector": ["20", 0],
            "guide_size": 512, "guide_size_for": True, "max_size": 1024, "seed": seed + 2, "steps": 20,
            "cfg": 4.0, "sampler_name": "dpmpp_2m", "scheduler": "karras", "denoise": 0.28, "feather": 8,
            "noise_mask": True, "force_inpaint": True, "bbox_threshold": 0.5, "bbox_dilation": 12,
            "bbox_crop_factor": 3.0, "sam_detection_hint": "center-1", "sam_dilation": 0, "sam_threshold": 0.93,
            "sam_bbox_expansion": 0, "sam_mask_hint_threshold": 0.7, "sam_mask_hint_use_negative": "False",
            "drop_size": 10, "wildcard": "", "cycle": 1, "inpaint_model": False, "noise_mask_feather": 20}}
        wf["9"]["inputs"]["images"] = ["21", 0]
        _hand_fix(wf, ["21", 0], vae, neg, seed)
    return wf


def _detailer(wf, nid, image, vae, pos, neg, det, seed, denoise, guide=512):
    wf[nid] = {"class_type": "FaceDetailer", "inputs": {
        "image": image, "model": ["4", 0], "clip": ["4", 1], "vae": vae,
        "positive": pos, "negative": neg, "bbox_detector": det,
        "guide_size": guide, "guide_size_for": True, "max_size": 1024, "seed": seed, "steps": 20,
        "cfg": 4.0, "sampler_name": "dpmpp_2m", "scheduler": "karras", "denoise": denoise, "feather": 8,
        "noise_mask": True, "force_inpaint": True, "bbox_threshold": 0.45, "bbox_dilation": 16,
        "bbox_crop_factor": 2.5, "sam_detection_hint": "center-1", "sam_dilation": 0, "sam_threshold": 0.93,
        "sam_bbox_expansion": 0, "sam_mask_hint_threshold": 0.7, "sam_mask_hint_use_negative": "False",
        "drop_size": 10, "wildcard": "", "cycle": 1, "inpaint_model": False, "noise_mask_feather": 20}}
    return [nid, 0]


def hands_ready() -> bool:
    return "bbox/hand_yolov8s.pt" in _options("UltralyticsDetectorProvider", "model_name")


def _hand_fix(wf, image, vae, neg, seed):
    """Tool 4: hand detailer -> ungliyan/haath saaf (agar hand model mojood ho)."""
    if not hands_ready():
        return
    wf["50"] = {"class_type": "UltralyticsDetectorProvider", "inputs": {"model_name": "bbox/hand_yolov8s.pt"}}
    hp = _enc(wf, "51", "natural human hand, five fingers, correct anatomy, relaxed hand, detailed skin")
    out = _detailer(wf, "52", image, vae, hp, neg, ["50", 0], seed + 3, 0.35, 384)
    wf["9"]["inputs"]["images"] = out


def upload(img: Image.Image) -> str:
    """Image ko ComfyUI ke input folder mein bhejo (enhance ke liye)."""
    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="PNG")
    name = f"aps_in_{random.randint(1, 10**9)}.png"
    body, boundary = _multipart(name, buf.getvalue())
    req = urllib.request.Request(COMFY_URL + "/upload/image", data=body,
                                 headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read())["name"]


def _multipart(name: str, data: bytes):
    b = "----aps" + str(random.randint(1, 10**9))
    head = (f"--{b}\r\nContent-Disposition: form-data; name=\"image\"; filename=\"{name}\"\r\n"
            "Content-Type: image/png\r\n\r\n").encode()
    tail = (f"\r\n--{b}\r\nContent-Disposition: form-data; name=\"overwrite\"\r\n\r\ntrue\r\n--{b}--\r\n").encode()
    return head + data + tail, b


ENHANCE = {"Light": 0.18, "Normal": 0.26, "Strong": 0.34}


def enhance_workflow(name: str, w: int, h: int, level: str, seed: int) -> dict:
    """AI enhance: 4x-UltraSharp upscale -> halka re-render (detail + real skin) -> face fix -> hand fix.
    Chehra/kapde wahi rehte hain (low denoise), sirf quality badhti hai."""
    wf: dict = {"4": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": CHECKPOINT}}}
    vae = ["4", 2]
    if VAE in _options("VAELoader", "vae_name"):
        wf["40"] = {"class_type": "VAELoader", "inputs": {"vae_name": VAE}}
        vae = ["40", 0]
    pos = _enc(wf, "6", "RAW photo, sharp focus, detailed natural skin texture, clear beautiful eyes, crisp fabric, "
                        "natural colours, professional photography, high detail")
    from .prompts import NEGATIVE as N
    neg = _enc(wf, "7", N)
    wf["1"] = {"class_type": "LoadImage", "inputs": {"image": name}}
    img = ["1", 0]
    if UPSCALER in _options("UpscaleModelLoader", "model_name"):
        wf["12"] = {"class_type": "UpscaleModelLoader", "inputs": {"model_name": UPSCALER}}
        wf["13"] = {"class_type": "ImageUpscaleWithModel", "inputs": {"upscale_model": ["12", 0], "image": img}}
        img = ["13", 0]
    tw, th = (w // 8) * 8, (h // 8) * 8
    wf["14"] = {"class_type": "ImageScale", "inputs": {"image": img, "upscale_method": "lanczos",
                                                         "width": tw, "height": th, "crop": "disabled"}}
    wf["10"] = {"class_type": "VAEEncode", "inputs": {"pixels": ["14", 0], "vae": vae}}
    wf["11"] = {"class_type": "KSampler", "inputs": {
        "seed": seed, "steps": 24, "cfg": 4.0, "sampler_name": "dpmpp_2m", "scheduler": "karras",
        "denoise": ENHANCE.get(level, 0.26), "model": ["4", 0], "positive": pos, "negative": neg, "latent_image": ["10", 0]}}
    wf["8"] = {"class_type": "VAEDecode", "inputs": {"samples": ["11", 0], "vae": vae}}
    wf["9"] = {"class_type": "SaveImage", "inputs": {"filename_prefix": "aps", "images": ["8", 0]}}
    if face_detailer_ready():
        wf["20"] = {"class_type": "UltralyticsDetectorProvider", "inputs": {"model_name": "bbox/face_yolov8m.pt"}}
        fp = _enc(wf, "22", "detailed beautiful face, sharp clear eyes, natural skin")
        wf["9"]["inputs"]["images"] = _detailer(wf, "21", ["8", 0], vae, fp, neg, ["20", 0], seed + 2, 0.3)
        _hand_fix(wf, ["21", 0], vae, neg, seed)
    return wf


def enhance(img: Image.Image, level: str = "Normal", timeout: int = 900) -> Image.Image:
    if not is_up():
        raise RuntimeError("ComfyUI chal nahi raha. Notebook ka 'Start' cell dobara chalayein.")
    name = upload(img)
    # max ~1.5 MP so T4 does not run out of memory
    s = min(1.0, (1_500_000 / (img.width * img.height)) ** 0.5) * 1.0
    w, h = int(img.width * s), int(img.height * s)
    return _submit(enhance_workflow(name, w, h, level, random.randint(1, 2**31)), timeout).resize(img.size, Image.LANCZOS)


def is_up() -> bool:
    try:
        _get("/system_stats")
        return True
    except Exception:
        return False


def _run(job: dict, w: int, h: int, timeout: int) -> Image.Image:
    return _submit(workflow(job, w, h, random.randint(1, 2**31)), timeout)


def interrupt():
    """Stop button: ComfyUI ka chal raha kaam turant roko."""
    try:
        _post("/interrupt", {})
    except Exception:
        pass


def _submit(wf: dict, timeout: int) -> Image.Image:
    try:
        pid = json.loads(_post("/prompt", {"prompt": wf}))["prompt_id"]
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"ComfyUI error {e.code}: {e.read().decode()[:300]}")
    start = time.time()
    while time.time() - start < timeout:
        hist = json.loads(_get(f"/history/{pid}"))
        if pid in hist:
            item = hist[pid]
            status = item.get("status", {})
            if status.get("status_str") == "error":
                raise RuntimeError(f"ComfyUI image fail: {json.dumps(status.get('messages', ''))[:300]}")
            for out in item.get("outputs", {}).values():
                for im in out.get("images", []):
                    q = urllib.parse.urlencode({"filename": im["filename"], "subfolder": im["subfolder"], "type": im["type"]})
                    img = Image.open(io.BytesIO(_get(f"/view?{q}"))).convert("RGB")
                    # ComfyUI's own copy is not needed (app saves its own) -> keep disk empty
                    try:
                        os.remove(os.path.join(COMFY_OUT, im["subfolder"], im["filename"]))
                    except OSError:
                        pass
                    return img
        time.sleep(1.5)
    raise RuntimeError("Image banne mein bahut time lag gaya (timeout).")


def generate(job: dict | str, w: int, h: int, timeout: int = 900) -> Image.Image:
    if not is_up():
        raise RuntimeError("ComfyUI chal nahi raha. Notebook ka 'Start' cell dobara chalayein.")
    if isinstance(job, str):
        job = {"scene": job}
    try:
        return _run(job, w, h, timeout)
    except RuntimeError as e:
        if "out of memory" not in str(e).lower() and "OutOfMemory" not in str(e):
            raise
        free_memory()  # GPU full -> clear and try once more
        return _run(job, w, h, timeout)
