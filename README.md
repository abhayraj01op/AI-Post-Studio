# Connect Mate Services — AI Post Studio v13 (Google Colab)

This is an update of the supplied v10 ZIP. It is designed for one-click batches of social posts and fictional sample biodata, using free/open-source software and a free Colab GPU when available.

## One-click workflow

- **Posts tab:** click `10 naye ready posts banao (photo + Hindi text)`. It creates 10 fresh AI portraits and their finished post artwork sequentially. No prompt or text entry is required. Defaults are Marriage, Female portrait, 1080×1350 and Connect Mate Services branding.
- **Biodata tab:** click `10 biodata — ek click, bina likhe`. It creates 10 fictional sample profiles with fresh AI portraits sequentially. Defaults are Marriage, Female, all states, all communities, half portrait and Connect Mate Services branding. The count selector for the regular biodata button also defaults to 10.
- The category, subject, size, profile type and other filters can still be changed, but they are optional.
- The Biodata generate button follows the selected count (1 / 5 / 10 / 20); the separate quick action still makes 10.
- Gallery previews use contain-fit so full portrait and story artwork are not shown as cropped thumbnails.
- The Biodata generate button follows the selected count (1 / 5 / 10 / 20); the separate quick action still makes 10.
- Gallery previews use contain-fit so full portrait and story artwork are not shown as cropped thumbnails.

## Fictional profile and disclosure rules

- The generator creates synthetic fictional names/details only. It does not read or publish real member biodata or personal information.
- The image artwork does **not** print `Demo`, `Fake`, `AI Generated` or similar labels.
- The social caption (outside the image) automatically includes: `यह एक डेमो डेटा पर आधारित उदाहरण है। वास्तविक रिश्तों के लिए कमेंट करें।` Keep this disclosure when publishing generated sample profiles.
- Do not present fictional profile details as an actual registered/available member. Use genuine member data only in a separate, consent-based workflow; this ZIP intentionally does not include that workflow.

## Improvements in v13

- Matched the Biodata generate-button label to the selected 1 / 5 / 10 / 20 profiles.
- Kept complete generated artwork visible in gallery previews with contain-fit display.
- Strengthened prompts for authentic Indian people, including everyday matrimonial portraits and non-model styling.
- Added a clear enhancement-tool choice: AI (ComfyUI) or Basic (Pillow).
- AI enhancement uses 4x-UltraSharp upscaling and low-denoise SDXL refinement; face/hand detailers run only when their ComfyUI nodes and models are installed.
- Removed the silent AI-to-Pillow fallback. If ComfyUI enhancement fails, the error is shown and the unprocessed file is not overwritten; Basic processing is available only when explicitly selected.

## Improvements in v11

- Added one-click 10-post generation in the Posts tab: new AI portrait + headline + CTA + caption + hashtags.
- Added one-click 10-biodata generation with no prompt entry.
- Added caption disclosure for fictional sample posts; disclosure is never drawn onto the image.
- Added complete biodata editing: Hindi/Roman name, age, height, community, education, job, city, state, marital status, children, family and expectations.
- Fixed selected-photo biodata loading by importing the render helper module correctly.
- Improved text layout: headlines/CTA shrink and wrap; biodata canvas expands to fit details instead of silently clipping normal text.
- Added one transient retry with memory cleanup and persistent error log at `data/error_logs.txt`.
- Kept sequential generation to reduce T4 GPU memory pressure.
- Model checkpoints, generated assets, DB, settings and exports remain under Google Drive `MyDrive/AI_Post_Studio/models` and `MyDrive/AI_Post_Studio/data`.

## Run in Google Colab

1. Upload this ZIP to GitHub or Google Drive and open `AI_Post_Studio_Colab.ipynb` in Google Colab.
2. Select **Runtime → Change runtime type → T4 GPU** if available.
3. Run cells from top to bottom and approve Google Drive access.
4. First setup downloads ComfyUI, SDXL checkpoint and optional helper models. It can take a while and needs temporary Colab disk space plus an internet connection during setup.
5. Keep the final **Start / Restart** cell running until it prints the current Gradio link.
6. After the app opens, use the Posts or Biodata tab's one-click button.

## Storage and free-GPU limitations

- Persistent user data and reusable model files are stored in Google Drive. ComfyUI code, temporary output and runtime cache use Colab's temporary disk where appropriate.
- 5 TB Drive storage provides room for assets/models/backups; it does **not** increase GPU VRAM, GPU speed, RAM or Colab session duration.
- Free Colab GPU availability and session limits vary. T4 is not guaranteed on every session. Batch generation is sequential and may pause/fail if Colab disconnects or the GPU is unavailable.
- Approximate T4 planning ranges: 45–120 seconds per SDXL portrait after models are loaded; a rendered post from an existing image is usually a few seconds; a biodata card from an existing photo is usually several seconds to tens of seconds. Model loading and Drive I/O add time. Ten fresh AI posts or ten fresh-photo biodata cards can take roughly 10–35+ minutes depending on the session and quality settings. These are estimates, not guarantees.

## Technical notes

- SDXL / RealVisXL is used for photorealistic portraits. Hindi text is drawn with Pillow and Mukta fonts, not by the image model.
- No paid API is required. The initial setup does need internet to download public open-source model/code assets. After setup, generation is local to the Colab runtime.
- The notebook embeds the app files, tests and Hindi fonts; a GitHub checkout is not required for the notebook to run.
- Gradio compatibility: CSS and HEAD are now passed to `gr.Blocks(...)` (where Gradio 5.x expects them), not to `Blocks.launch(...)`. This fixes the `TypeError: Blocks.launch() got an unexpected keyword argument 'css'` startup crash.
- Tests: run `PYTHONPATH=. pytest -q` from the extracted project. This is not a live Colab T4 runtime test; actual GPU output must still be checked in Colab.
