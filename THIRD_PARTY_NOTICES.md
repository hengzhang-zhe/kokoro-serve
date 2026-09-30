# Third-party notices

Typingo Kokoro contains its own API/service code and does not vendor the Kokoro model weights or voice files.

Runtime dependencies include:

- `hexgrad/kokoro` — official Kokoro inference library.
- `hexgrad/Kokoro-82M` — official Kokoro-82M model repository.
- `espeak-ng`
- `ffmpeg`
- `libsndfile`
- Python packages listed in `requirements.txt`

Each dependency remains under its own license.

The upstream `hexgrad/Kokoro-82M` model repository currently declares Apache-2.0. Before a commercial release or upstream version upgrade, verify the exact licenses and notices for the model, voices and runtime packages used in that release.
