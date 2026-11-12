"""Hindi text (headline, CTA, caption, hashtags, biodata) from a local open-source LLM on the Colab GPU.
If the model fails or gives bad JSON, a built-in template bank is used, so the app never gets stuck."""
import json
import random
import re

from .config import BIO_AGE, EDUCATION, HF_CACHE, TEXT_MODEL, age_range

_pipe = None
_failed = None


def _load():
    global _pipe, _failed
    if _pipe is not None:
        return _pipe
    if _failed:
        raise RuntimeError(_failed)  # don't retry a broken model again and again
    if TEXT_MODEL.startswith("Off"):
        _failed = "text model off; template use ho raha hai"
        raise RuntimeError(_failed)
    try:
        return _really_load()
    except Exception as e:
        _failed = f"text model off ({e}); template use ho raha hai"
        print("[textgen]", _failed)
        raise


def _really_load():
    global _pipe
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    tok = AutoTokenizer.from_pretrained(TEXT_MODEL, cache_dir=str(HF_CACHE))
    from transformers import BitsAndBytesConfig

    # 4-bit: ~1-2 GB of GPU instead of 3-6 GB, so the photo model keeps full room (better photos, no OOM)
    q = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_compute_dtype=torch.float16, bnb_4bit_quant_type="nf4")
    model = AutoModelForCausalLM.from_pretrained(
        TEXT_MODEL, cache_dir=str(HF_CACHE), device_map="cuda", quantization_config=q,
        low_cpu_mem_usage=True,
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
    "Divorcee": "Divorce ke baad nayi shuruaat; samajhdar, izzat dene wala saathi chahiye.",
    "Widow": "Jeevansathi ke jaane ke baad phir se saath; dil se apnane wala rishta.",
    "BinaDahej": "Bina dahej, sirf achhe sanskar aur samajh wala rishta.",
    "Govt": "Sarkari naukri wale ladke/ladki ka rishta; settled aur secure future.",
    "Business": "Apna business/dukaan; mehnati, settled ladka; family-oriented rishta.",
    "NRI": "Bahar (Dubai/USA/UK) rehne wala settled rishta; video call se baat.",
    "LateMarriage": "Umar 35+ hai par sapne wahi; der se sahi, sahi rishta.",
    "Friendship": "Sirf dosti aur achhi baat-cheet; izzat aur bharose wali friendship. Shaadi ka zikr nahi.",
    "Dating": "Serious dating, milna-julna, ek doosre ko samajhna; decent aur respectful tone.",
    "Urgent": "Jaldi shaadi karni hai; family ready hai; turant sampark karein.",
    "Testimonial": "Success story: humare zariye ek jodi ki shaadi ho gayi; khushi aur bharosa.",
    "Festival": "Tyohaar ki shubhkamnayein + is tyohaar apna jeevansathi dhoondhein.",
}

HINGLISH = "Hinglish = Hindi ke shabd ROMAN/English letters mein (jaise 'Sahi rishta, sahi insaan'). Devanagari bilkul nahi."
HINDI = "Aasan bolchaal Hindi DEVANAGARI mein, English ke aam shabd chalenge (जॉब, फैमिली). Shuddh/kathin Hindi bilkul nahi."


def lang_rule(lang: str) -> str:
    return HINGLISH if (lang or "").startswith("Hinglish") else HINDI


def is_hinglish(lang: str) -> bool:
    return (lang or "").startswith("Hinglish")


def _lang_ok(text: str, lang: str) -> bool:
    return (not _has_devanagari(text)) if is_hinglish(lang) else _has_devanagari(text)


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
HEADLINES_R = {
    "Normal": ["Sahi rishta, sahi insaan", "Aapki talaash yahan poori hogi", "Do dil, ek nayi shuruaat", "Bharose wala rishta",
               "Jeevansathi ki talaash?", "Apno jaisa saath"],
    "Couple": ["Kya tum wahi ho?", "Tumhare saath har din khaas", "Aao saath chalein", "Bas ek haan ka intezaar"],
    "MaaAkeli": ["Maa ka bhi sahara bano", "Ghar aur maa, dono sambhalo"],
    "BinaPapa": ["Papa nahi, par sapne wahi", "Bina dahej, sachcha rishta"],
    "Anath": ["Sahara bano, saathi bano", "Pyaar hi sabse bada parivaar"],
    "Friendship": ["Ek achha dost chahiye?", "Dosti ki nayi shuruaat"],
    "Dating": ["Milte hain, samajhte hain", "Coffee pe chalein?"],
    "Urgent": ["Jaldi shaadi, sahi rishta", "Family ready hai!"],
}
CTAS_R = ["Abhi message karein", "Biodata ke liye DM karein", "Aaj hi sampark karein", "Baat karein, rishta pakka karein"]
CAPS_R = ["Sahi jeevansathi ki talaash ab aasaan. Apni family ke liye achha rishta dhoondhein.\nBiodata ke liye DM karein.",
          "Har rishta khaas hota hai. Bharose ke saath aage badhein.\nBiodata ke liye DM karein."]
TAGS = "#shaadi #rishta #biodata #matrimony #marriage #jeevansathi #indianwedding #rishtey #upmatrimony #love"


def fallback_post(post_type: str, avoid: list, brand: str, lang: str = "Hindi") -> dict:
    H, C, P = (HEADLINES_R, CTAS_R, CAPS_R) if is_hinglish(lang) else (HEADLINES, CTAS, CAPS)
    pool = [h for h in H.get(post_type, H["Normal"]) if h not in avoid] or H["Normal"]
    return {"headline": random.choice(pool), "cta": random.choice(C), "caption": random.choice(P),
            "hashtags": _clean_tags(TAGS, brand)}


def _strip_brand(t: str, brand: str) -> str:
    """Brand na diya ho to kisi bhi purane/default brand ka naam hata do."""
    if brand:
        return t
    return re.sub(r"(?i)apna\s*connection", "", t or "").strip()


def post_field(field: str, post_type: str, instruction: str, category: str, subject: str, current: dict,
               brand: str, lang: str) -> str:
    """Sirf ek cheez (headline / cta / caption / hashtags) dobara likho; baaki wahi rahe."""
    avoid = [current.get(field, "")]
    for _ in range(3):
        t = post_text(post_type, instruction, category, subject, avoid, brand, lang)[field]
        if t and t not in avoid:
            return t
        avoid.append(t)
    return t


def post_text(post_type: str, instruction: str, category: str, subject: str, avoid: list, brand: str,
              lang: str = "Hindi") -> dict:
    brand_rule = (f'Business ka naam "{brand}" hai; ek hashtag is naam ka (bina space) zaroor ho.' if brand
                  else "Kisi bhi business/brand/company ka naam caption, headline ya hashtags mein BILKUL nahi likhna.")
    lo, hi = age_range(category)
    system = f"""Tum ek Indian matrimony / match-making business ke liye social media post likhte ho.
{brand_rule}
Bhasha: {lang_rule(lang)}
Keys: headline, cta, caption, hashtags.
- headline: 3-6 shabd, image se juda hua lekin abstract. Har baar naya.
- cta: 2-5 shabd (jaise "Abhi message karein" / "अभी मैसेज करें").
- caption: 2-3 line. Umar ka zikr ho to {lo}+ hi.
- hashtags: 8-12, HAMESHA Roman letters mein, space se alag.
- Koi supporting line nahi. "Demo" ya "Profile" shabd kabhi nahi."""
    user = (f"Post type: {POST_TYPE_GUIDE.get(post_type, '')}\nCategory: {category}. Photo mein: {subject}.\n"
            f"{('User instruction (zaroor maano): ' + instruction) if instruction else ''}\n"
            f"Ye headlines dobara mat likhna: {', '.join(avoid[:60]) or '(koi nahi)'}")
    try:
        d = _ask(system, user, 400)
        out = {k: _strip_brand(str(d.get(k, "")).strip(), brand) for k in ("headline", "cta", "caption", "hashtags")}
        if not _lang_ok(out["headline"], lang) or out["headline"] in avoid or not out["cta"]:
            raise ValueError("bad")
        out["hashtags"] = _clean_tags(out["hashtags"], brand)
        return out
    except Exception as e:
        print("[textgen] fallback post:", e)
        return fallback_post(post_type, avoid, brand, lang)


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
STATUS_HI = {"Divorced": "तलाकशुदा", "Widow/Widower": "विधवा/विधुर", "Separated": "अलग रह रहे"}

CITY_CHOICES = {
    "Andhra Pradesh": ["विशाखापत्तनम", "विजयवाड़ा", "गुंटूर", "तिरुपति"],
    "Arunachal Pradesh": ["ईटानगर", "नाहरलागुन", "जीरो"], "Assam": ["गुवाहाटी", "डिब्रूगढ़", "सिलचर", "जोरहाट"],
    "Bihar": ["पटना", "गया", "मुजफ्फरपुर", "भागलपुर"], "Chhattisgarh": ["रायपुर", "भिलाई", "बिलासपुर", "दुर्ग"],
    "Delhi": ["दिल्ली"], "Goa": ["पणजी", "मडगांव"], "Gujarat": ["अहमदाबाद", "सूरत", "वडोदरा", "राजकोट"],
    "Haryana": ["रोहतक", "गुरुग्राम", "करनाल", "हिसार"], "Himachal Pradesh": ["शिमला", "धर्मशाला", "सोलन", "मंडी"],
    "Jammu & Kashmir": ["श्रीनगर", "जम्मू", "अनंतनाग", "बारामूला"], "Jharkhand": ["रांची", "जमशेदपुर", "धनबाद", "बोकारो"],
    "Karnataka": ["बेंगलुरु", "मैसूर", "हुबली", "मंगलुरु"], "Kerala": ["तिरुवनंतपुरम", "कोच्चि", "कोझिकोड", "त्रिशूर"],
    "Madhya Pradesh": ["भोपाल", "इंदौर", "जबलपुर", "ग्वालियर"], "Maharashtra": ["पुणे", "मुंबई", "नागपुर", "नाशिक", "कोल्हापुर"],
    "Manipur": ["इंफाल", "थौबल", "उखरुल"], "Meghalaya": ["शिलांग", "तुरा", "जोवाई"],
    "Mizoram": ["आइजोल", "लुंगलेई", "चम्फाई"], "Nagaland": ["कोहिमा", "दीमापुर", "मोकोकचुंग"],
    "Odisha": ["भुवनेश्वर", "कटक", "राउरकेला", "पुरी"], "Punjab": ["लुधियाना", "अमृतसर", "जालंधर", "पटियाला"],
    "Rajasthan": ["जयपुर", "जोधपुर", "उदयपुर", "कोटा"], "Sikkim": ["गंगटोक", "नामची", "गेजिंग"],
    "Tamil Nadu": ["चेन्नई", "कोयंबटूर", "मदुरै", "सलेम"], "Telangana": ["हैदराबाद", "वारंगल", "करीमनगर", "निजामाबाद"],
    "Tripura": ["अगरतला", "उदयपुर", "धर्मनगर"], "Uttar Pradesh": ["लखनऊ", "कानपुर", "वाराणसी", "आगरा", "प्रयागराज"],
    "Uttarakhand": ["देहरादून", "हरिद्वार", "ऋषिकेश", "रुद्रपुर"], "West Bengal": ["कोलकाता", "सिलीगुड़ी", "हावड़ा", "दुर्गापुर"],
    "Chandigarh": ["चंडीगढ़"],
}
CITIES = {state: choices[0] for state, choices in CITY_CHOICES.items()}


ROMAN = {
    'प्राइवेट जॉब': 'Private job', 'टीचर': 'Teacher', 'ब्यूटीशियन': 'Beautician',
    'सिलाई का काम': 'Silai ka kaam', 'कंप्यूटर ऑपरेटर': 'Computer operator', 'घर का काम': 'Ghar ka kaam',
    'अपनी दुकान': 'Apni dukaan', 'ड्राइवर': 'Driver', 'खेती': 'Kheti',
    'सरकारी क्लर्क': 'Sarkari clerk', '10वीं': '10th', '12वीं': '12th',
    'बी.ए.': 'B.A.', 'बी.कॉम': 'B.Com', 'आई.टी.आई.': 'ITI',
    'डिप्लोमा': 'Diploma', 'ग्रेजुएट': 'Graduate', 'तलाकशुदा': 'Divorced',
    'विधवा/विधुर': 'Widow/Widower', 'अलग रह रहे': 'Separated', 'अविवाहित': 'Unmarried',
    '1 बच्चा': '1 bachcha', 'कोई बच्चा नहीं': 'Koi bachcha nahi', 'माँ-पापा, एक भाई और एक बहन': 'Maa-papa, ek bhai aur ek behen',
    'लखनऊ': 'Lucknow', 'पटना': 'Patna', 'पुणे': 'Pune',
    'जयपुर': 'Jaipur', 'भोपाल': 'Bhopal', 'कोलकाता': 'Kolkata',
    'अहमदाबाद': 'Ahmedabad', 'लुधियाना': 'Ludhiana', 'दिल्ली': 'Delhi',
    'रोहतक': 'Rohtak', 'कानपुर': 'Kanpur', 'वाराणसी': 'Varanasi',
    'आगरा': 'Agra', 'प्रयागराज': 'Prayagraj', 'गया': 'Gaya',
    'मुजफ्फरपुर': 'Muzaffarpur', 'भागलपुर': 'Bhagalpur', 'मुंबई': 'Mumbai',
    'नागपुर': 'Nagpur', 'नाशिक': 'Nashik', 'कोल्हापुर': 'Kolhapur',
    'जोधपुर': 'Jodhpur', 'उदयपुर': 'Udaipur', 'कोटा': 'Kota',
    'इंदौर': 'Indore', 'जबलपुर': 'Jabalpur', 'ग्वालियर': 'Gwalior',
    'सिलीगुड़ी': 'Siliguri', 'हावड़ा': 'Howrah', 'दुर्गापुर': 'Durgapur',
    'सूरत': 'Surat', 'वडोदरा': 'Vadodara', 'राजकोट': 'Rajkot',
    'अमृतसर': 'Amritsar', 'जालंधर': 'Jalandhar', 'पटियाला': 'Patiala',
    'गुरुग्राम': 'Gurugram', 'करनाल': 'Karnal', 'हिसार': 'Hisar',
    'विशाखापत्तनम': 'Visakhapatnam', 'विजयवाड़ा': 'Vijayawada', 'गुंटूर': 'Guntur',
    'तिरुपति': 'Tirupati', 'ईटानगर': 'Itanagar', 'नाहरलागुन': 'Naharlagun',
    'जीरो': 'Ziro', 'गुवाहाटी': 'Guwahati', 'डिब्रूगढ़': 'Dibrugarh',
    'सिलचर': 'Silchar', 'जोरहाट': 'Jorhat', 'रायपुर': 'Raipur',
    'भिलाई': 'Bhilai', 'बिलासपुर': 'Bilaspur', 'दुर्ग': 'Durg',
    'पणजी': 'Panaji', 'मडगांव': 'Margao', 'शिमला': 'Shimla',
    'धर्मशाला': 'Dharamshala', 'सोलन': 'Solan', 'मंडी': 'Mandi',
    'श्रीनगर': 'Srinagar', 'जम्मू': 'Jammu', 'अनंतनाग': 'Anantnag',
    'बारामूला': 'Baramulla', 'रांची': 'Ranchi', 'जमशेदपुर': 'Jamshedpur',
    'धनबाद': 'Dhanbad', 'बोकारो': 'Bokaro', 'बेंगलुरु': 'Bengaluru',
    'मैसूर': 'Mysuru', 'हुबली': 'Hubballi', 'मंगलुरु': 'Mangaluru',
    'तिरुवनंतपुरम': 'Thiruvananthapuram', 'कोच्चि': 'Kochi', 'कोझिकोड': 'Kozhikode',
    'त्रिशूर': 'Thrissur', 'इंफाल': 'Imphal', 'थौबल': 'Thoubal',
    'शिलांग': 'Shillong', 'तुरा': 'Tura', 'जोवाई': 'Jowai',
    'आइजोल': 'Aizawl', 'लुंगलेई': 'Lunglei', 'चम्फाई': 'Champhai',
    'कोहिमा': 'Kohima', 'दीमापुर': 'Dimapur', 'मोकोकचुंग': 'Mokokchung',
    'भुवनेश्वर': 'Bhubaneswar', 'कटक': 'Cuttack', 'राउरकेला': 'Rourkela',
    'पुरी': 'Puri', 'गंगटोक': 'Gangtok', 'नामची': 'Namchi',
    'चेन्नई': 'Chennai', 'कोयंबटूर': 'Coimbatore', 'मदुरै': 'Madurai',
    'सलेम': 'Salem', 'हैदराबाद': 'Hyderabad', 'वारंगल': 'Warangal',
    'करीमनगर': 'Karimnagar', 'निजामाबाद': 'Nizamabad', 'अगरतला': 'Agartala',
    'धर्मनगर': 'Dharmanagar', 'देहरादून': 'Dehradun', 'हरिद्वार': 'Haridwar',
    'ऋषिकेश': 'Rishikesh', 'रुद्रपुर': 'Rudrapur', 'चंडीगढ़': 'Chandigarh',
}


FAMILY_LINES = [
    ('माँ-पापा और भाई-बहनों के साथ अपनापन भरा परिवार।', 'Maa-papa aur bhai-behno ke saath apnapan bhara parivaar.'),
    ('सादा, मिलजुला परिवार जो रिश्तों को दिल से निभाता है।', 'Saada, mil-jula parivaar jo rishton ko dil se nibhata hai.'),
    ('परिवार में प्यार, बातचीत और एक-दूसरे का साथ अहम है।', 'Parivaar mein pyaar, baatcheet aur ek-doosre ka saath aham hai.'),
    ('छोटा और खुशमिजाज परिवार, जहाँ सब एक-दूसरे का ख्याल रखते हैं।', 'Chhota aur khushmizaaj parivaar, jahan sab ek-doosre ka khayal rakhte hain.'),
    ('संस्कार और आपसी सम्मान को मानने वाला परिवार।', 'Sanskaar aur aapsi sammaan ko maan-ne wala parivaar.'),
    ('अपनेपन और सादगी से जुड़ा हुआ परिवार।', 'Apnepan aur saadgi se juda hua parivaar.'),
    ('परिवार के फैसले मिल-बैठकर और समझदारी से लिए जाते हैं।', 'Parivaar ke faisle mil-baithkar aur samajhdaari se liye jaate hain.'),
    ('काम और परिवार, दोनों में एक-दूसरे का हौसला बढ़ाते हैं।', 'Kaam aur parivaar, dono mein ek-doosre ka hausla badhaate hain.'),
    ('मेहमाननवाजी और रिश्तों की कद्र करने वाला परिवार।', 'Mehmaan-nawaazi aur rishton ki kadar karne wala parivaar.'),
    ('साथ समय बिताना और अपनों की मदद करना परिवार की पहचान है।', 'Saath samay bitaana aur apnon ki madad karna parivaar ki pehchaan hai.'),
    ('नई सोच और पारिवारिक मूल्यों का संतुलन रखने वाला परिवार।', 'Nayi soch aur parivaarik values ka santulan rakhne wala parivaar.'),
    ('स्नेह और भरोसे के साथ आगे बढ़ता हुआ परिवार।', 'Sneh aur bharose ke saath aage badhta hua parivaar.'),
    ('घर में सबकी राय सुनी जाती है और मिलकर फैसले होते हैं।', 'Ghar mein sabki rai suni jaati hai aur milkar faisle hote hain.'),
    ('अपनों की छोटी उपलब्धियों पर पूरा परिवार खुश होता है।', 'Apnon ki chhoti uplabdhiyon par poora parivaar khush hota hai.'),
    ('परिवार में जिम्मेदारी और खुशियाँ सब मिलकर बाँटते हैं।', 'Parivaar mein zimmedari aur khushiyan sab milkar baantte hain.'),
    ('सादा जीवन और एक-दूसरे का साथ इस परिवार की खूबी है।', 'Saada jeevan aur ek-doosre ka saath is parivaar ki khoobi hai.'),
    ('रिश्तों में अपनापन और व्यवहार में गर्मजोशी रहती है।', 'Rishton mein apnapan aur vyavhaar mein garmajoshi rehti hai.'),
    ('परिवार के सभी सदस्य अपने काम और शौक आगे बढ़ाते हैं।', 'Parivaar ke sabhi sadasya apne kaam aur shauk aage badhaate hain.'),
    ('त्योहार और परिवार के साथ मिलना-जुलना सबको पसंद है।', 'Tyohaar aur parivaar ke saath milna-julna sabko pasand hai.'),
    ('घर में बातचीत, हँसी और एक-दूसरे की मदद का माहौल है।', 'Ghar mein baatcheet, hansi aur ek-doosre ki madad ka mahaul hai.'),
    ('परिवार के लोग अपने सपनों के लिए एक-दूसरे का हौसला बढ़ाते हैं।', 'Parivaar ke log apne sapnon ke liye ek-doosre ka hausla badhaate hain.'),
    ('साथ बैठकर खाना और दिन की बातें परिवार को जोड़ती हैं।', 'Saath baithkar khaana aur din ki baatein parivaar ko jodti hain.'),
    ('परिवार में हर सदस्य को आगे बढ़ने की आजादी मिलती है।', 'Parivaar mein har sadasya ko aage badhne ki azaadi milti hai.'),
    ('अपनों की देखभाल और आपसी सम्मान घर का हिस्सा हैं।', 'Apnon ki dekhbhaal aur aapsi sammaan ghar ka hissa hain.'),
    ('हर त्योहार सादगी और खुशी से साथ मनाया जाता है।', 'Har tyohaar saadgi aur khushi se saath manaaya jaata hai.'),
    ('काम के बाद परिवार के साथ समय बिताना सबको अच्छा लगता है।', 'Kaam ke baad parivaar ke saath samay bitaana sabko achha lagta hai.'),
    ('बड़ों का अनुभव और बच्चों की हँसी घर को खास बनाते हैं।', 'Bado ka anubhav aur bachchon ki hansi ghar ko khaas banaate hain.'),
    ('परिवार में पढ़ाई, काम और रिश्तों को बराबर अहमियत मिलती है।', 'Parivaar mein padhaai, kaam aur rishton ko baraabar ahmiyat milti hai.'),
    ('मेहमानों का स्वागत और अपनों का साथ इस घर की पहचान है।', 'Mehmaano ka swaagat aur apnon ka saath is ghar ki pehchaan hai.'),
    ('परिवार के लोग मिलकर मुश्किल समय को आसान बना देते हैं।', 'Parivaar ke log milkar mushkil samay ko aasaan bana dete hain.'),
    ('घर में सादगी है और हर रिश्ते में भरोसा है।', 'Ghar mein saadgi hai aur har rishte mein bharosa hai.'),
    ('अपने काम में मेहनत और घर में हँसी दोनों साथ चलते हैं।', 'Apne kaam mein mehnat aur ghar mein hansi dono saath chalte hain.'),
]
ATTRACTIVE_LINES = [
    ('सादगी और मुस्कान से हर मुलाकात खास बनती है।', 'Saadgi aur muskaan se har mulaqat khaas banti hai.'),
    ('अपने लोगों के साथ छोटी खुशियाँ मनाना मुझे पसंद है।', 'Apne logon ke saath chhoti khushiyan manana mujhe pasand hai.'),
    ('मेहनत, अपनापन और हँसी—यही मेरी पहचान है।', 'Mehnat, apnapan aur hansi—yahi meri pehchaan hai.'),
    ('नई बातें सीखना और अपने सपनों की ओर बढ़ना अच्छा लगता है।', 'Nayi baatein seekhna aur apne sapnon ki ore badhna achha lagta hai.'),
    ('घर की गर्माहट और दिल की सच्चाई मेरे लिए खास है।', 'Ghar ki garmahat aur dil ki sachchai mere liye khaas hai.'),
    ('खुशमिजाज स्वभाव और सच्चे रिश्ते मेरी छोटी-सी दुनिया हैं।', 'Khushmizaaj swabhaav aur sachche rishte meri chhoti-si duniya hain.'),
    ('अपनों के साथ बिताया समय सबसे प्यारी याद बन जाता है।', 'Apnon ke saath bitaaya samay sabse pyaari yaad ban jaata hai.'),
    ('जिंदगी की छोटी बातों में भी खुशी ढूँढना अच्छा लगता है।', 'Zindagi ki chhoti baaton mein bhi khushi dhoondna achha lagta hai.'),
    ('अपनेपन से भरा घर और सुकून भरी शामें मुझे पसंद हैं।', 'Apnepan se bhara ghar aur sukoon bhari shaamein mujhe pasand hain.'),
    ('ईमानदारी और हँसी से दिन अपने आप खूबसूरत हो जाता है।', 'Imaandari aur hansi se din apne aap khoobsurat ho jaata hai.'),
    ('रिश्तों को समय देना और खुशियाँ बाँटना मेरी आदत है।', 'Rishton ko samay dena aur khushiyan baantna meri aadat hai.'),
    ('परिवार का साथ और नई उम्मीदें मेरी ताकत हैं।', 'Parivaar ka saath aur nayi umeedein meri taakat hain.'),
    ('मिलजुलकर रहना और सबका ख्याल रखना अच्छा लगता है।', 'Mil-julkar rehna aur sabka khayal rakhna achha lagta hai.'),
    ('दिल से सरल और अपने काम को लेकर जिम्मेदार हूँ।', 'Dil se saral aur apne kaam ko lekar zimmedaar hoon.'),
    ('अच्छी किताबें, मीठी बातें और परिवार मेरी पसंदीदा चीजें हैं।', 'Achhi kitaabein, meethi baatein aur parivaar meri pasandeeda cheezein hain.'),
    ('हर दिन कुछ नया सीखना मुझे आगे बढ़ाता है।', 'Har din kuch naya seekhna mujhe aage badhaata hai.'),
    ('सादा जीवन और अपनों की हँसी मेरे लिए बहुत मायने रखती है।', 'Saada jeevan aur apnon ki hansi mere liye bahut maayne rakhti hai.'),
    ('मेरी खुशी अपनों के चेहरे पर मुस्कान देखने में है।', 'Meri khushi apnon ke chehre par muskaan dekhne mein hai.'),
    ('प्यार से सजा घर और साथ में चाय मेरी छोटी खुशी है।', 'Pyaar se saja ghar aur saath mein chai meri chhoti khushi hai.'),
    ('मेहनत के साथ हर दिन को बेहतर बनाने की कोशिश रहती है।', 'Mehnat ke saath har din ko behtar banaane ki koshish rehti hai.'),
    ('सच्चे मन से निभाए रिश्ते जिंदगी को सुंदर बनाते हैं।', 'Sachche man se nibhaaye rishte zindagi ko sundar banaate hain.'),
    ('परिवार, काम और अपने शौक तीनों को समय देना पसंद है।', 'Parivaar, kaam aur apne shauk teeno ko samay dena pasand hai.'),
    ('मेरी दुनिया में अपनापन, सम्मान और ढेर सारी हँसी है।', 'Meri duniya mein apnapan, sammaan aur dher saari hansi hai.'),
    ('सुबह की चाय और परिवार की बातें दिन बना देती हैं।', 'Subah ki chai aur parivaar ki baatein din bana deti hain.'),
    ('सकारात्मक सोच और सच्ची मुस्कान साथ चलती हैं।', 'Sakaraatmak soch aur sachchi muskaan saath chalti hai.'),
    ('अपनी जड़ों से जुड़कर आगे बढ़ना मुझे अच्छा लगता है।', 'Apni jadon se judkar aage badhna mujhe achha lagta hai.'),
    ('छोटी-छोटी उपलब्धियों को परिवार के साथ मनाना पसंद है।', 'Chhoti-chhoti uplabdhiyon ko parivaar ke saath manana pasand hai.'),
    ('मेरे लिए सबसे खूबसूरत पल अपनों के साथ होते हैं।', 'Mere liye sabse khoobsurat pal apnon ke saath hote hain.'),
    ('दिल से अपनापन और बातों में सादगी रखना पसंद है।', 'Dil se apnapan aur baaton mein saadgi rakhna pasand hai.'),
    ('जिम्मेदारी निभाना और मुस्कुराते रहना दोनों जरूरी हैं।', 'Zimmedari nibhaana aur muskuraate rehna dono zaroori hain.'),
    ('हर रिश्ते में गर्मजोशी लाना मेरी छोटी-सी खूबी है।', 'Har rishte mein garmajoshi laana meri chhoti-si khoobi hai.'),
    ('सीखते रहना, मुस्कुराते रहना और अपनों के करीब रहना।', 'Seekhte rehna, muskuraate rehna aur apnon ke kareeb rehna.'),
]
PARTNER_LINES = ATTRACTIVE_LINES
GHARJAMAI_LINES = ATTRACTIVE_LINES

def fresh_bio_phrase(field: str, used_details: dict | None = None, lang: str = "Hindi", profile_type: str = "Marriage", current: str = "") -> str:
    pool = ATTRACTIVE_LINES if field == "expectations" else FAMILY_LINES
    column = 1 if is_hinglish(lang) else 0
    used = {" ".join(str(value).lower().split()) for value in (used_details or {}).get(field, [])}
    current_key = " ".join(str(current).lower().split())
    choices = [pair[column] for pair in pool]
    available = [value for value in choices if " ".join(value.lower().split()) not in used and " ".join(value.lower().split()) != current_key]
    return random.choice(available or [value for value in choices if " ".join(value.lower().split()) != current_key] or choices)

def _remembered_bio_copy_is_used(field: str, value: str, used_details: dict | None) -> bool:
    target = " ".join(str(value or "").lower().split())
    return bool(target and target in {" ".join(str(item).lower().split()) for item in (used_details or {}).get(field, [])})

def _to_roman(d: dict) -> dict:
    """Backup biodata ko Hinglish (Roman) mein badlo."""
    for k in ("education", "job", "city", "family", "marital_status", "children"):
        d[k] = ROMAN.get(d[k], d[k])
    d["height"] = d["height"].replace(" फुट ", " ft ").replace(" इंच", " in")
    d["expectations"] = next((roman for hindi, roman in ATTRACTIVE_LINES if d["expectations"] == hindi), d["expectations"])
    d["caption"] = f"{d['name_roman']}, {d['age']} saal, {d['city']}.\nBiodata ke liye DM karein."
    return d


def fallback_bio(o: dict, avoid: list, is_blocked, used_details: dict | None = None) -> dict:
    d = _fallback_bio(o, avoid, is_blocked, used_details)
    return _to_roman(d) if is_hinglish(o.get("lang", "")) else d


def _fallback_bio(o: dict, avoid: list, is_blocked, used_details: dict | None = None) -> dict:
    female = o["type"] in ("Gharjamai", "MaaAkeli") or o["gender"] == "Female"
    names = F_NAMES if female else M_NAMES
    cand = [n for n in names if not is_blocked(n.split("|")[1])]
    if o.get("letters"):
        cand = [n for n in cand if n.split("|")[1].lower().startswith(o["letters"].lower()[:1])] or cand
    hi, ro = random.choice(cand or names).split("|")
    if o.get("full_name"):
        sh, sr = random.choice(SURNAMES).split("|")
        hi, ro = f"{hi} {sh}", f"{ro} {sr}"
    re_ = o["type"] in ("Remarriage", "Divorcee", "Widow/Widower")
    age = random.randint(*BIO_AGE.get(o["type"], (25, 33)))
    ft, inch = (random.choice([4, 5]), random.randint(0, 11)) if female else (5, random.randint(3, 11))
    status = STATUS_HI[random.choice(o.get("statuses") or ["Divorced"])] if re_ else "अविवाहित"
    kids = "—"
    if re_:
        kids = {"Yes": "1 बच्चा", "No": "कोई बच्चा नहीं"}.get(o.get("children"), random.choice(["1 बच्चा", "कोई बच्चा नहीं"]))
    exp = fresh_bio_phrase("expectations", used_details, o.get("lang", "Hindi"), o["type"])
    family = fresh_bio_phrase("family", used_details, o.get("lang", "Hindi"), o["type"])
    return {"name_hindi": hi, "name_roman": ro, "age": age, "height": f"{ft} फुट {inch} इंच",
            "education": random.choice(EDUCATION), "job": random.choice(JOBS_F if female else JOBS_M),
            "city": CITIES.get(o["state"], o["state"]), "state": o["state"], "community": o["community"],
            "family": family, "marital_status": status, "children": kids, "expectations": exp,
            "caption": f"{hi}, {age} वर्ष, {CITIES.get(o['state'], o['state'])}।\nबायोडाटा के लिए DM करें।",
            "hashtags": ""}


def alternate_bio_value(field: str, current: str, opts: dict, details: dict, is_blocked) -> str | None:
    """Return a different valid value for a field-level refresh."""
    if field == "name":
        female = opts.get("gender") == "Female" or opts.get("type") in ("Gharjamai", "MaaAkeli")
        candidates = F_NAMES if female else M_NAMES
        initial = (opts.get("letters") or "").lower()[:1]
        candidates = [item for item in candidates if (not initial or item.split("|")[1].lower().startswith(initial))
                     and not is_blocked(item.split("|")[1])]
        random.shuffle(candidates)
        for item in candidates:
            hindi, roman = item.split("|")
            if roman.lower() != str(details.get("name_roman", "")).split()[0].lower():
                surname_hi, surname_ro = random.choice(SURNAMES).split("|") if opts.get("full_name") else ("", "")
                return f"{hindi} {surname_hi}".strip(), f"{roman} {surname_ro}".strip()
        return None
    if field == "age":
        low, high = BIO_AGE.get(opts.get("type"), (25, 33))
        choices = [str(value) for value in range(low, high + 1) if str(value) != str(current)]
    elif field == "height":
        female = opts.get("gender") == "Female" or opts.get("type") in ("Gharjamai", "MaaAkeli")
        choices = [f"{feet} फुट {inch} इंच" for feet in ([4, 5] if female else [5, 6]) for inch in range(12)
                   if f"{feet} फुट {inch} इंच" != str(current)]
    elif field == "education":
        choices = [value for value in EDUCATION if value != current]
    elif field == "job":
        female = opts.get("gender") == "Female" or opts.get("type") in ("Gharjamai", "MaaAkeli")
        choices = [value for value in (JOBS_F if female else JOBS_M) if value != current]
    elif field == "city":
        choices = [value for value in CITY_CHOICES.get(opts.get("state", ""), [details.get("city", "")]) if value != current]
        if is_hinglish(details.get("lang", "")):
            choices = [ROMAN.get(value, value) for value in choices]
    elif field == "status":
        allowed = opts.get("type") in ("Remarriage", "Divorcee", "Widow/Widower")
        choices = [STATUS_HI[value] for value in (opts.get("statuses") or ["Divorced", "Widow/Widower", "Separated"]) if value in STATUS_HI] if allowed else []
        choices = [value for value in choices if value != current]
    else:
        return None
    return random.choice(choices) if choices else None


def biodata(o: dict, avoid: list, brand: str, is_blocked, used_details: dict | None = None) -> dict:
    system = f"""Tum matrimony biodata ke liye kalpanik lekin bilkul asli lagne wali details banate ho.
Keys: name_hindi, name_roman, age (number), height, education, job, city, state, community, family, marital_status, children, expectations (positive personal highlight, not partner requirements), caption, hashtags.
Bhasha (name_hindi ko chhod kar sab values): {lang_rule(o.get("lang", "Hindi"))} name_roman aur hashtags hamesha Roman.
- education sirf in mein se: {', '.join(EDUCATION)}. Kabhi PhD/IIT/MBA/CA/videsh nahi.
- job aam: dukaan, private job, teacher, sarkari clerk, kheti, driver, beautician, silai, computer operator.
- height jaise "5 फुट 4 इंच". family 1 line. expectations 1-2 line. city us state ka asli shaher.
- Family aur personal highlight positive, natural aur alag hon; expectations mein partner ki demands/list nahi, apni ek achhi personal line dein.
- caption: 2-3 line, end mein "बायोडाटा के लिए DM करें". hashtags 8-12 Roman.
- {'Ek hashtag #' + re.sub(chr(92) + 'W', '', brand.lower()) + ' zaroor.' if brand else 'Koi brand naam nahi.'}
- "Demo" ya "Profile" kabhi nahi."""
    re_ = o["type"] in ("Remarriage", "Divorcee", "Widow/Widower")
    gender = "Female" if o["type"] in ("Gharjamai", "MaaAkeli") else o["gender"]
    lo, hi_ = BIO_AGE.get(o["type"], (25, 33))
    tguide = BIO_GUIDE.get(o["type"], "")
    extra = ("Ladki maa/ghar ki zimmedari sambhalti hai. marital_status: अविवाहित. children: \"—\". expectations: aisa ladka jo ghar jamai ban kar rahe." if o["type"] == "Gharjamai"
             else f"marital_status in mein se: {', '.join(o.get('statuses') or MARITAL_DEFAULT)}. Bachche: {o.get('children', 'Any')}." if re_
             else "marital_status: अविवाहित. children: \"—\".")
    user = (f"Type: {o['type']}. {tguide} Gender: {'ladka' if gender == 'Male' else 'ladki'}. Age: {lo}-{hi_}.\n"
            f"State: {o['state']}. Community: {o['community']}.\n"
            f"Naam: {'poora naam surname ke saath' if o.get('full_name') else 'sirf pehla naam'}."
            f"{(' Naam in letters se shuru: ' + o['letters']) if o.get('letters') else ''}\n{extra}\n"
            f"{('User instruction (zaroor maano): ' + o['instruction']) if o.get('instruction') else ''}\n"
            f"Ye naam bilkul mat use karo: {', '.join(avoid[:300]) or '(koi nahi)'}")
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
            d["expectations"] = fresh_bio_phrase("expectations", used_details, o.get("lang", "Hindi"),
                                                   o["type"], d.get("expectations", ""))
            if _remembered_bio_copy_is_used("family", d.get("family", ""), used_details):
                d["family"] = fresh_bio_phrase("family", used_details, o.get("lang", "Hindi"),
                                                  o["type"], d.get("family", ""))
            d["hashtags"] = _clean_tags(str(d.get("hashtags", TAGS)), brand)
            d["caption"] = _strip_brand(d["caption"], brand)
            return d
        except Exception as e:
            print("[textgen] bio retry:", e)
    d = fallback_bio(o, avoid, is_blocked, used_details)
    d["hashtags"] = _clean_tags(TAGS, brand)
    return d


MARITAL_DEFAULT = ["Divorced", "Widow/Widower", "Separated"]
BIO_GUIDE = {
    "Divorcee": "Divorce ho chuka hai; marital_status talaakshuda/Divorced.",
    "Widow/Widower": "Jeevansathi guzar gaye; marital_status vidhwa/vidhur.",
    "Bina Dahej": "expectations mein saaf likho: dahej nahi chahiye/dena.",
    "MaaAkeli": "Ladki maa ke saath akeli; ghar jamai ya maa ko saath rakhne wala ladka chahiye.",
    "Anath": "Parivaar nahi hai (anath); family field mein yahi izzat se likho.",
    "Late Marriage": "Umar 35+ par pehli shaadi; marital_status avivahit.",
    "Friendship": "Ye friendship profile hai; expectations mein dosti/baat-cheet, shaadi nahi.",
    "Dating": "Serious dating profile; expectations mein samajhdar partner.",
    "Govt Job": "job koi aam sarkari naukri (clerk, railway, police constable, teacher).",
    "Business": "job: apni dukaan/chhota business.",
}
