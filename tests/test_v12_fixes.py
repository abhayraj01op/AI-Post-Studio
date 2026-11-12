import sys
import types

import pytest
from PIL import Image

# The app UI is only needed for its label helper; Colab provides the real Gradio package.
try:
    import gradio  # noqa: F401
except ImportError:
    gradio_stub = types.ModuleType("gradio")
    gradio_stub.SelectData = type("SelectData", (), {})
    sys.modules["gradio"] = gradio_stub

from app import config, main
from app.main import biodata_button_label
from app import comfy, enhance
from app.prompts import build_image_prompt, build_portrait_prompt


@pytest.mark.parametrize(("count", "expected"), [(1, "1 biodata banao"), (5, "5 biodata banao"),
                                                    (10, "10 biodata banao"), (20, "20 biodata banao")])
def test_biodata_generate_button_matches_selected_count(count, expected):
    assert biodata_button_label(count) == expected


def test_ai_enhancement_error_is_not_silently_replaced_with_pillow(monkeypatch):
    def unavailable(*args, **kwargs):
        raise RuntimeError("ComfyUI chal nahi raha")

    monkeypatch.setattr(comfy, "enhance", unavailable)
    monkeypatch.setattr(enhance, "enhance_image", lambda *args, **kwargs: pytest.fail("Pillow fallback must not run"))

    with pytest.raises(RuntimeError, match="ComfyUI chal nahi raha"):
        enhance.smart_enhance(Image.new("RGB", (8, 8)), method=enhance.AI_METHOD)


def test_pillow_processing_runs_only_when_basic_is_selected(monkeypatch):
    expected = Image.new("RGB", (4, 4), "red")
    seen = []

    def basic(img, level, out_size):
        seen.append((level, out_size))
        return expected

    monkeypatch.setattr(enhance, "enhance_image", basic)
    result, label = enhance.smart_enhance(Image.new("RGB", (8, 8)), "Light", (4, 4), enhance.BASIC_METHOD)

    assert result is expected
    assert "no generative AI" in label
    assert seen == [("Light", (4, 4))]


def test_female_image_and_biodata_prompts_request_authentic_indian_portraits():
    image_prompt = build_image_prompt("Marriage", "Female", False, "")
    bio_prompt = build_portrait_prompt("Female", 31, "All", "All", False)

    assert "ordinary Indian woman" in image_prompt["scene"]
    assert "authentic Indian facial features" in image_prompt["scene"]
    assert "ordinary Indian woman" in bio_prompt["scene"]
    assert "authentic Indian facial features" in bio_prompt["scene"]


def test_ai_enhancement_error_keeps_original_image_and_shows_reason(tmp_path, monkeypatch):
    original = tmp_path / "original.png"
    Image.new("RGB", (8, 8), "red").save(original)
    before = original.read_bytes()
    db = {"images": [{"id": "image-1", "path": str(original), "w": 8, "h": 8}],
          "posts": {}, "biodata": [], "settings": {}}
    db["images"][0].update(category="Marriage", subject="Female")
    monkeypatch.setattr(config, "DATA", tmp_path)
    monkeypatch.setattr(main.storage, "load", lambda: db)
    monkeypatch.setattr(main.enhance, "smart_enhance",
                        lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("ComfyUI is unavailable")))

    message, _gallery = main.enhance_images(["image-1"], "Normal", False)

    assert "ComfyUI is unavailable" in message
    assert "0/1 complete" in message
    assert original.read_bytes() == before
