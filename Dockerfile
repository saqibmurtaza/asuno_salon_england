# Use a slim Python image
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy the entire monorepo
COPY . .

# Install dependencies
RUN pip install --no-cache-dir -r fastapi_backend/requirements.txt
RUN pip install --no-cache-dir -r chainlit_frontend/requirements.txt

# Expose ports
EXPOSE 7860 8000

# Start both services
CMD ["sh", "-c", "cd fastapi_backend && python -m uvicorn src.fastapi_backend.main:app --host 0.0.0.0 --port 8000 & cd ../chainlit_frontend && chainlit run src/chainlit_frontend/app.py --host 0.0.0.0 --port 7860 && wait"]
