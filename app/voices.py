from dataclasses import dataclass

@dataclass(frozen=True)
class VoiceRoute:
    voice: str
    lang_code: str
    locale: str
    accent: str
    gender: str | None

ENGLISH_VOICES = (
    # American English - female
    "af_heart", "af_alloy", "af_aoede", "af_bella", "af_jessica",
    "af_kore", "af_nicole", "af_nova", "af_river", "af_sarah", "af_sky",
    # American English - male
    "am_adam", "am_echo", "am_eric", "am_fenrir", "am_liam",
    "am_michael", "am_onyx", "am_puck", "am_santa",
    # British English - female
    "bf_alice", "bf_emma", "bf_isabella", "bf_lily",
    # British English - male
    "bm_daniel", "bm_fable", "bm_george", "bm_lewis",
)

def resolve_voice(voice: str) -> VoiceRoute:
    if not voice or len(voice) < 2:
        raise ValueError("Invalid Kokoro voice name")

    language_prefix = voice[0].lower()
    gender_prefix = voice[1].lower()

    if language_prefix == "a":
        lang_code = "a"
        locale = "en-US"
        accent = "US"
    elif language_prefix == "b":
        lang_code = "b"
        locale = "en-GB"
        accent = "UK"
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

def voice_name(voice: str) -> str:
    raw = voice.split("_", 1)[1] if "_" in voice else voice
    return raw.replace("_", " ").title()

def voice_catalog() -> list[dict]:
    result = []
    for voice in ENGLISH_VOICES:
        route = resolve_voice(voice)
        result.append({
            "voice": voice,
            "name": voice_name(voice),
            "language": "en",
            "locale": route.locale,
            "accent": route.accent,
            "gender": route.gender,
        })
    return result
