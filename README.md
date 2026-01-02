# Unified Multi-Application Chatbot POC

A unified chatbot that serves multiple applications (Food Delivery, E-Commerce, etc.) with strict context isolation and a comparison mode.

## Prerequisites

- Python 3.9+
- OpenAI API Key (Set as `OPENAI_API_KEY` env var)

## Setup

1.  **Install Dependencies**:
    ```bash
    python -m venv .venv
    .\.venv\Scripts\activate
    pip install -r requirements.txt
    ```

2.  **Run Backend**:
    ```bash
    uvicorn backend.main:app --reload
    ```
    The API will be available at `http://localhost:8000`.

3.  **Run Frontend**:
    Open `frontend/index.html` in your browser.

## Usage

1.  **Select Application**: Use the header dropdown to switch between "Food Delivery", "E-Commerce", etc.
2.  **Upload Manual**: Open the chat widget and click "Context Manual" to upload a PDF/TXT for the *current* application.
3.  **Chat**: Ask questions. The context will be restricted to the selected application.
4.  **Comparison Mode**: Check "Enable Comparison Mode" to ask questions across all uploaded manuals.

## Directory Structure

- `backend/`: FastAPI application and RAG logic.
- `frontend/`: HTML/JS simulation of the host app.
- `data/`: Stores uploaded chunks and vector database.
