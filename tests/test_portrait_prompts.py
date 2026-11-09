from PIL import Image

from app.config import AGE_RANGE, BIO_AGE, CATEGORIES, CLASSES, DEFAULT_SUBJECT, SUBJECTS
from app.prompts import build_image_prompt, build_portrait_prompt, look
from app import render
from app.render import fit_cover, fit_contain_blur


def test_bold_is_a_distinct_subtle_option():
    assert "Bold" in CLASSES
    assert "polished but realistic" in look("Bold")["tone"]
    assert any("jewel-tone" in outfit for outfit in look("Bold")["f"])


def test_every_category_female_prompt_keeps_head_and_eyes_in_frame():
    for category in CATEGORIES:
        prompt = build_image_prompt(category, DEFAULT_SUBJECT, False, "", "Bold")
        assert "Indian woman" in prompt["scene"]
        assert "entire head" in prompt["scene"]
        assert "Both eyes open, naturally aligned" in prompt["scene"]
        assert "asymmetrical eyes" in prompt["neg"]


def test_biodata_portrait_emphasizes_face_framing_and_eyes():
    prompt = build_portrait_prompt("Female", 31, "Marathi", "Maharashtra", False)
    assert "full head and chin visible" in prompt["scene"]
    assert "Both eyes open" in prompt["scene"]
    assert "head cropped" in prompt["neg"]


def test_biodata_photo_uses_top_anchored_portrait_crop():
    portrait = Image.new("RGB", (800, 1200), (211, 73, 55))
    for y in range(22):
        for x in range(798):
            portrait.putpixel((x, y), (255, 255, 255))
    fitted = fit_cover(portrait, 1080, 900, 0.02)
    assert fitted.size == (1080, 900)
    assert fitted.getpixel((540, 11)) == (255, 255, 255)


def test_biodata_renderer_keeps_the_top_of_a_half_portrait(monkeypatch):
    monkeypatch.setattr(render, "FONTS_DIR", __import__("pathlib").Path(__file__).parents[1] / "fonts")
    portrait = Image.new("RGB", (896, 1120), (211, 73, 55))
    for y in range(22):
        for x in range(894):
            portrait.putpixel((x, y), (255, 255, 255))
    details = {
        "lang": "Hinglish (Roman, aasan)", "photo_type": "Half photo",
        "name_roman": "Reena", "name_hindi": "रीना", "age": 31, "height": "5 ft 6 in",
        "community": "Maratha", "education": "Graduate", "job": "Teacher",
        "city": "Pune", "state": "Maharashtra", "marital_status": "Unmarried",
        "family": "Maa-papa aur ek bhai", "expectations": "Simple aur understanding partner chahiye.",
    }
    card = render.render_biodata(portrait, details, False, "")
    assert card.size == (1080, 1720)
    assert card.getpixel((540, 10)) == (255, 255, 255)


def test_full_portrait_contain_keeps_image_dimensions():
    fitted = fit_contain_blur(Image.new("RGB", (800, 1200)), 1080, 900)
    assert fitted.size == (1080, 900)


def test_default_image_subject_is_female():
    assert DEFAULT_SUBJECT == "Female"
    assert SUBJECTS[DEFAULT_SUBJECT] == "Sirf ladki (Female)"

def test_biodata_prompt_uses_selected_region_and_community_without_blur():
    prompt = build_portrait_prompt("Female", 37, "Maratha", "Maharashtra", True, False)
    assert "from Maharashtra" in prompt["scene"]
    assert "selected biodata community is Maratha" in prompt["scene"]
    assert "blurred" not in prompt["scene"].lower()
    assert "crisp" in prompt["scene"]
    assert "motion blur" in prompt["neg"]


def test_full_biodata_prompt_requests_full_body_and_natural_hands():
    prompt = build_portrait_prompt("Female", 40, "All", "All", True, True)
    assert "ENTIRE body visible" in prompt["scene"]
    assert "both hands visible" in prompt["scene"]
    assert "five distinct natural fingers" in prompt["scene"]
    assert "half body" in prompt["neg"]


def test_full_photo_fit_preserves_subject_without_blur_background():
    source = Image.new("RGB", (400, 800), (211, 73, 55))
    fitted = fit_contain_blur(source, 800, 800)
    assert fitted.size == (800, 800)
    assert fitted.getpixel((20, 400)) == render.CREAM
    assert fitted.getpixel((400, 400)) == (211, 73, 55)


def test_portrait_clothing_is_indian_styled_across_looks():
    for style in ("Normal", "Middle class", "High class", "Bold"):
        prompt = build_portrait_prompt("Female", 37, "All", "Maharashtra", True, False, style)
        assert "Indian matrimonial profile photo" in prompt["scene"]
        garment = prompt["scene"].split("wearing ", 1)[1].split(", from", 1)[0].lower()
        assert any(item in garment for item in ("saree", "kurta", "salwar"))


def test_marriage_and_remarriage_age_ranges_match_user_requirements():
    assert AGE_RANGE["Marriage"] == (28, 34)
    assert AGE_RANGE["Remarriage"] == (35, 46)
    assert BIO_AGE["Marriage"] == (28, 34)
    assert BIO_AGE["Remarriage"] == (35, 46)
    assert BIO_AGE["Widow/Widower"] == (35, 46)


def test_full_photo_fit_does_not_crop_nearby_portrait_shapes():
    source = Image.new("RGB", (832, 1216), (211, 73, 55))
    fitted = render.fit_photo(source, 1080, 1200, True)
    assert fitted.size == (1080, 1200)
    assert fitted.getpixel((0, 600)) == render.CREAM
