import json
from typing import List, Optional
from pydantic import BaseModel
from google import genai
from google.genai import types
from app.config import settings
from app.tools.registry import registry
from app.utils.retry import execute_with_retry

class ChatMessage(BaseModel):
    role: str
    content: str

class PlanResult(BaseModel):
    is_clear: bool
    follow_up_question: Optional[str] = None
    selected_tool: Optional[str] = None
    reasoning: str

# Initialize Gemini Client
client = genai.Client(api_key=settings.GEMINI_API_KEY)

async def plan_task(user_query: str, extracted_text: str, history: List[ChatMessage]) -> PlanResult:
    """
    Evaluates context, current input, and conversation history using Gemini.
    """
    tools_desc = "\n".join([f"- {t.name}: {t.description}" for t in registry.list_tools()])
    
    # Format the conversational history for the planner's context
    formatted_history = ""
    for msg in history[-6:]:  # Keep rolling history window
        formatted_history += f"{msg.role.upper()}: {msg.content}\n"

    system_instruction = (
        "You are an intelligent orchestrator for a multi-task agent.\n"
        "Your job is to inspect the latest user query, any extracted text context, and the conversation history, then determine the next step.\n\n"
        "Rules:\n"
        "1. Context Resolution: If the user's latest query is a short follow-up (e.g., 'Who was the second?', 'Why?', 'Explain it', 'Summarize that instead') "
        "that refers to something in the conversation history, you MUST resolve the reference using that history. "
        "Do not flag it as ambiguous if the history makes it clear what they are talking about.\n"
        "2. For general conversational follow-up questions (such as asking about 'the second' moonwalker), resolve the reference and select the 'conversational_answering' tool.\n"
        "3. Only set `is_clear` to false and generate a `follow_up_question` if the request is genuinely unresolvable even after reviewing the entire history and context.\n\n"
        "Available Tools:\n"
        f"{tools_desc}\n\n"
        "You must respond with a raw JSON object matching this schema:\n"
        "{\n"
        "  \"is_clear\": bool,\n"
        "  \"follow_up_question\": \"string or null\",\n"
        "  \"selected_tool\": \"string or null\",\n"
        "  \"reasoning\": \"string explaining your planning logic\"\n"
        "}"
    )

    config = types.GenerateContentConfig(
        system_instruction=system_instruction,
        response_mime_type="application/json",
        temperature=0.1
    )

    combined_input = (
        f"--- CONVERSATION HISTORY ---\n{formatted_history}\n"
        f"--- CURRENT INPUTS ---\n"
        f"Latest User Query: {user_query}\n"
        f"Extracted Context (if any): {extracted_text}"
    )

    response = await execute_with_retry(
        client.aio.models.generate_content,
        model=settings.GEMINI_MODEL,
        contents=combined_input,
        config=config
    )
    
    raw_json = response.text.strip()
    data = json.loads(raw_json)
    return PlanResult(**data)