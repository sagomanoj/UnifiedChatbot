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

2.  **Configure Environment**:
    - Copy `.env.example` to `.env`.
    - Fill in your `OPENAI_API_KEY` (and Azure settings if applicable).

3.  **Run Backend**:
    ```bash
    uvicorn backend.main:app --reload
    ```
    The API will be available at `http://localhost:8000`.

4.  **Run Frontend**:
    - For the Chatbot: Open `frontend/index.html` in your browser.
    - For Management: Open `frontend/management.html` to add apps and upload manuals.

## Usage

1.  **Select Application**: Use the header dropdown to switch between "Food Delivery", "E-Commerce", etc.
2.  **Upload Manual**: Open the chat widget and click "Context Manual" to upload a PDF/TXT for the *current* application.
3.  **Chat**: Ask questions. The context will be restricted to the selected application.
4.  **Comparison Mode**: Check "Enable Comparison Mode" to ask questions across all uploaded manuals.

## Directory Structure

- `backend/`: FastAPI application and RAG logic.
- `frontend/`: HTML/JS simulation of the host app.
- `data/`: Stores uploaded chunks and vector database.
