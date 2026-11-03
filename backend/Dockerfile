FROM python:3.11-slim

# System deps:
#   tesseract-ocr -> OCR fallback for scanned/photo lab reports
#   poppler-utils -> pdf2image needs this for the scanned-PDF OCR fallback
#   libportaudio2  -> sounddevice (speech_to_text.py) needs this at import
#                     time or the whole app fails to boot. NOTE: this only
#                     fixes the import crash â€” actual microphone recording
#                     still won't work inside the container (no host mic
#                     access by default). Fine until that endpoint is
#                     actually exercised through Docker.
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    poppler-utils \
    libportaudio2 \
    && rm -rf /var/lib/apt/lists/*

# Install ngrok
RUN apt-get update && apt-get install -y curl gnupg && \
    curl -sSL https://ngrok-agent.s3.amazonaws.com/ngrok.asc \
      | tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null && \
    echo "deb https://ngrok-agent.s3.amazonaws.com buster main" \
      | tee /etc/apt/sources.list.d/ngrok.list && \
    apt-get update && apt-get install -y ngrok && \
    rm -rf /var/lib/apt/lists/*

    
WORKDIR /app

RUN pip install --no-cache-dir uv

# src MUST be copied before `uv sync` â€” this is an editable install
# (package name "agents" lives at src/agents/), and hatchling needs the
# actual source tree present to figure out what to build. Reversing this
# order breaks the build with a confusing hatchling/wheel error.
COPY pyproject.toml ./
COPY uv.lock* ./
COPY src ./src
RUN uv sync --no-dev

# FIX (Docker adaptability): buying_agent.py (price comparison, browser-use +
# Playwright) had zero browser binary available inside the container before
# this â€” the package `playwright` was installed via uv sync, but nothing
# ever ran `playwright install` to actually download a Chromium build, and
# the code was also pointing at a hardcoded Windows chrome.exe path (fixed
# separately in buying_agent.py). --with-deps pulls in the apt packages
# headless Chromium needs (fonts, libnss3, etc.) that python:3.11-slim
# doesn't have by default.
RUN uv run playwright install --with-deps chromium

COPY knowledge ./knowledge
COPY data/catalog ./data/catalog
# NOTE: no top-level `config/` folder in this project â€” CrewAI's YAML
# configs live inside src/agents/config/ and are already covered by the
# `COPY src ./src` line above. Don't re-add a separate COPY config step.

ENV PYTHONUNBUFFERED=1
EXPOSE 8080

CMD ["uv", "run", "uvicorn", "agents.main:app", "--host", "0.0.0.0", "--port", "8080", "--app-dir", "src"]