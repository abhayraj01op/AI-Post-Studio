# AI Post Studio — Poori Project Spec (Master Prompt)

Is prompt ko kisi bhi AI builder ko dekar same project dobara banwaya ja sakta hai.

---

## 1. Business
- Matrimony / match-making business. Default brand naam **"Apna Connection"**; user brand naam badal sakta hai.
- **Brand toggle OFF** = image, caption ya hashtags kahin bhi brand naam nahi (#apnaconnection bhi nahi).
- **Brand toggle ON** = image par brand naam + ek hashtag brand ka (bina space, jaise #apnaconnection).

## 2. Bhasha
- App ka saara UI text **Hinglish (Roman script)** mein.
- Image par likhi lines **Devanagari** mein, **aasan Hindi/Hinglish** (common English shabd jaise जॉब, फैमिली, सिंपल, अंडरस्टैंडिंग theek hain). **Shuddh Hindi nahi.**
- Hashtags **hamesha Roman** mein.

## 3. Sabse zaroori rules
1. Photo banane wala AI **kabhi text nahi likhta**. Saara Hindi text code se photo par draw hota hai (sahi spelling ke liye).
2. Photos **asli lagni chahiye**: Indian log, DSLR jaisi, aam rishta-photo style, models jaise nahi, cartoon/3D nahi.
3. Har photo mein **pose, angle, jagah, roshni, chehra alag** (shuffle deck, sab use hone tak repeat nahi).
4. **Kunwari ladkiyan:** sindoor, mangalsutra, bridal jewellery nahi.
5. **Umar:** Marriage 28+ (28–34), Remarriage 35+ (35–46).
6. Saare AI kaam **ek-ek karke**, kabhi ek saath nahi. Bada error (server band / credit / rate limit) aaye to batch ruk jaaye aur **asli wajah laal rang mein** dikhe.
7. Data kabhi khona nahi chahiye (web version: browser IndexedDB; Colab version: Google Drive `db.json` + files).
8. **"Demo Profile"** ya "Demo"/"Profile" kabhi nahi likhna.

## 4. Page 1 — Images banao
- **Category:** Marriage, Friendship, Dating, Remarriage, Gharjamai.
- **Kiski photo:** Couple, Sirf ladki, Sirf ladka, Ladki + uski mammi, Ladka + buzurg mammi.
- **Kitni images:** 1 / 10 / 20 / 30.
- **Half photo** (kamar se upar) ya **Full photo** (sar se pair tak).
- **Size:** 1080x1080 Square, 1080x1350 Portrait, 1080x1920 Story (bani photo is size par crop/fit).
- **Apni baat** (optional, 300 akshar) — prompt mein jud jaati hai.
- Composition: chehre beech mein; upar ~22% aur neeche ~22% saaf background (headline/CTA chehre par na aaye).
- **Apni photo upload** (multiple) — chuni size par fit.
- Gallery: har photo par label (category • subject / Upload), delete button.
- Progress: "Ban rahi hain X/Y • N fail".
- Colab version mein extra: **"Images + Posts ek saath banao"** — ek click mein N photo aur unke post.

## 5. Page 2 — Posts banao
- **Post type:**
  - Normal — simple, garam, bharosemand rishta post.
  - Couple — romantic, seedha viewer se baat ("tum"/"aap").
  - MaaAkeli — ladki maa ke saath akeli, ghar jamai chahiye jo maa ka bhi saath de.
  - BinaPapa — maa bol rahi, papa nahi rahe, dahej ki koi maang nahi.
  - Anath — orphan ladka/ladki, izzat aur sahara dene wala saathi.
- **Apni baat** (optional instruction, AI zaroor maane).
- AI har image ke liye likhe: **headline** (Devanagari, 3–6 shabd, image se juda lekin abstract, **kabhi repeat nahi** — pichhli 200 headlines yaad), **CTA** (2–5 shabd), **caption** (2–3 line), **hashtags** (8–12, Roman).
- **Koi supporting line nahi** — sirf headline + CTA image par.
- Design: upar maroon gradient band mein brand naam (marigold) + safed headline (shadow); neeche marigold pill mein CTA; uske neeche footer (jaise WhatsApp number) — sirf brand ON par.
- Har post edit ho sake (headline/CTA/caption/hashtags) → "Image par add karo".
- Download PNG/JPG; saare posts ZIP.

## 6. Page 3 — Biodata banao
- **Type:** Marriage, Remarriage, Ghar Jamai (sirf ladki; ladka chahiye jo ghar jamai bane aur ghar + maa sambhale).
- Remarriage: **Status** (Divorced, Widow/Widower, Separated — multi), **Bachche** (Any/Yes/No).
- **Gender** (Female/Male), **State** (All = aabaadi ke hisaab se zyada UP/Bihar/Maharashtra…), **Community** (All ya list: Hindu, Muslim, Sikh, Jain, Christian, Brahmin, Rajput, Yadav, Jat, Kurmi, Baniya/Agarwal, Kayastha, Gupta, Maratha, Gujjar, Kushwaha, Teli, Lodhi, SC/ST, Buddhist).
- **Poora naam** (surname ke saath) ya sirf pehla naam; **naam in letters se shuru** (optional); **apni baat**; **kitne biodata**.
- Details: naam (Hindi + Roman), umar, height ("5 फुट 4 इंच"), **padhai sirf** 10वीं / 12वीं / बी.ए. / बी.कॉम / आई.टी.आई. / डिप्लोमा / ग्रेजुएट (kabhi PhD/IIT/MBA/CA/videsh nahi), aam naukri (dukaan, private job, teacher, clerk, kheti, driver, beautician, silai, computer operator), us state ka asli shehar, community, family (1 line), marital status, bachche, expectations (1–2 line), caption (end: "बायोडाटा के लिए DM करें"), hashtags.
- **Naam 4 din tak repeat nahi** (pehla naam ya poora naam; time ke saath save).
- Portrait photo AI se (chest-up, alag background), card canvas par: upar photo, maroon + marigold patti, neeche Hindi details, "पार्टनर कैसा चाहिए" box. Brand ON par photo ke kone mein brand naam.
- Har card: naam/umar edit, **Regenerate** (same instruction/options), download, delete; saare ZIP.

## 7. Design
- Garam rang: **maroon (#7a1f1a) + marigold (#f2a516)**, cream background (#fbf4e6), ink (#2b1a14).
- Fonts: **Fraunces** (headings) + **Mukta** (Hindi/body). Purple nahi, Inter nahi.

## 8. Tech (Colab edition)
- Google Colab (T4 GPU), Google Drive mount, sab tools + data Drive par (`MyDrive/AI_Post_Studio`).
- **ComfyUI** (API mode) + **RealVisXL V5** SDXL checkpoint — photorealistic; negative prompt mein text/watermark/cartoon/extra fingers.
- Hindi text: **Qwen2.5-7B-Instruct** (4-bit) local; JSON output; galat/kharab jawab par built-in Hindi template bank.
- Text drawing: Pillow + libraqm (sahi Devanagari matra/shaping), Mukta fonts.
- App UI: Gradio, `share=True` link; queue ek-ek kaam.
- One-click notebook: Drive mount → setup (ComfyUI, model, fonts, packages) → name test → start.

## 9. Test
- Naam jo 3 din pehle use hua → block. 5 din pehle → allowed.
