FROM python:3.13-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy everything
COPY . .

# Install dependencies
RUN cd fastapi_backend && uv sync
RUN cd ../chainlit_frontend && uv sync

# Expose ports
EXPOSE 7860 8000

# Start both services
CMD ["sh", "-c", "\
  cd /app/fastapi_backend && uv run python -m uvicorn src.fastapi_backend.main:app --host 0.0.0.0 --port 8000 & \
  cd /app/chainlit_frontend && uv run chainlit run src/chainlit_frontend/app.py --host 0.0.0.0 --port 7860 & \
  wait"]