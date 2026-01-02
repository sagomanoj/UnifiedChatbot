import os
import shutil
from typing import Optional
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from backend.rag_service import RAGService

# Simple .env loader to avoid extra dependencies for POC
def load_env():
    if os.path.exists(".env"):
        with open(".env", "r") as f:
            for line in f:
                if "=" in line and not line.startswith("#"):
                    key, value = line.strip().split("=", 1)
                    os.environ[key] = value

load_env()

app = FastAPI(title="Unified Multi-Application Chatbot POC")

# CORS Middleware (Enable all for POC)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize RAG Service
rag_service = RAGService()

@app.on_event("startup")
async def startup_event():
    # Run ingestion in a separate thread/process if possible, but for POC synchronous is okay 
    # (starts after server is ready to accept connections? No, startup blocks server start).
    # But it allows "import main" to succeed.
    print("Triggering startup ingestion...")
    rag_service.ingest_existing_manuals()

class ChatRequest(BaseModel):
    query: str
    app: str

class ChatResponse(BaseModel):
    response: str
    app: str

@app.get("/")
def read_root():
    return {"message": "Unified Chatbot API is running"}

@app.get("/apps")
async def get_apps():
    # Return list of strings for the frontend dropdown
    return rag_service.get_available_apps()

# --- Management Endpoints ---

@app.get("/management/apps")
async def get_apps_detailed():
    # Return the full objects (name, manual) for the management dashboard
    return rag_service.get_apps_full()

@app.post("/management/apps")
async def add_app(data: dict):
    name = data.get("name")
    if not name:
        raise HTTPException(status_code=400, detail="Name is required")
    rag_service.add_app(name)
    return {"message": f"App {name} added"}

@app.delete("/management/apps/{name}")
async def delete_app(name: str):
    rag_service.delete_app(name)
    return {"message": f"App {name} deleted"}

@app.post("/management/upload/{app_name}")
async def upload_management_manual(app_name: str, file: UploadFile = File(...)):
    # Manuals directory from rag_service context
    manuals_dir = "./data/user_manual"
    if not os.path.exists(manuals_dir):
        os.makedirs(manuals_dir)
        
    file_path = os.path.join(manuals_dir, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    try:
        chunks = rag_service.ingest_document(file_path, app_name, clear_existing=True)
        return {"message": f"Manual updated for {app_name}", "filename": file.filename, "chunks": chunks}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        response_text = rag_service.query(request.query, request.app)
        return ChatResponse(response=response_text, app=request.app)
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
