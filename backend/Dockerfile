FROM python:3.11-slim

# System deps:
#   tesseract-ocr -> OCR fallback for scanned/photo lab reports
#   poppler-utils -> pdf2image needs this for the scanned-PDF OCR fallback
#   libportaudio2  -> sounddevice (speech_to_text.py) needs this at import
#                     time or the whole app fails to boot. NOTE: this only
#                     fixes the import crash — actual microphone recording
#                     still won't work inside the container (no host mic
#                     access by default). Fine until that endpoint is
#                     actually exercised through Docker.
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    poppler-utils \
    libportaudio2 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN pip install --no-cache-dir uv

# src MUST be copied before `uv sync` — this is an editable install
# (package name "agents" lives at src/agents/), and hatchling needs the
# actual source tree present to figure out what to build. Reversing this
# order breaks the build with a confusing hatchling/wheel error.
COPY pyproject.toml ./
COPY uv.lock* ./
COPY src ./src
RUN uv sync --no-dev

COPY knowledge ./knowledge
# NOTE: no top-level `config/` folder in this project — CrewAI's YAML
# configs live inside src/agents/config/ and are already covered by the
# `COPY src ./src` line above. Don't re-add a separate COPY config step.

ENV PYTHONUNBUFFERED=1
EXPOSE 8080

CMD ["uv", "run", "uvicorn", "agents.main:app", "--host", "0.0.0.0", "--port", "8080", "--app-dir", "src"]