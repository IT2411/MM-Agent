from typing import Dict, Any
from google import genai
from google.genai import types
from app.tools.base import BaseTool
from app.config import settings
from app.utils.retry import execute_with_retry

client = genai.Client(api_key=settings.GEMINI_API_KEY)

def format_history_context(context: Dict[str, Any]) -> str:
    history_str = ""
    if context and "history" in context:
        for msg in context["history"][-5:]:
            role_name = "USER" if msg.role == "user" else "ASSISTANT"
            history_str += f"{role_name}: {msg.content}\n"
    return history_str


class ConversationalTool(BaseTool):
    @property
    def name(self) -> str:
        return "conversational_answering"

    @property
    def description(self) -> str:
        return "Used for general conversation, greetings, or friendly, helpful responses to general questions."

    async def execute(self, input_text: str, context: Dict[str, Any] = None) -> str:
        # Enforce English responses
        config = types.GenerateContentConfig(
            system_instruction=(
                "You are a friendly and helpful conversational assistant. "
                "You MUST respond in English only, even if the user or any document details are in another language, "
                "unless the user explicitly requests another language."
            ),
            temperature=0.7
        )

        contents = []
        if context and "history" in context:
            for msg in context["history"][-6:]:
                role = "user" if msg.role == "user" else "model"
                contents.append(
                    types.Content(
                        role=role,
                        parts=[types.Part.from_text(text=msg.content)]
                    )
                )

        contents.append(
            types.Content(
                role="user",
                parts=[types.Part.from_text(text=input_text)]
            )
        )

        response = await execute_with_retry(
            client.aio.models.generate_content,
            model=settings.GEMINI_MODEL,
            contents=contents,
            config=config
        )
        return response.text.strip()


class SummarizeTool(BaseTool):
    @property
    def name(self) -> str:
        return "summarization"

    @property
    def description(self) -> str:
        return "Used to summarize a body of text or a document. Produces a specific, rigid 3-part format."

    async def execute(self, input_text: str, context: Dict[str, Any] = None) -> str:
        history_context = format_history_context(context)

        # Robust block-parsing to extract the duration line following the header
        duration_info = ""
        combined_corpus = f"{history_context}\n{input_text}"
        if "--- Audio Duration ---" in combined_corpus:
            try:
                parts = combined_corpus.split("--- Audio Duration ---")
                if len(parts) > 1:
                    # Grab the text block immediately following the header and get its first line
                    duration_line = parts[1].strip().split("\n")[0].strip()
                    if duration_line:
                        duration_info = f"\n\n**Audio Duration**: {duration_line}"
            except Exception as e:
                # Graceful degradation in case of unexpected parsing errors
                duration_info = ""

        system_prompt = (
            "You are a strict summarization engine. You MUST write your entire response in English only.\n"
            "If the user's latest query is a short follow-up instruction (like 'summary' or 'summarize this'), "
            "inspect the conversation history to locate the main body of text, document contents, or data previously discussed, "
            "and perform the summary on that content.\n\n"
            "You must output exactly in this format:\n\n"
            "1-Line Summary:\n[Insert a clear, concise one-line summary here]\n\n"
            "Key Points:\n"
            "- [Point 1]\n"
            "- [Point 2]\n"
            "- [Point 3]\n\n"
            "Detailed Summary:\n[Insert a paragraph exactly 5 sentences long summarizing the details.]\n\n"
            "Do not add any additional introductory or concluding text."
        )

        prompt = (
            f"--- Conversation History ---\n{history_context}\n"
            f"--- Latest Input/Instruction ---\n{input_text}"
        )

        config = types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=0.3
        )

        response = await execute_with_retry(
            client.aio.models.generate_content,
            model=settings.GEMINI_MODEL,
            contents=prompt,
            config=config
        )
        
        final_summary = response.text.strip()
        # Append duration metadata safely
        if duration_info:
            final_summary += duration_info
            
        return final_summary


class SentimentTool(BaseTool):
    @property
    def name(self) -> str:
        return "sentiment_analysis"

    @property
    def description(self) -> str:
        return "Analyzes the emotional tone or sentiment of the input text or the text currently being discussed in the conversation history."

    async def execute(self, input_text: str, context: Dict[str, Any] = None) -> str:
        history_context = format_history_context(context)

        system_prompt = (
            "Analyze the sentiment of the text. You MUST write your entire response in English only.\n"
            "If the latest input is a short follow-up command (like 'sentiment' or 'analyze this'), "
            "look at the conversation history to identify the target text being discussed and perform the analysis on that target.\n\n"
            "Respond using only the following format:\n"
            "Label: [Positive / Negative / Neutral]\n"
            "Confidence: [Score between 0.0 and 1.0]\n"
            "Justification: [One-line explanation of why this label and confidence were assigned]"
        )

        prompt = (
            f"--- Conversation History ---\n{history_context}\n"
            f"--- Latest Input/Instruction ---\n{input_text}"
        )

        config = types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=0.1
        )

        response = await execute_with_retry(
            client.aio.models.generate_content,
            model=settings.GEMINI_MODEL,
            contents=prompt,
            config=config
        )
        return response.text.strip()


class CodeExplainTool(BaseTool):
    @property
    def name(self) -> str:
        return "code_explanation"

    @property
    def description(self) -> str:
        return "Explains program code. Identifies the programming language, explains its purpose, highlights bugs/vulnerabilities, and analyzes complexity."

    async def execute(self, input_text: str, context: Dict[str, Any] = None) -> str:
        history_context = format_history_context(context)

        system_prompt = (
            "Analyze and explain the code snippet. You MUST write your entire response in English only.\n"
            "If the latest query is a short command (like 'explain this code' or 'explain it'), "
            "look at the conversation history to locate the code block previously shared, and analyze that code.\n\n"
            "Format your response exactly as follows:\n"
            "1. Language Detected: [Name of language]\n"
            "2. Purpose & Explanation: [What the code does]\n"
            "3. Bug & Vulnerability Check: [List potential bugs, edge cases, or security issues, or state none found]\n"
            "4. Complexity Analysis: [Identify Time and Space complexity in Big O notation]"
        )

        prompt = (
            f"--- Conversation History ---\n{history_context}\n"
            f"--- Latest Input/Instruction ---\n{input_text}"
        )

        config = types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=0.2
        )

        response = await execute_with_retry(
            client.aio.models.generate_content,
            model=settings.GEMINI_MODEL,
            contents=prompt,
            config=config
        )
        return response.text.strip()