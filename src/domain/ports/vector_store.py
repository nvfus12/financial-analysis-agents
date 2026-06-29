from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class VectorStore(ABC):
    """Port interface for interacting with the vector database."""

    @abstractmethod
    def index_documents(self, collection_name: str, documents: List[Dict[str, Any]]) -> None:
        """
        Splits and indices a list of document chunks.
        Each document in the list should be a dictionary containing 'id', 'text', and 'metadata'.
        """
        pass

    @abstractmethod
    def query(
        self, 
        collection_name: str, 
        query_text: str, 
        limit: int = 3, 
        metadata_filter: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Queries the vector store collection for semantically similar chunks.
        Returns a list of dictionaries, each containing 'text', 'score', and 'metadata'.
        """
        pass

    @abstractmethod
    def delete_collection(self, collection_name: str) -> None:
        """Deletes the specified collection from the vector database."""
        pass
