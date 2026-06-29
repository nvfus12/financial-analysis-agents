import os
import logging
from typing import List, Dict, Any
from src.domain.ports.pdf_parser import PDFParser
from src.infrastructure.config import Config

logger = logging.getLogger(__name__)

class LlamaParseAdapter(PDFParser):
    """
    Adapter implementing the PDFParser interface.
    Uses LlamaParse cloud service for high-fidelity table extraction when API key is set.
    Falls back to local pypdf extraction if key is missing or on API error.
    """

    def __init__(self):
        self.api_key = Config.LLAMA_CLOUD_API_KEY
        if not self.api_key:
            logger.warning("LLAMA_CLOUD_API_KEY is not set in Config. LlamaParseAdapter will fall back to local pypdf.")

    def parse_pdf(self, file_path: str) -> List[Dict[str, Any]]:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"PDF file not found at: {file_path}")

        # If API key is available, attempt cloud-based LlamaParse
        if self.api_key:
            try:
                logger.info(f"Sending {file_path} to LlamaParse API...")
                from llama_parse import LlamaParse
                
                parser = LlamaParse(
                    api_key=self.api_key,
                    result_type="markdown",
                    verbose=False,
                    language="vi" # Vietnamese language support
                )
                
                # load_data returns LlamaIndex Document objects
                documents = parser.load_data(file_path)
                
                chunks = []
                for idx, doc in enumerate(documents):
                    chunks.append({
                        "text": doc.text,
                        "metadata": {
                            "page_number": doc.metadata.get("page_number", idx + 1),
                            "parser_type": "llamaparse",
                            "source_file": os.path.basename(file_path)
                        }
                    })
                return chunks
            except Exception as e:
                logger.error(f"LlamaParse cloud API failed: {e}. Falling back to local pypdf.")

        # Fallback: Local offline pypdf parser
        return self._local_parse(file_path)

    def _local_parse(self, file_path: str) -> List[Dict[str, Any]]:
        """Parses the PDF offline page-by-page using the standard pypdf library."""
        logger.info(f"Extracting text locally from {file_path} using pypdf...")
        try:
            import pypdf
            reader = pypdf.PdfReader(file_path)
            
            chunks = []
            for page_idx, page in enumerate(reader.pages):
                text = page.extract_text() or ""
                chunks.append({
                    "text": text,
                    "metadata": {
                        "page_number": page_idx + 1,
                        "parser_type": "pypdf_fallback",
                        "source_file": os.path.basename(file_path)
                    }
                })
            return chunks
        except ImportError:
            logger.error("pypdf library is not installed. Cannot run fallback parsing.")
            return []
        except Exception as e:
            logger.error(f"Local pypdf parsing failed: {e}")
            return []
