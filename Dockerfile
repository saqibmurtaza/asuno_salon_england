FROM python:3.13-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy uv binaries
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy project files
COPY . .

# Sync both environments
RUN cd /app/fastapi_backend && uv sync
RUN cd /app/chainlit_frontend && uv sync

EXPOSE 7860 8000

# FIX: Run chainlit from the correct relative path
CMD ["sh", "-c", "\
  cd /app/fastapi_backend && uv run python -m uvicorn src.fastapi_backend.main:app --host 0.0.0.0 --port 8000 --log-level warning & \
  sleep 5; \
  cd /app/chainlit_frontend && uv run chainlit run app.py --host 0.0.0.0 --port 7860 --headless & \
  wait"]
  