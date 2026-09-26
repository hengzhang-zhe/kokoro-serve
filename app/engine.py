from __future__ import annotations

import asyncio
from functools import lru_cache

import numpy as np
from kokoro import KModel, KPipeline

from app.audio import encode_audio
from app.config import Settings, get_settings
from app.voices import resolve_voice

class KokoroServeEngine:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.model: KModel | None = None
        self.pipelines: dict[str, KPipeline] = {}
        self.semaphore = asyncio.Semaphore(settings.max_concurrency)

    def load(self) -> None:
        if self.model is not None:
            return

        self.model = (
            KModel(repo_id=self.settings.model_repo)
            .to(self.settings.device)
            .eval()
        )

        self.pipelines["a"] = KPipeline(
            lang_code="a",
            repo_id=self.settings.model_repo,
            model=self.model,
            device=self.settings.device,
        )
        self.pipelines["b"] = KPipeline(
            lang_code="b",
            repo_id=self.settings.model_repo,
            model=self.model,
            device=self.settings.device,
        )

    async def synthesize(
        self,
        text: str,
        voice: str,
        speed: float,
        response_format: str,
    ) -> bytes:
        if self.model is None:
            raise RuntimeError("Kokoro engine has not been initialized")

        route = resolve_voice(voice)

        async with self.semaphore:
            return await asyncio.to_thread(
                self._synthesize_sync,
                text,
                voice,
                speed,
                response_format,
                route.lang_code,
            )

    def _synthesize_sync(
        self,
        text: str,
        voice: str,
        speed: float,
        response_format: str,
        lang_code: str,
    ) -> bytes:
        pipeline = self.pipelines[lang_code]
        chunks: list[np.ndarray] = []

        for result in pipeline(
            text,
            voice=voice,
            speed=speed,
            model=self.model,
        ):
            audio = result.audio
            if audio is not None:
                chunks.append(np.asarray(audio, dtype=np.float32))

        if not chunks:
            raise RuntimeError("Kokoro returned no audio")

        waveform = np.concatenate(chunks)

        return encode_audio(
            waveform,
            self.settings.sample_rate,
            response_format,
        )

@lru_cache
def get_engine() -> KokoroServeEngine:
    return KokoroServeEngine(get_settings())
