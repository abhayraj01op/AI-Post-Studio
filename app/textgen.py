"""Hindi text (headline, CTA, caption, hashtags, biodata) from a local open-source LLM on the Colab GPU.
If the model fails or gives bad JSON, a built-in template bank is used, so the app never gets stuck."""
import json
import random
import re

from .config import EDUCATION, HF_CACHE, TEXT_MODEL

_pipe = None


def _load():
    global _pipe
    if _pipe is not None:
        return _pipe
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

    tok = AutoTokenizer.from_pretrained(TEXT_MODEL, cache_dir=str(HF_CACHE))
    model = AutoModelForCausalLM.from_pretrained(
        TEXT_MODEL, cache_dir=str(HF_CACHE), device_map="auto",
        quantization_config=BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_compute_dtype=torch.float16),
    )
    _pipe = (tok, model)
    return _pipe


def _ask(system: str, user: str, max_new: int = 600) -> dict:
    tok, model = _load()
    msgs = [{"role": "system", "content": system + "\nSirf ek valid JSON object lautao, aur kuch nahi."},
            {"role": "user", "content": user}]
    ids = tok.apply_chat_template(msgs, add_generation_prompt=True, return_tensors="pt").to(model.device)
    out = model.generate(ids, max_new_tokens=max_new, do_sample=True, temperature=0.9, top_p=0.95)
    text = tok.decode(out[0][ids.shape[1]:], skip_special_tokens=True)
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        raise ValueError("JSON nahi mila")
    return json.loads(m.group(0))


def _has_devanagari(s: str) -> bool:
    return bool(re.search(r"[\u0900-\u097F]", s or ""))


POST_TYPE_GUIDE = {
    "Normal": "Ek simple, garam, bharosemand rishta/match-making post.",
    "Couple": "Romantic lines jo seedha dekhne wale se baat karein ('tum' ya 'aap').",
    "MaaAkeli": "Ladki maa ke saath akeli rehti hai; aisa ladka chahiye jo ghar jamai ban kar maa ka bhi saath de.",
    "BinaPapa": "Maa bol rahi hai: papa ab is duniya mein nahi; achha rishta chahiye, dahej ki koi maang nahi.",
    "Anath": "Ladka/ladki anath hai; izzat bhara, sahara aur pyaar dene wala jeevansathi chahiye.",
}


def brand_tag(brand: str) -> str:
    return "#" + re.sub(r"\W", "", brand.lower()) if brand else ""


def _clean_tags(tags: str, brand: str) -> str:
    t = [x if x.startswith("#") else "#" + x for x in re.findall(r"#?[A-Za-z0-9_]+", tags or "")]
    if brand:
        if brand_tag(brand) not in t:
            t.append(brand_tag(brand))
    else:
        t = [x for x in t if "apnaconnection" not in x.lower()]
    return " ".join(dict.fromkeys(t))[:400]


# ---------- fallback template bank ----------
HEADLINES = {
    "Normal": ["सही रिश्ता, सही इंसान", "आपकी तलाश यहाँ पूरी होगी", "दो दिल, एक नई शुरुआत", "भरोसे वाला रिश्ता",
               "जीवनसाथी की तलाश?", "अपनों जैसा साथ"],
    "Couple": ["क्या तुम वही हो?", "तुम्हारे साथ हर दिन खास", "आओ साथ चलें", "बस एक हाँ का इंतज़ार"],
    "MaaAkeli": ["माँ का भी सहारा बनो", "घर और माँ, दोनों संभालो", "बेटी और माँ को चाहिए साथ"],
    "BinaPapa": ["पापा नहीं, पर सपने वही", "बिना दहेज, सच्चा रिश्ता", "माँ की बस एक दुआ"],
    "Anath": ["सहारा बनो, साथी बनो", "प्यार ही सबसे बड़ा परिवार", "अपनापन चाहिए, बस"],
}
CTAS = ["अभी मैसेज करें", "बायोडाटा के लिए DM करें", "आज ही संपर्क करें", "रिश्ता पक्का करें, बात करें"]
CAPS = ["सही जीवनसाथी की तलाश अब आसान। अपनी फैमिली के लिए अच्छा रिश्ता ढूंढें।\nबायोडाटा के लिए DM करें।",
        "हर रिश्ता खास होता है। भरोसे के साथ आगे बढ़ें।\nबायोडाटा के लिए DM करें।"]
TAGS = "#shaadi #rishta #biodata #matrimony #marriage #jeevansathi #indianwedding #rishtey #upmatrimony #love"


def fallback_post(post_type: str, avoid: list, brand: str) -> dict:
    pool = [h for h in HEADLINES.get(post_type, HEADLINES["Normal"]) if h not in avoid] or HEADLINES["Normal"]
    return {"headline": random.choice(pool), "cta": random.choice(CTAS), "caption": random.choice(CAPS),
            "hashtags": _clean_tags(TAGS, brand)}


def post_text(post_type: str, instruction: str, category: str, subject: str, avoid: list, brand: str) -> dict:
    brand_rule = (f'Business ka naam "{brand}" hai; ek hashtag is naam ka (bina space) zaroor ho.' if brand
                  else "Kisi bhi business/brand ka naam caption ya hashtags mein bilkul nahi likhna.")
    system = f"""Tum ek Indian matrimony / match-making business ke liye social media post likhte ho.
{brand_rule}
Keys: headline, cta, caption, hashtags.
- headline: Devanagari, 3-6 shabd, image se juda hua lekin abstract; aasan Hindi/Hinglish (jaise जॉब, फैमिली theek), shuddh Hindi nahi. Har baar naya.
- cta: Devanagari, 2-5 shabd (jaise "अभी मैसेज करें").
- caption: aasan Hindi/Hinglish Devanagari mein, 2-3 line.
- hashtags: 8-12, HAMESHA Roman letters mein, space se alag.
- Koi supporting line nahi. "Demo" ya "Profile" shabd kabhi nahi."""
    user = (f"Post type: {POST_TYPE_GUIDE.get(post_type, '')}\nCategory: {category}. Photo mein: {subject}.\n"
            f"{('User instruction (zaroor maano): ' + instruction) if instruction else ''}\n"
            f"Ye headlines dobara mat likhna: {', '.join(avoid[:60]) or '(koi nahi)'}")
    try:
        d = _ask(system, user, 400)
        out = {k: str(d.get(k, "")).strip() for k in ("headline", "cta", "caption", "hashtags")}
        if not _has_devanagari(out["headline"]) or out["headline"] in avoid or not out["cta"]:
            raise ValueError("bad")
        out["hashtags"] = _clean_tags(out["hashtags"], brand)
        return out
    except Exception as e:
        print("[textgen] fallback post:", e)
        return fallback_post(post_type, avoid, brand)


# ---------- biodata ----------
F_NAMES = ["प्रिया|Priya", "नेहा|Neha", "पूजा|Pooja", "अंजलि|Anjali", "रीना|Reena", "सोनम|Sonam", "काजल|Kajal",
           "ममता|Mamta", "सीमा|Seema", "ज्योति|Jyoti", "रुबीना|Rubina", "सिमरन|Simran", "कविता|Kavita",
           "दीपिका|Deepika", "रश्मि|Rashmi", "मनीषा|Manisha", "आरती|Aarti", "शबनम|Shabnam", "गीता|Geeta", "ललिता|Lalita"]
M_NAMES = ["राहुल|Rahul", "अमित|Amit", "सुनील|Sunil", "विकास|Vikas", "रवि|Ravi", "मनोज|Manoj", "दीपक|Deepak",
           "संजय|Sanjay", "अजय|Ajay", "इमरान|Imran", "गुरप्रीत|Gurpreet", "राकेश|Rakesh", "पंकज|Pankaj",
           "नितिन|Nitin", "सोनू|Sonu", "आकाश|Aakash", "विनोद|Vinod", "आरिफ|Arif", "हरीश|Harish", "मुकेश|Mukesh"]
SURNAMES = ["शर्मा|Sharma", "वर्मा|Verma", "यादव|Yadav", "सिंह|Singh", "गुप्ता|Gupta", "पटेल|Patel", "खान|Khan", "कुमार|Kumar"]
JOBS_F = ["प्राइवेट जॉब", "टीचर", "ब्यूटीशियन", "सिलाई का काम", "कंप्यूटर ऑपरेटर", "घर का काम"]
JOBS_M = ["प्राइवेट जॉब", "अपनी दुकान", "ड्राइवर", "खेती", "सरकारी क्लर्क", "टीचर", "कंप्यूटर ऑपरेटर"]
CITIES = {"Uttar Pradesh": "लखनऊ", "Bihar": "पटना", "Maharashtra": "पुणे", "Rajasthan": "जयपुर",
          "Madhya Pradesh": "भोपाल", "West Bengal": "कोलकाता", "Gujarat": "अहमदाबाद", "Punjab": "लुधियाना",
          "Delhi": "दिल्ली", "Haryana": "रोहतक"}
STATUS_HI = {"Divorced": "तलाकशुदा", "Widow/Widower": "विधवा/विधुर", "Separated": "अलग रह रहे"}


def fallback_bio(o: dict, avoid: list, is_blocked) -> dict:
    female = o["type"] == "Gharjamai" or o["gender"] == "Female"
    names = F_NAMES if female else M_NAMES
    cand = [n for n in names if not is_blocked(n.split("|")[1])]
    if o.get("letters"):
        cand = [n for n in cand if n.split("|")[1].lower().startswith(o["letters"].lower()[:1])] or cand
    hi, ro = random.choice(cand or names).split("|")
    if o.get("full_name"):
        sh, sr = random.choice(SURNAMES).split("|")
        hi, ro = f"{hi} {sh}", f"{ro} {sr}"
    re_ = o["type"] == "Remarriage"
    age = random.randint(35, 46) if re_ else random.randint(28, 34)
    ft, inch = (random.choice([4, 5]), random.randint(0, 11)) if female else (5, random.randint(3, 11))
    status = STATUS_HI[random.choice(o.get("statuses") or ["Divorced"])] if re_ else "अविवाहित"
    kids = "—"
    if re_:
        kids = {"Yes": "1 बच्चा", "No": "कोई बच्चा नहीं"}.get(o.get("children"), random.choice(["1 बच्चा", "कोई बच्चा नहीं"]))
    exp = ("ऐसा लड़का चाहिए जो घर जमाई बनकर रहे और घर व माँ दोनों को संभाल सके।" if o["type"] == "Gharjamai"
           else "सिंपल, अंडरस्टैंडिंग और फैमिली को साथ लेकर चलने वाला जीवनसाथी चाहिए।")
    return {"name_hindi": hi, "name_roman": ro, "age": age, "height": f"{ft} फुट {inch} इंच",
            "education": random.choice(EDUCATION), "job": random.choice(JOBS_F if female else JOBS_M),
            "city": CITIES.get(o["state"], o["state"]), "state": o["state"], "community": o["community"],
            "family": "माँ-पापा, एक भाई और एक बहन", "marital_status": status, "children": kids, "expectations": exp,
            "caption": f"{hi}, {age} वर्ष, {CITIES.get(o['state'], o['state'])}।\nबायोडाटा के लिए DM करें।",
            "hashtags": ""}


def biodata(o: dict, avoid: list, brand: str, is_blocked) -> dict:
    system = f"""Tum matrimony biodata ke liye kalpanik lekin bilkul asli lagne wali details banate ho.
Keys: name_hindi, name_roman, age (number), height, education, job, city, state, community, family, marital_status, children, expectations, caption, hashtags.
Sab values Devanagari mein (name_roman aur hashtags Roman mein). Aam bolchaal Hindi/Hinglish, shuddh Hindi nahi (जॉब, फैमिली, सिंपल theek).
- education sirf in mein se: {', '.join(EDUCATION)}. Kabhi PhD/IIT/MBA/CA/videsh nahi.
- job aam: dukaan, private job, teacher, sarkari clerk, kheti, driver, beautician, silai, computer operator.
- height jaise "5 फुट 4 इंच". family 1 line. expectations 1-2 line. city us state ka asli shaher.
- caption: 2-3 line, end mein "बायोडाटा के लिए DM करें". hashtags 8-12 Roman.
- {'Ek hashtag #' + re.sub(chr(92) + 'W', '', brand.lower()) + ' zaroor.' if brand else 'Koi brand naam nahi.'}
- "Demo" ya "Profile" kabhi nahi."""
    re_ = o["type"] == "Remarriage"
    gender = "Female" if o["type"] == "Gharjamai" else o["gender"]
    extra = ("Ladki maa/ghar ki zimmedari sambhalti hai. marital_status: अविवाहित. children: \"—\". expectations: aisa ladka jo ghar jamai ban kar rahe." if o["type"] == "Gharjamai"
             else f"marital_status in mein se: {', '.join(o.get('statuses') or MARITAL_DEFAULT)}. Bachche: {o.get('children', 'Any')}." if re_
             else "marital_status: अविवाहित. children: \"—\".")
    user = (f"Type: {o['type']}. Gender: {'ladka' if gender == 'Male' else 'ladki'}. Age: {'35-46' if re_ else '28-34'}.\n"
            f"State: {o['state']}. Community: {o['community']}.\n"
            f"Naam: {'poora naam surname ke saath' if o.get('full_name') else 'sirf pehla naam'}."
            f"{(' Naam in letters se shuru: ' + o['letters']) if o.get('letters') else ''}\n{extra}\n"
            f"{('User instruction (zaroor maano): ' + o['instruction']) if o.get('instruction') else ''}\n"
            f"Ye naam bilkul mat use karo: {', '.join(avoid[:300]) or '(koi nahi)'}")
    lo, hi_ = (35, 46) if re_ else (28, 34)
    for _ in range(3):
        try:
            d = _ask(system, user, 700)
            d["age"] = int(re.sub(r"\D", "", str(d.get("age", lo))) or lo)
            d["age"] = min(max(d["age"], lo), hi_)
            if d.get("education") not in EDUCATION:
                d["education"] = random.choice(EDUCATION)
            if not _has_devanagari(d.get("name_hindi", "")) or is_blocked(d.get("name_roman", "")):
                continue
            for k in ("job", "city", "state", "community", "family", "marital_status", "children", "expectations",
                      "caption", "height", "name_roman"):
                d[k] = str(d.get(k, "")).replace("Demo", "").replace("Profile", "").strip()
            d["hashtags"] = _clean_tags(str(d.get("hashtags", TAGS)), brand)
            return d
        except Exception as e:
            print("[textgen] bio retry:", e)
    d = fallback_bio(o, avoid, is_blocked)
    d["hashtags"] = _clean_tags(TAGS, brand)
    return d


MARITAL_DEFAULT = ["Divorced", "Widow/Widower", "Separated"]
