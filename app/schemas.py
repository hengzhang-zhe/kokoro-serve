from typing import Literal

from pydantic import BaseModel, Field

AudioFormat = Literal["mp3", "wav", "flac", "opus"]

class SpeechRequest(BaseModel):
    model: str = Field(default="kokoro")
    input: str = Field(min_length=1)
    voice: str = Field(default="af_heart")
    response_format: AudioFormat = Field(default="mp3")
    speed: float = Field(default=1.0, ge=0.5, le=2.0)
