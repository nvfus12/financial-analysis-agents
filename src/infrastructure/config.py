import os
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

class Config:
    """Application configuration loader."""
    
    # API Keys
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    LLAMA_CLOUD_API_KEY = os.getenv("LLAMA_CLOUD_API_KEY", "")
    
    # Base workspace directory (root of the project)
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    # Paths for persistence (relative to workspace root by default)
    DATABASE_URL = os.getenv("DATABASE_URL", "data/finanalyst.db")
    CHROMA_DB_PATH = os.getenv("CHROMA_DB_PATH", "data/chroma_store")
    PDF_UPLOAD_DIR = os.getenv("PDF_UPLOAD_DIR", "data/pdf_uploads")
    
    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    
    # Model Configurations
    LLM_MODEL_NAME_FLASH = os.getenv("LLM_MODEL_NAME_FLASH", "gemini-2.0-flash")
    LLM_MODEL_NAME_PRO = os.getenv("LLM_MODEL_NAME_PRO", "gemini-2.5-pro")
    LLM_MODEL_NAME_EMBEDDING = os.getenv("LLM_MODEL_NAME_EMBEDDING", "models/gemini-embedding-2")
    
    @classmethod
    def get_db_path(cls) -> str:
        """Returns the absolute path to the SQLite database file, ensuring parent dirs exist."""
        path = cls.DATABASE_URL if os.path.isabs(cls.DATABASE_URL) else os.path.join(cls.BASE_DIR, cls.DATABASE_URL)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        return path

    @classmethod
    def get_chroma_path(cls) -> str:
        """Returns the absolute path to the ChromaDB directory, ensuring it exists."""
        path = cls.CHROMA_DB_PATH if os.path.isabs(cls.CHROMA_DB_PATH) else os.path.join(cls.BASE_DIR, cls.CHROMA_DB_PATH)
        os.makedirs(path, exist_ok=True)
        return path

    @classmethod
    def get_upload_dir(cls) -> str:
        """Returns the absolute path to the PDF uploads directory, ensuring it exists."""
        path = cls.PDF_UPLOAD_DIR if os.path.isabs(cls.PDF_UPLOAD_DIR) else os.path.join(cls.BASE_DIR, cls.PDF_UPLOAD_DIR)
        os.makedirs(path, exist_ok=True)
        return path
