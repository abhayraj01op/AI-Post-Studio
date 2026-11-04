# AI Post Studio (Colab) (v8)

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/abhayraj01op/AI-Post-Studio/blob/main/AI_Post_Studio_Colab.ipynb)

**Direct Colab link:** https://colab.research.google.com/github/abhayraj01op/AI-Post-Studio/blob/main/AI_Post_Studio_Colab.ipynb

## Kaise chalayein
1. Is zip ki saari files GitHub repo `abhayraj01op/AI-Post-Studio` ke **main** branch ke root mein upload karein (folder ke andar nahi). Repo **Public** rakhein.
2. Upar wala link kholein → Runtime → Change runtime type → **T4 GPU**.
3. Cells upar se neeche ek-ek karke chalayein. Repo link pehle se bhara hai.

## v3 — Photo quality fix
- Bindi/sindoor/mangalsutra ab kisi photo mein nahi aayega (ye sab "negative" list mein hai; pehle "no sindoor" likhne se ulta sindoor aa jata tha).
- Har photo 3 step mein banti hai: normal → 1.5x HD re-render → FaceDetailer se chehra theek. Chehra/ungliyan kam bigadti hain.
- Har baar naya chehra: naam, state, chehre ka shape, skin, aankh, naak, baal, body sab random.
- Sirf aise pose jahan haath aaram se hon (ungliyan kam kharab).
- Settings cell mein 2 free photo model: RealVisXL V5 ya Juggernaut XL v9.
- Ek photo ab ~60–120 sec (T4 par) leti hai, kyunki quality zyada hai.

## v5 badlav
- Same face problem fix: har photo mein do random chehre mila kar naya chehra; face fix bhi usi chehre ko rakhta hai.
- Photo quality: 4x-UltraSharp upscaler + T4-safe VAE + random sampler/CFG.
- RAM/Disk: text model 4-bit (kam GPU), ek hi photo model Drive par, ComfyUI ki extra copies turant delete.

## Enhance (naya)
Tab 4 mein images, posts aur biodata ko ek click mein saaf/sharp karein. Post ka text aur biodata ki details bhi behtar ban sakti hain.

## v8 badlav
- Setup ka Impact-Pack `git pull` error fix: woh folder ab Drive par nahi, har baar fresh aata hai; fail ho to bhi setup nahi rukta.
- Umar: Marriage/Friendship/Dating 25+, Remarriage/Gharjamai 35+.
- Look option: Normal / Middle class / High class / Mix — kapde, jagah, background badalte hain. Photos zyada attractive aur real.
- Full photo ab sach mein sir se pair tak (lambi photo banti hai, kaati nahi jaati). Haath-fix step bhi joda.
- Har tab mein ⏹ Roko / Cancel button.
- Enhance ab AI wala: 4x upscaler + re-render + chehra fix + haath fix.
- Post: headline / CTA / caption / hashtags har ek alag se ↻ naya, copy button, phir "Image par add karo". 13 naye post types.
- Brand naam sirf tab aata hai jab tick ON ho aur naam likha ho (pehle default "Apna Connection" khud lag jata tha).
- Biodata: 13 types, Half/Full/Mix photo, Hinglish ya aasan Hindi.
