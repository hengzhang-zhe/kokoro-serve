from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

from app.audio import MEDIA_TYPES
from app.config import get_settings
from app.engine import get_engine
from app.schemas import SpeechRequest
from app.voices import resolve_voice

router = APIRouter()
settings = get_settings()

@router.get("/health")
def health():
    engine = get_engine()
    return {
        "status": "ok",
        "service": settings.app_name,
        "version": settings.app_version,
        "model_repo": settings.model_repo,
        "device": settings.device,
        "loaded": engine.model is not None,
    }

@router.get("/v1/models")
def models():
    return {
        "object": "list",
        "data": [{
            "id": "kokoro",
            "object": "model",
            "owned_by": "hexgrad",
            "source": settings.model_repo,
        }],
    }

@router.get("/v1/audio/voices")
def voices():
    return {
        "source": settings.model_repo,
        "supported_prefixes": {
            "af_*": {"locale": "en-US", "gender": "female"},
            "am_*": {"locale": "en-US", "gender": "male"},
            "bf_*": {"locale": "en-GB", "gender": "female"},
            "bm_*": {"locale": "en-GB", "gender": "male"},
        },
        "recommended": [
            "af_heart",
            "af_bella",
            "am_michael",
            "bf_emma",
            "bm_george",
        ],
    }

@router.post("/v1/audio/speech")
async def speech(request: SpeechRequest):
    if request.model not in {"kokoro", "Kokoro-82M", settings.model_repo}:
        raise HTTPException(
            status_code=400,
            detail="Only the Kokoro model is supported",
        )

    text = request.input.strip()
    if not text:
        raise HTTPException(status_code=400, detail="input cannot be blank")

    if len(text) > settings.max_input_chars:
        raise HTTPException(
            status_code=413,
            detail=f"input exceeds {settings.max_input_chars} characters",
        )

    try:
        resolve_voice(request.voice)
        data = await get_engine().synthesize(
            text=text,
            voice=request.voice,
            speed=request.speed,
            response_format=request.response_format,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"TTS synthesis failed: {exc}",
        ) from exc

    return Response(
        content=data,
        media_type=MEDIA_TYPES[request.response_format],
    )
