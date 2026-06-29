import logging
from typing import List, Dict, Any
from src.domain.ports.sentiment_analyzer import SentimentAnalyzer

logger = logging.getLogger(__name__)

class FinBERTAdapter(SentimentAnalyzer):
    """
    Adapter implementing the SentimentAnalyzer interface using ProsusAI/FinBERT.
    Falls back to a keyword-based lexicon and LLM-assisted sentiment analysis
    if Hugging Face or PyTorch is not fully set up.
    """

    def __init__(self):
        self.pipeline = None
        try:
            logger.info("Attempting to load FinBERT model pipeline...")
            from transformers import pipeline
            # This will download the model (~400MB) on first run and cache it locally
            self.pipeline = pipeline("sentiment-analysis", model="ProsusAI/finbert")
            logger.info("FinBERT model loaded successfully.")
        except Exception as e:
            logger.warning(f"Could not load FinBERT via transformers: {e}. Falling back to rule-based analysis.")

    def analyze_sentiment(self, texts: List[str]) -> List[Dict[str, Any]]:
        if not texts:
            return []

        results = []
        if self.pipeline:
            try:
                # Call Hugging Face pipeline
                outputs = self.pipeline(texts)
                for out in outputs:
                    label = out["label"].lower() # 'positive', 'negative', 'neutral'
                    conf = out["score"]
                    
                    # Map to numeric score between [-1.0, 1.0]
                    if label == "positive":
                        score = conf
                    elif label == "negative":
                        score = -conf
                    else:
                        score = 0.0
                        
                    results.append({
                        "label": label,
                        "score": round(score, 4)
                    })
                return results
            except Exception as e:
                logger.error(f"FinBERT pipeline execution failed: {e}. Falling back to rules.")

        # Fallback implementation
        return self._fallback_sentiment(texts)

    def _fallback_sentiment(self, texts: List[str]) -> List[Dict[str, Any]]:
        """A simple, robust keyword-based lexicon analyzer for Vietnamese financial text."""
        logger.debug("Running rule-based Vietnamese financial sentiment scorer.")
        pos_words = ["tăng", "bứt phá", "lợi nhuận", "vượt", "ấn tượng", "khả quan", "mua", "tích lũy", "đỉnh mới", "ngoại gom"]
        neg_words = ["giảm", "lỗ", "áp lực", "chốt lời", "điều chỉnh", "bán", "cạnh tranh", "sụt giảm", "rủi ro", "lo ngại"]
        
        results = []
        for text in texts:
            text_lower = text.lower()
            pos_count = sum(1 for w in pos_words if w in text_lower)
            neg_count = sum(1 for w in neg_words if w in text_lower)
            
            if pos_count > neg_count:
                label = "positive"
                # Basic confidence score based on word counts
                score = min(0.5 + 0.1 * (pos_count - neg_count), 0.9)
            elif neg_count > pos_count:
                label = "negative"
                score = -min(0.5 + 0.1 * (neg_count - pos_count), 0.9)
            else:
                label = "neutral"
                score = 0.0
                
            results.append({
                "label": label,
                "score": round(score, 2)
            })
        return results
