from pathlib import Path
from PIL import Image

from app import render
from app.main import add_public_demo_note


def test_caption_gets_public_demo_disclosure_only_in_caption():
    caption = add_public_demo_note("Achhe jeevansathi ki talaash.")
    assert "डेमो डेटा" in caption
    assert "वास्तविक रिश्तों के लिए कमेंट करें" in caption
    assert add_public_demo_note(caption) == caption


def test_long_biodata_expands_canvas_instead_of_clipping(monkeypatch):
    monkeypatch.setattr(render, "FONTS_DIR", Path(__file__).parents[1] / "fonts")
    photo = Image.new("RGB", (896, 1120), (200, 150, 100))
    details = {
        "lang": "Hindi (aasan, Devanagari)", "photo_type": "Half photo",
        "name_roman": "Sample Person", "name_hindi": "कविता शर्मा", "age": 32,
        "height": "5 फुट 4 इंच", "community": "Hindu", "education": "बी.ए.",
        "job": "प्राइवेट जॉब", "city": "भोपाल", "state": "Madhya Pradesh",
        "marital_status": "अविवाहित", "children": "—",
        "family": "माता-पिता और एक भाई-बहन, परिवार के साथ रहते हैं",
        "expectations": "समझदार, सम्मान देने वाला और परिवार को महत्व देने वाला जीवनसाथी चाहिए। " * 12,
    }
    card = render.render_biodata(photo, details, False, "")
    assert card.width == 1080
    assert card.height > 1720


def test_post_layout_keeps_requested_canvas_size(monkeypatch):
    monkeypatch.setattr(render, "FONTS_DIR", Path(__file__).parents[1] / "fonts")
    photo = Image.new("RGB", (1080, 1350), (120, 80, 60))
    out = render.render_post(photo, "जीवन भर साथ निभाने वाले हमसफर की तलाश है", "अभी संपर्क करें और बात शुरू करें", False, "", "")
    assert out.size == (1080, 1350)
