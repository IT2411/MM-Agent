import json
from typing import List, Optional
from pydantic import BaseModel
from google import genai
from google.genai import types
from app.config import settings
from app.tools.registry import registry

class ChatMessage(BaseModel):
    role: str
    content: str

class PlanResult(BaseModel):
    is_clear: bool
    follow_up_question: Optional[str] = None
    selected_tool: Optional[str] = None
    reasoning: str

client = genai.Client(api_key=settings.GEMINI_API_KEY)

async def plan_task(user_query: str, extracted_text: str, history: List[ChatMessage]) -> PlanResult:
    """
    Evaluates context, current input, and conversation history using Gemini.
    """
    tools_desc = "\n".join([f"- {t.name}: {t.description}" for t in registry.list_tools()])
    
    # Format the conversational history for the planner's context
    formatted_history = ""
    for msg in history[-6:]:  # Keep the last ~6 messages to maintain context limits
        formatted_history += f"{msg.role.upper()}: {msg.content}\n"

    system_instruction = (
        "You are an intelligent orchestrator for a multi-task agent.\n"
        "Your job is to inspect the user query, any extracted text content, and the conversation history, then determine the next step.\n\n"
        "Rules:\n"
        "1. If the current user query is a reply to a previous clarification or follow-up question (visible in the Conversation History), "
        "re-evaluate the context of the whole conversation. Use the previously extracted text/code combined with the user's latest query to fulfill their intent.\n"
        "2. If the user's overall goal is still ambiguous or missing, set `is_clear` to false and generate a short, friendly `follow_up_question` asking what they want to do.\n"
        "3. If the goal is clear, select the best single tool from the available tools list.\n\n"
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

    response = await client.aio.models.generate_content(
        model=settings.GEMINI_MODEL,
        contents=combined_input,
        config=config
    )
    
    raw_json = response.text.strip()
    data = json.loads(raw_json)
    return PlanResult(**data)