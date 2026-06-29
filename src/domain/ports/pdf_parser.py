from abc import ABC, abstractmethod
from typing import List, Dict, Any

class PDFParser(ABC):
    """Port interface for layout-aware PDF document parsing (e.g. using LlamaParse)."""

    @abstractmethod
    def parse_pdf(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Parses a PDF document into structured, markdown-formatted text blocks.
        Each chunk in the return list is a dictionary containing:
        - 'text': markdown string representation (preserving table layouts).
        - 'metadata': metadata dictionaries (e.g. page_number, block_type).
        """
        pass
