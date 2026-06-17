import json
from typing import Optional
from pydantic import BaseModel
from google import genai
from google.genai import types
from app.config import settings
from app.tools.registry import registry

class PlanResult(BaseModel):
    is_clear: bool
    follow_up_question: Optional[str] = None
    selected_tool: Optional[str] = None
    reasoning: str

# Initialize Gemini Client
client = genai.Client(api_key=settings.GEMINI_API_KEY)

async def plan_task(user_query: str, extracted_text: str) -> PlanResult:
    """
    Evaluates the input to determine if the user's intent is clear using the modern Gemini SDK.
    """
    tools_desc = "\n".join([f"- {t.name}: {t.description}" for t in registry.list_tools()])
    
    system_instruction = (
        "You are an intelligent orchestrator for a multi-task agent.\n"
        "Your job is to inspect the user query and any extracted text content, then determine the next step.\n\n"
        "Rules:\n"
        "1. If the user query is ambiguous, missing, or just contains a raw document/text with no clear instruction "
        "on what to do with it, you MUST set `is_clear` to false and generate a short, friendly `follow_up_question` "
        "asking what they want to do. Do not guess.\n"
        "2. If the goal is clear, select the best single tool from the available tools list.\n\n"
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

    combined_input = f"User Query: {user_query}\nExtracted Context: {extracted_text}"

    response = await client.aio.models.generate_content(
        model=settings.GEMINI_MODEL,
        contents=combined_input,
        config=config
    )
    
    raw_json = response.text.strip()
    data = json.loads(raw_json)
    return PlanResult(**data)