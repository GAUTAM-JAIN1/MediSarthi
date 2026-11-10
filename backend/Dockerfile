FROM python:3.11-slim

# System deps: tesseract, poppler, portaudio
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    poppler-utils \
    libportaudio2 \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN pip install --no-cache-dir uv

# Create non-root user uid 1000 (HF requirement)
RUN useradd -m -u 1000 user
ENV HOME=/home/user \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app
RUN chown -R user:user /app /home/user

USER user

# Install dependencies
COPY --chown=user:user pyproject.toml uv.lock ./
RUN uv sync --no-dev --frozen --no-install-project

# Copy application files
COPY --chown=user:user src ./src
RUN uv sync --no-dev --frozen
COPY --chown=user:user knowledge ./knowledge
COPY --chown=user:user data/catalog ./data/catalog
COPY --chown=user:user data/demo ./data/demo

# Warm default embedder so there is no first-request download
RUN python -c "from chromadb.utils import embedding_functions as e; e.DefaultEmbeddingFunction()(['warmup'])"

ENV APP_ENV=production \
    CREWAI_TRACING_ENABLED=false \
    PYTHONUNBUFFERED=1

EXPOSE 7860

CMD uvicorn agents.main:app --host 0.0.0.0 --port 7860 --app-dir src
