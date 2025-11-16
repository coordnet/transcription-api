FROM nvidia/cuda:12.2.2-cudnn9-runtime-ubuntu22.04
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

WORKDIR /app

RUN apt-get update && apt-get install -y \
    wget python3-pip \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

ARG MODEL=turbo
ENV MODEL=$MODEL

RUN mkdir -p /app/models/

# Map 'turbo' to 'large-v3-turbo' for HuggingFace model path
RUN if [ "$MODEL" = "turbo" ]; then \
        MODEL_PATH="large-v3-turbo"; \
    else \
        MODEL_PATH="$MODEL"; \
    fi && \
    wget -O /app/models/config.json https://huggingface.co/Systran/faster-whisper-${MODEL_PATH}/resolve/main/config.json && \
    wget -O /app/models/model.bin https://huggingface.co/Systran/faster-whisper-${MODEL_PATH}/resolve/main/model.bin && \
    wget -O /app/models/tokenizer.json https://huggingface.co/Systran/faster-whisper-${MODEL_PATH}/resolve/main/tokenizer.json && \
    wget -O /app/models/vocabulary.txt https://huggingface.co/Systran/faster-whisper-${MODEL_PATH}/resolve/main/vocabulary.txt

# Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1

# Copy from the cache instead of linking since it's a mounted volume
ENV UV_LINK_MODE=copy

# Install the project's dependencies using the lockfile and settings
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project --python /usr/bin/python3

# Copy the project files to the container
ADD . /app
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --python /usr/bin/python3

# Place executables in the environment at the front of the path
ENV PATH="/app/.venv/bin:$PATH"

# Reset the entrypoint, don't invoke `uv`
ENTRYPOINT []

# Expose the application port
EXPOSE 3000

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Run the application
CMD ["flask", "--app", "src/main", "--debug", "run", "--host", "0.0.0.0", "--port", "3000"]
