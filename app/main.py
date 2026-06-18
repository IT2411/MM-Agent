import json
import webbrowser
from contextlib import asynccontextmanager
from typing import List, Optional
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.responses import HTMLResponse
from pydantic import TypeAdapter

from app.tools.registry import registry
from app.agent.executor import AgentExecutor, AgentResponse, ChatMessage
from app.utils.extractor import extract_text_from_file

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Print a prominent, clickable link in the terminal on startup
    url = "http://127.0.0.1:8000"
    print("\n" + "="*60)
    print(f"👉 Click here to open the Agentic Workspace: {url}")
    print("="*60 + "\n")
    yield

app = FastAPI(title="Multi-Modal Agent Backend", lifespan=lifespan)

chat_history_adapter = TypeAdapter(List[ChatMessage])

# Global Backend Session Store to preserve document context safely across turns
ACTIVE_DOCUMENT_CONTEXT = ""

@app.post("/api/chat", response_model=AgentResponse)
async def process_chat(
    query: str = Form(""),
    history: str = Form("[]"),
    extracted_text: str = Form(""),  # Handled natively on backend now
    files: Optional[List[UploadFile]] = File(None)
):
    global ACTIVE_DOCUMENT_CONTEXT
    
    try:
        parsed_history = chat_history_adapter.validate_json(history)
    except Exception:
        parsed_history = []

    combined_extracted_text = ""

    # 1. If new files are uploaded, extract and store their text
    if files:
        extracted_contents = []
        for file in files:
            if file.filename:
                file_text = await extract_text_from_file(file)
                
                # OCR Fallback
                if file.filename.lower().endswith(".pdf") and not file_text.strip():
                    from google.genai import types
                    from google import genai
                    from app.config import settings
                    
                    print(f"Programmatic PDF parsing yielded nothing for {file.filename}. Triggering OCR fallback...")
                    client = genai.Client(api_key=settings.GEMINI_API_KEY)
                    
                    await file.seek(0)
                    pdf_bytes = await file.read()
                    
                    response = await client.aio.models.generate_content(
                        model=settings.GEMINI_MODEL,
                        contents=[
                            types.Part.from_bytes(data=pdf_bytes, mime_type="application/pdf"),
                            "Perform complete OCR on this document and transcribe all text perfectly."
                        ]
                    )
                    file_text = response.text.strip()

                if file_text.strip():
                    extracted_contents.append(f"--- Extracted from {file.filename} ---\n{file_text}")
        
        combined_extracted_text = "\n\n".join(extracted_contents)
        # Update the Backend Session Store with the newly extracted text
        ACTIVE_DOCUMENT_CONTEXT = combined_extracted_text
        
    else:
        # 2. If no new files are uploaded, reuse our robust backend session context!
        combined_extracted_text = ACTIVE_DOCUMENT_CONTEXT

    # Execute the agent query
    response = await AgentExecutor.run(
        user_query=query, 
        extracted_text=combined_extracted_text,
        history=parsed_history
    )
    
    # Send the active context back (retains compatibility)
    response.extracted_text = combined_extracted_text
    return response

@app.get("/", response_class=HTMLResponse)
def get_ui():
    with open("app/templates/index.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

@app.get("/health")
def health_check():
    return {"status": "healthy", "registered_tools": [t.name for t in registry.list_tools()]}