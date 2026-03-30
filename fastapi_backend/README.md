---
title: Asuna Salon UK
emoji: 💇‍♀️
colorFrom: pink
colorTo: indigo
sdk: docker
app_port: 7860
---

Here is the step-by-step guide to installing uv it on your machine:

---

### 1. Installation Commands
Choose the command based on your Operating System:

* **Windows (PowerShell):**
    ```powershell
    powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
    ```
* **macOS / Linux:**
    ```bash
    curl -LsSf https://astral.sh/uv/install.sh | sh
    ```
* **Using pip (Alternative):**
    If you prefer using Python's own package manager to install it:
    ```bash
    pip install uv
    ```

---

### 2. Verify the Installation
After running the command, restart your terminal and type:
```bash
uv --version
```
If it returns a version number (e.g., `uv 0.5.x`), you are ready to go.

---

### 3. Using `uv` with your Project Structure
Now that `uv` is installed, here is how you should use it to fix those "Import not resolved" errors in your specific folders:

**For the Backend:**
1.  Navigate to the folder: `cd fastapi_backend`
2.  Install all dependencies from your `pyproject.toml`:
    ```bash
    uv sync
    ```
    *This creates a `.venv` folder automatically.*

**For the Frontend:**
1.  Navigate to the folder: `cd ../chainlit_frontend`
2.  Sync the frontend dependencies:
    ```bash
    uv sync
    ```

---

### 4. Why use `uv` instead of `pip`?
* **Speed:** It is often **10x to 100x faster** than pip at installing libraries.
* **No more Manual `venv`:** Running `uv sync` creates and manages the virtual environment for you.
* **Lockfiles:** The `uv.lock` file in your folder ensures that if you share this project with a client (like the salon owner), they get the exact same versions of the libraries you used.

---

### 5. Running your Apps with `uv`
Instead of activating the environment manually, you can just run:
* **To start FastAPI:** `uv run uvicorn fastapi_backend.main:app --reload`
* **To start Chainlit:** `uv run chainlit run src/chainlit_frontend/app.py`

### Suggested Next Step
Since you now have `uv` set up, would you like me to help you **add a new library** (like `openai` or `langchain`) to one of your `pyproject.toml` files using the `uv add` command?