FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

ARG TORCH_INDEX_URL=https://download.pytorch.org/whl/cpu

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       espeak-ng \
       ffmpeg \
       libsndfile1 \
       curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .

# Install CPU-only PyTorch first so Kokoro does not pull CUDA/NVIDIA wheels
# from the default PyPI dependency resolution path.
RUN pip install --upgrade pip \
    && pip install --index-url ${TORCH_INDEX_URL} torch \
    && pip install -r requirements.txt

COPY app ./app
COPY web ./web

EXPOSE 9000

HEALTHCHECK --interval=30s --timeout=5s --start-period=120s --retries=5 \
  CMD curl -fsS http://127.0.0.1:9000/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "9000", "--workers", "1"]
