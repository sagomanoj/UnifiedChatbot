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

@app.post("/upload/{app_name}")
async def upload_manual(app_name: str, file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file uploaded")
    
    # Save to temp
    temp_dir = "data/temp"
    os.makedirs(temp_dir, exist_ok=True)
    file_path = f"{temp_dir}/{file.filename}"
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    try:
        # Ingest
        chunks = rag_service.ingest_document(file_path, app_name)
        
        # Cleanup
        os.remove(file_path)
        
        return {
            "message": f"Successfully uploaded {file.filename} for {app_name}",
            "chunks_added": chunks
        }
    except Exception as e:
        # Cleanup on error
        if os.path.exists(file_path):
            os.remove(file_path)
        
        import traceback
        traceback.print_exc()
        print(f"Error during ingestion: {str(e)}")
        
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

@app.get("/apps")
def get_apps():
    return {"apps": rag_service.get_available_apps()}
