from typing import Dict, Any
from google import genai
from google.genai import types
from app.tools.base import BaseTool
from app.config import settings

# Initialize the modern Gemini Client
# It automatically picks up GEMINI_API_KEY from your environment/.env
client = genai.Client(api_key=settings.GEMINI_API_KEY)

class ConversationalTool(BaseTool):
    @property
    def name(self) -> str:
        return "conversational_answering"

    @property
    def description(self) -> str:
        return "Used for general conversation, greetings, or friendly, helpful responses to general questions."

    async def execute(self, input_text: str, context: Dict[str, Any] = None) -> str:
        config = types.GenerateContentConfig(
            system_instruction="You are a friendly and helpful conversational assistant.",
            temperature=0.7
        )
        response = await client.aio.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=input_text,
            config=config
        )
        return response.text.strip()


class SummarizeTool(BaseTool):
    @property
    def name(self) -> str:
        return "summarization"

    @property
    def description(self) -> str:
        return "Used to summarize a body of text. Produces a specific, rigid 3-part format: 1-line summary, 3 key bullet points, and a 5-sentence summary."

    async def execute(self, input_text: str, context: Dict[str, Any] = None) -> str:
        system_prompt = (
            "You are a strict summarization engine. You must output exactly in this format:\n\n"
            "1-Line Summary:\n[Insert a clear, concise one-line summary here]\n\n"
            "Key Points:\n"
            "- [Point 1]\n"
            "- [Point 2]\n"
            "- [Point 3]\n\n"
            "Detailed Summary:\n[Insert a paragraph exactly 5 sentences long summarizing the details.]\n\n"
            "Do not add any additional introductory or concluding text."
        )
        config = types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=0.3
        )
        response = await client.aio.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=input_text,
            config=config
        )
        return response.text.strip()


class SentimentTool(BaseTool):
    @property
    def name(self) -> str:
        return "sentiment_analysis"

    @property
    def description(self) -> str:
        return "Analyzes the emotional tone or sentiment of the input text. Returns a label, confidence score, and one-line justification."

    async def execute(self, input_text: str, context: Dict[str, Any] = None) -> str:
        system_prompt = (
            "Analyze the sentiment of the text provided. Respond using only the following format:\n"
            "Label: [Positive / Negative / Neutral]\n"
            "Confidence: [Score between 0.0 and 1.0]\n"
            "Justification: [One-line explanation of why this label and confidence were assigned]"
        )
        config = types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=0.1
        )
        response = await client.aio.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=input_text,
            config=config
        )
        return response.text.strip()


class CodeExplainTool(BaseTool):
    @property
    def name(self) -> str:
        return "code_explanation"

    @property
    def description(self) -> str:
        return "Explains program code. Identifies the programming language, explains its purpose, highlights bugs/vulnerabilities, and analyzes time/space complexity."

    async def execute(self, input_text: str, context: Dict[str, Any] = None) -> str:
        system_prompt = (
            "Analyze and explain the provided code snippet. Format your response exactly as follows:\n"
            "1. Language Detected: [Name of language]\n"
            "2. Purpose & Explanation: [What the code does]\n"
            "3. Bug & Vulnerability Check: [List potential bugs, edge cases, or security issues, or state none found]\n"
            "4. Complexity Analysis: [Identify Time and Space complexity in Big O notation]"
        )
        config = types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=0.2
        )
        response = await client.aio.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=input_text,
            config=config
        )
        return response.text.strip()