from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseTool(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        """Unique identifier for the tool."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Detailed description of what the tool does and when to use it."""
        pass

    @abstractmethod
    async def execute(self, input_text: str, context: Dict[str, Any] = None) -> str:
        """Execute the tool's main logic."""
        pass