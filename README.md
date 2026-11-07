# AI Post Studio (Colab) (v6)

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

## v6 badlav
- Same face problem fix: har photo mein do random chehre mila kar naya chehra; face fix bhi usi chehre ko rakhta hai.
- Photo quality: 4x-UltraSharp upscaler + T4-safe VAE + random sampler/CFG.
- RAM/Disk: text model 4-bit (kam GPU), ek hi photo model Drive par, ComfyUI ki extra copies turant delete.
