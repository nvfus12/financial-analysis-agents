from abc import ABC, abstractmethod
from typing import List, Dict, Any, Generator

class LLMProvider(ABC):
    """Port interface for interaction with Large Language Models (e.g. Gemini)."""

    @abstractmethod
    def generate_text(self, system_instruction: str, prompt: str, temperature: float = 0.2) -> str:
        """
        Generates a standard text completion response from the model.
        """
        pass

    @abstractmethod
    def generate_stream(self, system_instruction: str, prompt: str, temperature: float = 0.2) -> Generator[str, None, None]:
        """
        Generates a streaming text completion response from the model, yielding text chunks.
        """
        pass
