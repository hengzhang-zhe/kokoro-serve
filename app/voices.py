from dataclasses import dataclass

@dataclass(frozen=True)
class VoiceRoute:
    voice: str
    lang_code: str
    locale: str
    accent: str
    gender: str | None

def resolve_voice(voice: str) -> VoiceRoute:
    if not voice or len(voice) < 2:
        raise ValueError("Invalid Kokoro voice name")

    language_prefix = voice[0].lower()
    gender_prefix = voice[1].lower()

    if language_prefix == "a":
        lang_code = "a"
        locale = "en-US"
        accent = "American English"
    elif language_prefix == "b":
        lang_code = "b"
        locale = "en-GB"
        accent = "British English"
    else:
        raise ValueError(
            "Kokoro Serve currently enables English voices only: "
            "a*=American English, b*=British English"
        )

    gender = {"f": "female", "m": "male"}.get(gender_prefix)

    return VoiceRoute(
        voice=voice,
        lang_code=lang_code,
        locale=locale,
        accent=accent,
        gender=gender,
    )
