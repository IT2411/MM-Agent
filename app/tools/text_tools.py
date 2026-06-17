import re
from typing import Dict, Any
from google import genai
from google.genai import types
from app.tools.base import BaseTool
from app.config import settings
from app.utils.retry import execute_with_retry

client = genai.Client(api_key=settings.GEMINI_API_KEY)

def format_history_context(context: Dict[str, Any]) -> str:
    """Helper to format previous turns safely as reference context for tools."""
    history_str = ""
    if context and "history" in context:
        for msg in context["history"][-5:]:
            # Defensive check for dict vs object structures
            if isinstance(msg, dict):
                role = msg.get("role", "user")
                content = msg.get("content", "")
            else:
                role = getattr(msg, "role", "user")
                content = getattr(msg, "content", "")
            
            role_name = "USER" if role == "user" else "ASSISTANT"
            history_str += f"{role_name}: {content}\n"
    return history_str


class ConversationalTool(BaseTool):
    @property
    def name(self) -> str:
        return "conversational_answering"

    @property
    def description(self) -> str:
        return (
            "Used for general conversation, greetings, and answering specific informational questions, "
            "lookups, or Q&A queries about a provided document or context (e.g., 'What are the action items?', "
            "'Who is mentioned in this file?', 'What was the decision on budget?')."
        )

    async def execute(self, input_text: str, context: Dict[str, Any] = None) -> str:
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
                # Defensive check for dict vs object structures
                if isinstance(msg, dict):
                    role = msg.get("role", "user")
                    content = msg.get("content", "")
                else:
                    role = getattr(msg, "role", "user")
                    content = getattr(msg, "content", "")
                
                contents.append(
                    types.Content(
                        role="user" if role == "user" else "model",
                        parts=[types.Part.from_text(text=content)]
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

        duration_info = ""
        combined_corpus = f"{history_context}\n{input_text}"
        if "--- Audio Duration ---" in combined_corpus:
            for line in combined_corpus.split("\n"):
                if "Audio Duration" in line or (line.strip() and "min" in line and "sec" in line):
                    clean_line = line.replace("--- Audio Duration ---", "").replace("---", "").strip()
                    duration_info = f"\n\n**Audio Duration**: {clean_line}"
                    break

        system_prompt = (
            "You are a strict summarization engine. You MUST write your entire response in English only.\n"
            "Always prioritize summarizing the text provided in the '[Extracted Document Context]' or current input first.\n"
            "Only if the latest user query is a short follow-up instruction (like 'summary' or 'summarize this') and lacks context, "
            "inspect the conversation history to locate the main body of text previously discussed.\n\n"
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
            "Always prioritize analyzing the text provided in the '[Extracted Document Context]' or current input first.\n"
            "Only if the latest input is a short follow-up command (like 'sentiment' or 'analyze this') and lacks context, "
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
            "Analyze and explain the provided code snippet. You MUST write your entire response in English only.\n"
            "Always prioritize analyzing the code provided in the '[Extracted Document Context]' or current input first.\n"
            "Only if the latest input is a short command (like 'explain this code' or 'explain it') and lacks context, "
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
    
        
class YouTubeTranscriptTool(BaseTool):
    @property
    def name(self) -> str:
        return "youtube_transcript_fetching"

    @property
    def description(self) -> str:
        return "Used only when the user explicitly asks to fetch, transcribe, summarize, or analyze the content of a YouTube video or URL."

    def _extract_video_id(self, text: str) -> str:
        """Parses standard, shortened, mobile, and embed YouTube URLs to extract the 11-char Video ID."""
        patterns = [
            r"youtube\.com/watch\?v=([a-zA-Z0-9_-]{11})",
            r"youtu\.be/([a-zA-Z0-9_-]{11})",
            r"youtube\.com/embed/([a-zA-Z0-9_-]{11})",
            r"youtube\.com/v/([a-zA-Z0-9_-]{11})",
            r"youtube\.com/watch\?.+&v=([a-zA-Z0-9_-]{11})"
        ]
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1)
        return ""

    async def execute(self, input_text: str, context: Dict[str, Any] = None) -> str:
        video_id = self._extract_video_id(input_text)
        if not video_id:
            return "Error: No valid YouTube URL detected in the query or document context."

        transcript_list = None
        errors_logged = []

        try:
            import youtube_transcript_api
            
            # Resolve the correct API reference
            api_module = youtube_transcript_api
            if hasattr(api_module, "YouTubeTranscriptApi"):
                api_class = getattr(api_module, "YouTubeTranscriptApi")
            else:
                api_class = api_module

            # Attempt 1: Standard 'get_transcript' static call
            if hasattr(api_class, "get_transcript"):
                try:
                    transcript_list = api_class.get_transcript(video_id, languages=['en', 'hi'])
                except Exception as e:
                    errors_logged.append(f"get_transcript failed: {str(e)}")

            # Attempt 2: Static 'fetch' call (matching your system's package attributes)
            if transcript_list is None and hasattr(api_class, "fetch"):
                try:
                    transcript_list = api_class.fetch(video_id)
                except Exception as e:
                    errors_logged.append(f"fetch (static) failed: {str(e)}")

            # Attempt 3: Instance 'fetch' call
            if transcript_list is None and hasattr(api_class, "fetch"):
                try:
                    instance = api_class()
                    transcript_list = instance.fetch(video_id)
                except Exception as e:
                    errors_logged.append(f"fetch (instance) failed: {str(e)}")

            # Handle execution failure across all modes
            if transcript_list is None:
                return (
                    f"Error: Failed to fetch transcript using all available methods (get_transcript, fetch).\n"
                    f"System errors encountered: {errors_logged}.\n"
                    "Please verify if subtitles/captions are enabled for this video."
                )

            # Robustly format the transcript depending on if it is a list of dicts, strings, or a raw string
            if isinstance(transcript_list, list):
                if len(transcript_list) > 0 and isinstance(transcript_list[0], dict) and 'text' in transcript_list[0]:
                    raw_transcript = " ".join([entry['text'] for entry in transcript_list])
                else:
                    raw_transcript = " ".join([str(entry) for entry in transcript_list])
            else:
                raw_transcript = str(transcript_list)

        except Exception as e:
            return f"Error executing YouTube transcript module: {str(e)}"

        # Tool Chaining
        normalized_input = input_text.lower()
        if "summar" in normalized_input or "bullet" in normalized_input:
            from app.tools.registry import registry
            summarize_tool = registry.get_tool("summarization")
            if summarize_tool:
                return await summarize_tool.execute(raw_transcript, context=context)

        return f"--- YouTube Transcript (Video ID: {video_id}) ---\n{raw_transcript}"