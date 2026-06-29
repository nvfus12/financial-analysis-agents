import os
import random
import logging
from typing import List, Dict, Any, Optional
import chromadb
import google.generativeai as genai
from src.domain.ports.vector_store import VectorStore
from src.infrastructure.config import Config

logger = logging.getLogger(__name__)

class ChromaDBAdapter(VectorStore):
    """
    Adapter implementing the VectorStore interface using ChromaDB and Gemini Embedding API.
    Supports load balancing across multiple Gemini API keys and automatic fallback to 9router
    (or vice versa) for embedding generation if any key fails.
    """

    def __init__(self):
        self.client = chromadb.PersistentClient(path=Config.get_chroma_path())

    def _execute_with_retry(self, operation_fn):
        """
        Executes an embedding operation with load balancing and automatic fallback:
        - If primary is native Gemini: shuffles and shunts requests across gemini keys. If all fail, falls back to 9router.
        - If primary is 9router: tries 9router first. If it fails, falls back to native gemini keys list.
        """
        primary = os.getenv("PRIMARY_PROVIDER", "gemini").lower()
        
        # Load multiple Gemini keys
        gemini_keys_str = os.getenv("GEMINI_API_KEYS", "").strip()
        if not gemini_keys_str:
            gemini_keys_str = os.getenv("GEMINI_API_KEY", "").strip()
        gemini_keys = [k.strip() for k in gemini_keys_str.split(",") if k.strip()]
        
        nine_router_key = os.getenv("NINE_ROUTER_API_KEY", "").strip()
        nine_router_base = os.getenv("NINE_ROUTER_API_BASE", "https://api.9router.com/v1").strip()

        # Build list of providers to try in order
        providers_queue = []
        if primary == "9router":
            if nine_router_key:
                providers_queue.append(("9router", nine_router_key, nine_router_base))
            if gemini_keys:
                shuffled_keys = list(gemini_keys)
                random.shuffle(shuffled_keys)
                for key in shuffled_keys:
                    providers_queue.append(("gemini", key, ""))
        else: # Default: native gemini
            if gemini_keys:
                shuffled_keys = list(gemini_keys)
                random.shuffle(shuffled_keys)
                for key in shuffled_keys:
                    providers_queue.append(("gemini", key, ""))
            if nine_router_key:
                providers_queue.append(("9router", nine_router_key, nine_router_base))

        if not providers_queue:
            raise ValueError("No API credentials configured. Please set Google Gemini keys or 9router key in settings.")

        last_exception = None
        for idx, (provider_type, key, base_url) in enumerate(providers_queue):
            try:
                if provider_type == "gemini":
                    logger.info(f"Attempting native Gemini embedding using key: ...{key[-4:]} (index {idx+1}/{len(providers_queue)})")
                    genai.configure(api_key=key)
                    return operation_fn(use_openai=False, client=None)
                else: # 9router
                    logger.info(f"Attempting 9router embedding using base: {base_url} (index {idx+1}/{len(providers_queue)})")
                    from openai import OpenAI
                    client = OpenAI(api_key=key, base_url=base_url)
                    return operation_fn(use_openai=True, client=client)
            except Exception as e:
                logger.warning(f"Embedding Provider {provider_type} (index {idx+1}) failed with error: {e}. Trying next fallback...")
                last_exception = e
                continue
                
        logger.error("All configured embedding API keys and fallback providers failed.")
        raise last_exception

    def _get_embedding(self, text: str, is_query: bool = False) -> List[float]:
        """Calls Gemini Embedding API or custom proxy for a single text."""
        def run(use_openai, client):
            if use_openai:
                model = os.getenv("EMBEDDING_MODEL_NAME_OVERRIDE", "").strip()
                if not model:
                    model = Config.LLM_MODEL_NAME_EMBEDDING
                
                res = client.embeddings.create(
                    model=model,
                    input=text
                )
                return res.data[0].embedding
            else:
                task_type = "retrieval_query" if is_query else "retrieval_document"
                # Remove 'models/' prefix if using genai.embed_content which automatically handles it
                native_model = Config.LLM_MODEL_NAME_EMBEDDING
                res = genai.embed_content(
                    model=native_model,
                    content=text,
                    task_type=task_type
                )
                return res["embedding"]

        return self._execute_with_retry(run)

    def _get_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Calls Gemini Embedding API or custom proxy for a batch of texts."""
        def run(use_openai, client):
            if use_openai:
                model = os.getenv("EMBEDDING_MODEL_NAME_OVERRIDE", "").strip()
                if not model:
                    model = Config.LLM_MODEL_NAME_EMBEDDING
                    
                res = client.embeddings.create(
                    model=model,
                    input=texts
                )
                return [d.embedding for d in res.data]
            else:
                native_model = Config.LLM_MODEL_NAME_EMBEDDING
                res = genai.embed_content(
                    model=native_model,
                    content=texts,
                    task_type="retrieval_document"
                )
                return res["embedding"]

        return self._execute_with_retry(run)

    def index_documents(self, collection_name: str, documents: List[Dict[str, Any]]) -> None:
        """
        Indices document chunks in ChromaDB.
        Each document dict should contain 'id', 'text', and 'metadata'.
        """
        if not documents:
            return

        try:
            collection = self.client.get_or_create_collection(name=collection_name)
            
            ids = [doc["id"] for doc in documents]
            texts = [doc["text"] for doc in documents]
            metadatas = [doc.get("metadata", {}) for doc in documents]
            
            # Embed all texts in a batch
            embeddings = self._get_embeddings_batch(texts)
            
            collection.add(
                ids=ids,
                documents=texts,
                embeddings=embeddings,
                metadatas=metadatas
            )
            logger.info(f"Indexed {len(documents)} chunks in ChromaDB collection '{collection_name}'.")
        except Exception as e:
            logger.error(f"ChromaDB indexing failed for collection '{collection_name}': {e}")
            raise e

    def query(
        self, 
        collection_name: str, 
        query_text: str, 
        limit: int = 3, 
        metadata_filter: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Queries ChromaDB for semantically similar documents.
        """
        try:
            # Check if collection exists
            try:
                collection = self.client.get_collection(name=collection_name)
            except Exception:
                logger.warning(f"ChromaDB collection '{collection_name}' does not exist.")
                return []
                
            # Embed the query
            query_embedding = self._get_embedding(query_text, is_query=True)
            
            # Map filter format for ChromaDB (where_document, where, etc.)
            where_filter = metadata_filter if metadata_filter else None
            
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=limit,
                where=where_filter
            )
            
            # Format outputs
            formatted = []
            if results and results["documents"]:
                docs = results["documents"][0]
                ids = results["ids"][0]
                metadatas = results["metadatas"][0]
                distances = results["distances"][0] if "distances" in results else [0.0] * len(docs)
                
                for i in range(len(docs)):
                    formatted.append({
                        "id": ids[i],
                        "text": docs[i],
                        "score": round(1.0 - distances[i], 4), # Convert distance to similarity score
                        "metadata": metadatas[i]
                    })
            return formatted
        except Exception as e:
            logger.error(f"ChromaDB query failed for collection '{collection_name}': {e}")
            return []

    def delete_collection(self, collection_name: str) -> None:
        try:
            self.client.delete_collection(name=collection_name)
            logger.info(f"Deleted ChromaDB collection '{collection_name}'.")
        except Exception as e:
            logger.warning(f"Failed to delete collection '{collection_name}': {e}")
