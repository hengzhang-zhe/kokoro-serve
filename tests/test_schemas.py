import pytest
from pydantic import ValidationError

from app.schemas import SpeechRequest

def test_default_request():
    req = SpeechRequest(input="Hello")
    assert req.model == "kokoro"
    assert req.voice == "af_heart"
    assert req.response_format == "mp3"
    assert req.speed == 1.0

def test_speed_bounds():
    with pytest.raises(ValidationError):
        SpeechRequest(input="Hello", speed=0.1)
