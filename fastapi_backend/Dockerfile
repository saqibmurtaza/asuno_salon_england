# Use a slim Python image
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install 'uv' for fast package management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set working directory
WORKDIR /app

# Copy the entire monorepo
COPY . .

# Install dependencies for both folders using uv
RUN cd fastapi_backend && uv sync
RUN cd chainlit_frontend && uv sync

# Expose the Hugging Face default port
EXPOSE 7860

# Start both services
# We use 'uv run' to ensure the virtual environments are used
CMD ["sh", "-c", "cd fastapi_backend && uv run uvicorn src.fastapi_backend.main:app --host 0.0.0.0 --port 8000 & cd chainlit_frontend && uv run chainlit run src/chainlit_frontend/app.py --host 0.0.0.0 --port 7860"]
