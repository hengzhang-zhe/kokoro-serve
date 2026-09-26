import pytest

from app.voices import resolve_voice

def test_us_female_voice():
    route = resolve_voice("af_heart")
    assert route.lang_code == "a"
    assert route.locale == "en-US"
    assert route.gender == "female"

def test_uk_male_voice():
    route = resolve_voice("bm_george")
    assert route.lang_code == "b"
    assert route.locale == "en-GB"
    assert route.gender == "male"

def test_unsupported_language_rejected():
    with pytest.raises(ValueError):
        resolve_voice("jf_alpha")
