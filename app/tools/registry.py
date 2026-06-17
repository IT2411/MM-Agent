from typing import Dict, List
from app.tools.base import BaseTool

class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}

    def register(self, tool: BaseTool):
        self._tools[tool.name] = tool

    def get_tool(self, name: str) -> BaseTool:
        return self._tools.get(name)

    def list_tools(self) -> List[BaseTool]:
        return list(self._tools.values())

# Create a single global registry
registry = ToolRegistry()

def initialize_default_tools():
    """
    Imports and registers core tools on module load.
    Deferred imports are used to avoid circular import issues.
    """
    from app.tools.text_tools import (
        ConversationalTool, 
        SummarizeTool, 
        SentimentTool, 
        CodeExplainTool,
        YouTubeTranscriptTool
    )
    
    registry.register(ConversationalTool())
    registry.register(SummarizeTool())
    registry.register(SentimentTool())
    registry.register(CodeExplainTool())
    registry.register(YouTubeTranscriptTool())

# Initialize the default tools automatically
initialize_default_tools()