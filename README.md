# AI Post Studio — Google Colab (Updated)

This package restores the archived Colab application and includes the previously requested tools: AI-generated photos, editable Hindi/Hinglish posts and biodata, AI enhancement, export sizes, watermark, weekly posting plan, and a lead tracker.

## Included image improvements

- Indian women are preselected for solo images and biodata; couples and men remain available.
- Biodata prompts explicitly ask for the complete head, hairline, chin, and open, aligned eyes in focus.
- The biodata card frames portraits from the top so the face is not cropped by the wide card.
- A restrained **Bold** option adds polished, richer outfits while keeping clothing modest and realistic.
- Image generation uses a more detailed first render and a higher-detail upscale pass. Realistic results still depend on the model, prompt, and available T4 GPU; no image model can guarantee perfect facial features.
- Gradio and its client are pinned to a compatible set that avoids the earlier Gradio schema-conversion crash.

## First-time setup

1. Open `AI_Post_Studio_Colab.ipynb` in Google Colab (upload it from this ZIP, or place the notebook itself in Drive).
2. Choose **Runtime → Change runtime type → T4 GPU**.
3. Run the cells from top to bottom. The notebook includes the app code and Hindi fonts, so no GitHub upload is needed. Approve the Google Drive prompt. The first setup downloads ComfyUI and a large photo model; allow several minutes and several GB of free Colab storage.
4. Open the `gradio.live` link printed by the final cell.

Your images, posts, biodata, and settings are saved in `MyDrive/AI_Post_Studio`.

## Later sessions

Reopen the notebook in Colab and run the cells from top to bottom. If Colab retains an old broken runtime, choose **Runtime → Disconnect and delete runtime**, then run all cells again.

## Notes

- Photo generation and AI enhancement run locally in Colab; they do not use Lovable credits. Text generation uses a small local language model, with built-in templates as a fallback.
- Free Colab sessions and GPU availability are limited by Google. A disconnected runtime stops generation; saved work remains on Drive.
- This updated package was rebuilt from the app files recovered from the repository's archived `cafa3336` snapshot. The former v10 ZIP was not present in Files, and the current GitHub `main` branch is empty, so an exact byte-for-byte v10 match could not be confirmed.
- The package's Python syntax, prompt rules, and local portrait framing have been checked here. The notebook has not been launched on a Google Colab T4 in this environment.