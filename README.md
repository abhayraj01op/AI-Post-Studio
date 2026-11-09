# AI Post Studio — updated from your v10 ZIP

This package starts from the v10 ZIP you uploaded and keeps its existing image, post, biodata, editing, enhancement, and lead-management features. It adds the requested portrait, quality, and interface updates.

## What changed

- Solo images now start with **Sirf ladki (Female)** in every category. Couple and male selections remain available.
- Biodata defaults to a female portrait and half-photo framing; male remains a manual selection.
- Marriage profiles use ages 28–34; remarriage profiles use ages 35–46.
- **Bold** is a new optional look with modest, polished jewel-tone outfits. **Mix** remains the default.
- Portrait instructions ask for the complete head, hairline, chin, and two open, aligned eyes. The negative prompt excludes closed, missing, or uneven eyes and cropped faces.
- Biodata headshots use a top-anchored crop, while full-body photos stay contained in frame on a clean solid background. Full-photo choices use a more permissive uncropped fit.
- Portrait prompts emphasize selected region/community context, Indian matrimonial clothing, crisp fabric detail, clear backgrounds, and plausible hands when visible.
- The image render uses 34 first-pass steps and a 24-step detail pass; face refinement remains available when its optional detector installs.
- The Gradio screen has clearer tab focus, spacing, buttons, gallery edges, and small-screen tab handling.
- The notebook includes the app files and Hindi fonts. You do not need to upload app folders to GitHub.

## Run in Google Colab

1. Extract this ZIP and upload `AI_Post_Studio_Colab.ipynb` to Colab, or place it in Google Drive and open it from there.
2. Select **Runtime → Change runtime type → T4 GPU**.
3. Run the notebook cells from top to bottom and approve Google Drive access.
4. The first setup downloads ComfyUI, one photo model, and helper files. Keep several GB free in Colab temporary storage and allow extra time for the downloads.
5. Open the `gradio.live` link printed by the final cell.

If the interface stops or the old share link reports that no interface is running, reconnect Colab, rerun Setup only if needed, then run **Start / Restart** to open the fresh link. The app runs separately from the notebook cell, so long image-model loading does not require leaving that cell running.

Images, posts, biodata, settings, and the selected photo model are saved in `MyDrive/AI_Post_Studio`. ComfyUI itself runs on the temporary Colab disk. Incomplete photo model downloads resume when Setup is rerun; the setup validates the model before starting the app.

## Accuracy notes

The app code compiles locally and all 15 automated tests pass, including portrait framing, age ranges, region/community context, clothing prompts, and full-photo card rendering. The notebook was not run on a live Colab T4 here. Image prompts and optional face/hand detailers can improve results but cannot guarantee anatomically perfect eyes, clothing, or fingers.

This archive is updated from the exact v10 ZIP you supplied. Its original application features were retained; the `src/pages` and `src/lib/utils.ts` TypeScript errors reported in chat belong to a different project, not this Colab source.