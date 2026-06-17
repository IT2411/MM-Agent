import webbrowser
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import List, Optional

from app.tools.registry import registry
from app.tools.text_tools import ConversationalTool, SummarizeTool, SentimentTool, CodeExplainTool
from app.agent.executor import AgentExecutor, AgentResponse

# Register tools at module load
registry.register(ConversationalTool())
registry.register(SummarizeTool())
registry.register(SentimentTool())
registry.register(CodeExplainTool())

# Lifecycle manager to automatically open browser on startup
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Open browser in a new tab
    url = "http://127.0.0.1:8000"
    print(f"\n🚀 Launching interface at {url} ...\n")
    webbrowser.open_new_tab(url)
    yield
    # Shutdown logic can go here if needed

app = FastAPI(title="Multi-Modal Agent Backend", lifespan=lifespan)

# Conversation history schema
class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str

class ChatRequest(BaseModel):
    query: str
    extracted_text: Optional[str] = ""
    history: List[ChatMessage] = []

@app.post("/api/chat", response_model=AgentResponse)
async def process_chat(request: ChatRequest):
    if not request.query.strip() and not request.extracted_text.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")
    
    # We pass history through to the executor
    response = await AgentExecutor.run(
        user_query=request.query, 
        extracted_text=request.extracted_text,
        history=request.history
    )
    return response

# Serve the HTML UI at the root route
@app.get("/", response_class=HTMLResponse)
def get_ui():
    with open("app/templates/index.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

@app.get("/health")
def health_check():
    return {"status": "healthy", "registered_tools": [t.name for t in registry.list_tools()]}