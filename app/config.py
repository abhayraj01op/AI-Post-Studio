"""Central settings. Every file the app makes lives inside Google Drive (BASE)."""
import os
from pathlib import Path

BASE = Path(os.environ.get("APS_BASE", "/content/drive/MyDrive/AI_Post_Studio"))
DATA = BASE / "data"
IMAGES_DIR = DATA / "images"
POSTS_DIR = DATA / "posts"
BIODATA_DIR = DATA / "biodata"
FONTS_DIR = BASE / "fonts"
DB_FILE = DATA / "db.json"

COMFY_URL = os.environ.get("APS_COMFY_URL", "http://127.0.0.1:8188")
CHECKPOINT = os.environ.get("APS_CHECKPOINT", "RealVisXL_V5.0_fp16.safetensors")
TEXT_MODEL = os.environ.get("APS_TEXT_MODEL", "Qwen/Qwen2.5-7B-Instruct")
HF_CACHE = BASE / "hf_cache"

# Same choices as the web app
CATEGORIES = ["Marriage", "Friendship", "Dating", "Remarriage", "Gharjamai"]
SUBJECTS = {
    "Couple": "Couple",
    "Female": "Sirf ladki (Female)",
    "Male": "Sirf ladka (Male)",
    "BetiMaa": "Ladki + uski mammi",
    "BetaMaa": "Ladka + buzurg mammi",
}
# label -> (final w, h, generation w, h) ; SDXL-friendly generation sizes
SIZES = {
    "1080x1080 (Square)": (1080, 1080, 1024, 1024),
    "1080x1350 (Portrait)": (1080, 1350, 896, 1120),
    "1080x1920 (Story)": (1080, 1920, 768, 1344),
}
POST_TYPES = {
    "Normal": "Normal",
    "Couple": "Couple (romantic, seedha viewer se)",
    "MaaAkeli": "MaaAkeli (maa ke saath akeli, ghar jamai chahiye)",
    "BinaPapa": "BinaPapa (maa bol rahi, papa nahi, dahej nahi)",
    "Anath": "Anath (orphan)",
}
STATES = [
    "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh", "Delhi", "Goa", "Gujarat",
    "Haryana", "Himachal Pradesh", "Jammu & Kashmir", "Jharkhand", "Karnataka", "Kerala", "Madhya Pradesh",
    "Maharashtra", "Manipur", "Meghalaya", "Mizoram", "Nagaland", "Odisha", "Punjab", "Rajasthan", "Sikkim",
    "Tamil Nadu", "Telangana", "Tripura", "Uttar Pradesh", "Uttarakhand", "West Bengal", "Chandigarh",
]
STATE_WEIGHTS = {
    "Uttar Pradesh": 24, "Maharashtra": 12, "Bihar": 12, "West Bengal": 10, "Madhya Pradesh": 8, "Rajasthan": 8,
    "Tamil Nadu": 7, "Gujarat": 7, "Karnataka": 6, "Andhra Pradesh": 5, "Odisha": 4, "Telangana": 4, "Kerala": 3,
    "Jharkhand": 4, "Assam": 3, "Punjab": 3, "Chhattisgarh": 3, "Haryana": 3, "Delhi": 2, "Uttarakhand": 1,
}
COMMUNITIES = [
    "Hindu", "Muslim", "Sikh", "Jain", "Christian", "Brahmin", "Rajput", "Yadav", "Jat", "Kurmi",
    "Baniya / Agarwal", "Kayastha", "Gupta", "Maratha", "Gujjar", "Kushwaha", "Teli", "Lodhi", "SC / ST", "Buddhist",
]
MARITAL = ["Divorced", "Widow/Widower", "Separated"]
EDUCATION = ["10वीं", "12वीं", "बी.ए.", "बी.कॉम", "आई.टी.आई.", "डिप्लोमा", "ग्रेजुएट"]
NAME_BLOCK_DAYS = 4


def ensure_dirs():
    for d in (DATA, IMAGES_DIR, POSTS_DIR, BIODATA_DIR, FONTS_DIR, HF_CACHE):
        d.mkdir(parents=True, exist_ok=True)
ALL_STATES_LABEL = "All"
