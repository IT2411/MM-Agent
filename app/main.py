from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from app.tools.registry import registry
from app.tools.text_tools import ConversationalTool, SummarizeTool, SentimentTool, CodeExplainTool
from app.agent.executor import AgentExecutor, AgentResponse

# Initialize app
app = FastAPI(title="Multi-Modal Agent Backend (Phase 1: Text)")

# Register available tools
registry.register(ConversationalTool())
registry.register(SummarizeTool())
registry.register(SentimentTool())
registry.register(CodeExplainTool())

class ChatRequest(BaseModel):
    query: str
    extracted_text: str = ""

@app.post("/api/chat", response_model=AgentResponse)
async def process_chat(request: ChatRequest):
    if not request.query.strip() and not request.extracted_text.strip():
        raise HTTPException(status_code=400, detail="Inputs cannot both be empty.")
    
    response = await AgentExecutor.run(
        user_query=request.query, 
        extracted_text=request.extracted_text
    )
    return response

@app.get("/health")
def health_check():
    return {"status": "healthy", "registered_tools": [t.name for t in registry.list_tools()]}