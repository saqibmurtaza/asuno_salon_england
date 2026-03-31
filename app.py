import subprocess
import sys
import time
import os

# 1. Start FastAPI Backend in the background
print("Starting FastAPI backend on port 8000...")
backend_process = subprocess.Popen([
    sys.executable, "-m", "uvicorn", 
    "fastapi_backend.src.fastapi_backend.main:app", 
    "--host", "0.0.0.0", 
    "--port", "8000"
])

# Give the backend a few seconds to initialize
time.sleep(5)

# 2. Start Chainlit Frontend on HF's required port 7860
print("Starting Chainlit frontend on port 7860...")
subprocess.run([
    sys.executable, "-m", "chainlit", "run",
    "chainlit_frontend/app.py",
    "--host", "0.0.0.0",
    "--port", "7860",
    "--headless"
])