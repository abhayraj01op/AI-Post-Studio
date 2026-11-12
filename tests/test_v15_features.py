import sys
import types

try:
    import gradio  # noqa: F401
except ImportError:
    gradio_stub = types.ModuleType("gradio")
    gradio_stub.SelectData = type("SelectData", (), {})
    sys.modules["gradio"] = gradio_stub

from PIL import Image

from app import config, main, textgen, tools
from app.prompts import build_image_prompt, build_portrait_prompt


def test_every_fallback_post_invites_a_dm_or_comment_in_both_languages():
    for lang in ("Hindi", "Hinglish (Roman, aasan)"):
        post = textgen.fallback_post("Normal", [], "", lang)
        assert textgen.normalize_post_cta(post["cta"], lang) == post["cta"]
        assert any(token in post["cta"].lower() for token in ("dm", "comment", "कमेंट", "टिप्पणी"))
        if lang.startswith("Hinglish"):
            assert not any("\u0900" <= char <= "\u097f" for char in post["cta"])
        else:
            assert any("\u0900" <= char <= "\u097f" for char in post["cta"])


def test_all_post_types_keep_headline_in_the_selected_language():
    for post_type in config.POST_TYPES:
        hindi = textgen.fallback_post(post_type, [], "", "Hindi")
        hinglish = textgen.fallback_post(post_type, [], "", "Hinglish (Roman, aasan)")
        assert any("\u0900" <= char <= "\u097f" for char in hindi["headline"])
        assert not any("\u0900" <= char <= "\u097f" for char in hinglish["headline"])


def test_manual_cta_without_dm_or_comment_is_replaced_with_action_cta():
    for lang in ("Hindi", "Hinglish (Roman, aasan)"):
        cta = textgen.normalize_post_cta("Aaj hi sampark karein", lang)
        assert any(token in cta.lower() for token in ("dm", "comment", "कमेंट", "टिप्पणी"))
        if lang.startswith("Hinglish"):
            assert not any("\u0900" <= char <= "\u097f" for char in cta)
        else:
            assert any("\u0900" <= char <= "\u097f" for char in cta)


def test_saving_a_post_enforces_a_dm_or_comment_cta(tmp_path, monkeypatch):
    db = {
        "images": [{"id": "img-1", "path": str(tmp_path / "source.png")}],
        "posts": {},
        "settings": {"lang": "Hinglish (Roman, aasan)", "brand_on": False, "footer": "", "format": "png"},
    }
    Image.new("RGB", (8, 8), "white").save(db["images"][0]["path"])
    monkeypatch.setattr(main.storage, "load", lambda: db)
    monkeypatch.setattr(main.storage, "update", lambda change: change(db))
    monkeypatch.setattr(main.storage, "push_headline", lambda _headline: None)
    monkeypatch.setattr(main, "POSTS_DIR", tmp_path)
    monkeypatch.setattr(main, "render_post", lambda *args: Image.new("RGB", (8, 8), "white"))

    message, _gallery = main.edit_post("img-1", "Sahi rishta", "Aaj hi sampark karein", "Caption", "#rishta")

    assert "Image par add ho gaya" in message
    assert any(token in db["posts"]["img-1"]["cta"].lower() for token in ("dm", "comment"))


def test_photo_prompts_request_better_clothing_background_and_anatomy():
    prompts = [
        build_image_prompt("Marriage", "Female", False, ""),
        build_portrait_prompt("Female", 31, "All", "All", False),
        build_portrait_prompt("Female", 31, "All", "All", False, full=True),
    ]
    for prompt in prompts:
        scene = prompt["scene"].lower()
        negative = prompt["neg"].lower()
        assert "fabric weave" in scene or "fabric texture" in scene
        assert "coherent" in scene or "clear" in scene
        assert "natural" in scene and ("anatomy" in scene or "body proportions" in scene)
        assert "distorted smile" in negative
        assert "malformed fingers" in negative


def test_optional_social_accounts_are_saved_and_added_to_extra_tool_exports(tmp_path, monkeypatch):
    source = tmp_path / "source.png"
    Image.new("RGB", (16, 16), "white").save(source)
    monkeypatch.setattr(tools, "DATA", tmp_path)
    monkeypatch.setattr(tools, "EXPORT_DIR", tmp_path / "exports")
    monkeypatch.setattr(tools, "_sources", lambda _ids, _all: [("item-1", str(source))])
    saved = {"settings": {}}

    def update(mutator):
        mutator(saved)

    monkeypatch.setattr(tools.storage, "update", update)
    original_watermark = tools.watermark
    captured = {}

    def capture_watermark(img, number, logo, pos, opacity, social_contacts=None):
        captured.update(social_contacts or {})
        return original_watermark(img, number, logo, pos, opacity, social_contacts)

    monkeypatch.setattr(tools, "watermark", capture_watermark)

    _message, archive, _preview = tools.export_all(
        ["item-1"], False, ["Instagram post (1080x1080)"], "", None, "Neeche right", 80, True,
        "@connect", "https://facebook.com/groups/rishta", "https://facebook.com/page", "@connectmate",
    )

    assert archive and __import__("pathlib").Path(archive).exists()
    assert captured == {
        "Telegram": "@connect",
        "Facebook Group": "https://facebook.com/groups/rishta",
        "Facebook Page": "https://facebook.com/page",
        "Instagram": "@connectmate",
    }
    assert saved["settings"] == {
        "extra_telegram": "@connect",
        "extra_facebook_group": "https://facebook.com/groups/rishta",
        "extra_facebook_page": "https://facebook.com/page",
        "extra_instagram_page": "@connectmate",
    }