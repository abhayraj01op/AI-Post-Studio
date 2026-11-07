from app.config import CLASSES, DEFAULT_SUBJECT, SUBJECTS
from app.prompts import build_image_prompt, build_portrait_prompt, look
from app.render import fit_contain_blur
from PIL import Image


def test_bold_is_a_distinct_subtle_option():
    assert "Bold" in CLASSES
    assert "polished but realistic" in look("Bold")["tone"]
    assert any("jewel-tone" in outfit for outfit in look("Bold")["f"])


def test_single_female_subject_mentions_full_head_and_clear_eyes():
    prompt = build_image_prompt("Marriage", "Female", False, "", "Bold")
    assert "Indian woman" in prompt["scene"]
    assert "entire head" in prompt["scene"]
    assert "Both eyes open, naturally aligned" in prompt["scene"]
    assert "asymmetrical eyes" in prompt["neg"]


def test_biodata_portrait_emphasizes_face_framing_and_eyes():
    prompt = build_portrait_prompt("Female", 31, "Marathi", "Maharashtra", False)
    assert "full head and chin visible" in prompt["scene"]
    assert "Both eyes open, naturally aligned" in prompt["scene"]
    assert "head cropped" in prompt["neg"]


def test_face_safe_contain_keeps_portrait_pixels_inside_biodata_photo_area():
    portrait = Image.new("RGB", (800, 1200), (211, 73, 55))
    for y in range(22):
        for x in range(798):
            portrait.putpixel((x, y), (255, 255, 255))
    fitted = fit_contain_blur(portrait, 1080, 900)
    assert fitted.size == (1080, 900)
    assert fitted.getpixel((540, 11)) == (255, 255, 255)


def test_default_post_photo_choice_is_female():
    assert DEFAULT_SUBJECT == "Female"
    assert SUBJECTS[DEFAULT_SUBJECT] == "Sirf ladki (Female)"