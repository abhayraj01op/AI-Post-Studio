"""Talks to the local ComfyUI server (started by the notebook). One image at a time."""
import io
import json
import random
import time
import urllib.parse
import urllib.request

from PIL import Image

from .config import CHECKPOINT, COMFY_URL
from .prompts import NEGATIVE


def workflow(prompt: str, w: int, h: int, seed: int) -> dict:
    return {
        "4": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": CHECKPOINT}},
        "5": {"class_type": "EmptyLatentImage", "inputs": {"width": w, "height": h, "batch_size": 1}},
        "6": {"class_type": "CLIPTextEncode", "inputs": {"text": prompt, "clip": ["4", 1]}},
        "7": {"class_type": "CLIPTextEncode", "inputs": {"text": NEGATIVE, "clip": ["4", 1]}},
        "3": {"class_type": "KSampler", "inputs": {
            "seed": seed, "steps": 30, "cfg": 5.0, "sampler_name": "dpmpp_2m_sde", "scheduler": "karras",
            "denoise": 1.0, "model": ["4", 0], "positive": ["6", 0], "negative": ["7", 0], "latent_image": ["5", 0]}},
        "8": {"class_type": "VAEDecode", "inputs": {"samples": ["3", 0], "vae": ["4", 2]}},
        "9": {"class_type": "SaveImage", "inputs": {"filename_prefix": "aps", "images": ["8", 0]}},
    }


def _get(path: str):
    with urllib.request.urlopen(COMFY_URL + path, timeout=30) as r:
        return r.read()


def is_up() -> bool:
    try:
        _get("/system_stats")
        return True
    except Exception:
        return False


def generate(prompt: str, w: int, h: int, timeout: int = 600) -> Image.Image:
    if not is_up():
        raise RuntimeError("ComfyUI chal nahi raha. Notebook ka 'Start' cell dobara chalayein.")
    body = json.dumps({"prompt": workflow(prompt, w, h, random.randint(1, 2**31))}).encode()
    req = urllib.request.Request(COMFY_URL + "/prompt", data=body, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            pid = json.loads(r.read())["prompt_id"]
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
                    return Image.open(io.BytesIO(_get(f"/view?{q}"))).convert("RGB")
        time.sleep(1.5)
    raise RuntimeError("Image banne mein bahut time lag gaya (timeout).")
