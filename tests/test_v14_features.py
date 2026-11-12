import sys
import types

try:
    import gradio  # noqa: F401
except ImportError:
    gradio_stub = types.ModuleType("gradio")
    gradio_stub.SelectData = type("SelectData", (), {})
    sys.modules["gradio"] = gradio_stub

from app import config, render, textgen


def test_biodata_card_keeps_only_requested_fields():
    fields = render.biodata_card_fields({
        "lang": "Hindi", "name_hindi": "कविता शर्मा", "name_roman": "Kavita Sharma",
        "age": 31, "height": "5 फुट 4 इंच", "community": "Hidden community",
        "children": "Hidden children", "education": "बी.ए.", "job": "टीचर",
        "city": "भोपाल", "state": "Madhya Pradesh", "marital_status": "अविवाहित",
        "family": "मिलजुला परिवार", "expectations": "मेहनत, अपनापन और हँसी—यही मेरी पहचान है।",
    })
    assert fields["meta"] == "31 वर्ष  •  5 फुट 4 इंच"
    assert [label for label, _ in fields["rows"]] == ["पढ़ाई", "जॉब", "शहर", "स्टेटस", "फैमिली"]
    assert fields["rows"][2][1] == "भोपाल"
    assert fields["labels"]["want"] == "रिश्ते की खूबसूरत बात:"
    assert "Hidden community" not in str(fields)
    assert "Hidden children" not in str(fields)
    assert "Madhya Pradesh" not in str(fields)


def test_fallback_profiles_have_distinct_family_and_highlight_copy():
    history = {"family": [], "expectations": []}
    names = []
    opts = {"type": "Marriage", "gender": "Female", "state": "Maharashtra",
            "community": "Maratha", "lang": "Hindi", "full_name": True}
    generated = []
    for _ in range(20):
        details = textgen.fallback_bio(opts, names, lambda name: name in names, history)
        names.append(details["name_roman"].split()[0])
        history["family"].append(details["family"])
        history["expectations"].append(details["expectations"])
        generated.append(details)
    assert len({item["family"] for item in generated}) == 20
    assert len({item["expectations"] for item in generated}) == 20


def test_regenerated_values_change_and_remain_valid():
    opts = {"type": "Marriage", "gender": "Female", "state": "Maharashtra"}
    current_age = "31"
    new_age = textgen.alternate_bio_value("age", current_age, opts, {}, lambda _name: False)
    new_education = textgen.alternate_bio_value("education", "बी.ए.", opts, {}, lambda _name: False)
    new_city = textgen.alternate_bio_value("city", "पुणे", opts, {"lang": "Hindi"}, lambda _name: False)
    assert new_age != current_age
    assert 28 <= int(new_age) <= 34
    assert new_education in textgen.EDUCATION and new_education != "बी.ए."
    assert new_city in textgen.CITY_CHOICES["Maharashtra"] and new_city != "पुणे"


def test_every_supported_state_has_a_fallback_city():
    assert set(config.STATES) == set(textgen.CITY_CHOICES)
    assert all(textgen.CITIES[state] in textgen.CITY_CHOICES[state] for state in config.STATES)


def test_refresh_line_skips_the_current_line():
    current = "मेहनत, अपनापन और हँसी—यही मेरी पहचान है।"
    replacement = textgen.fresh_bio_phrase("expectations", {"expectations": []}, current=current)
    assert replacement != current
    assert "partner" not in replacement.lower()
