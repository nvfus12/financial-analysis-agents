import os
import sys
import logging

# Ensure root dir is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("verify_adapters")

def test_vnstock():
    logger.info("=== Testing VnStockAdapter ===")
    from src.infrastructure.adapters.vnstock_adapter import VnStockAdapter
    adapter = VnStockAdapter()
    
    # Test price bars
    df = adapter.get_historical_prices("FPT", days=10)
    logger.info(f"Price data (shape: {df.shape}):")
    print(df.head())
    
    # Test ratios
    ratios = adapter.get_financial_ratios("FPT")
    logger.info("Financial ratios:")
    print(ratios)
    
    # Test profile
    profile = adapter.get_company_profile("FPT")
    logger.info("Company profile:")
    print(profile)

def test_scraper():
    logger.info("=== Testing CafeFScraper ===")
    from src.infrastructure.adapters.cafef_scraper import CafeFScraper
    scraper = CafeFScraper()
    news = scraper.fetch_latest_news("FPT", limit=3)
    logger.info(f"Scraped {len(news)} news articles:")
    for idx, art in enumerate(news):
        print(f"{idx+1}. {art['title']} ({art['source']})")

def test_sentiment():
    logger.info("=== Testing FinBERTAdapter ===")
    from src.infrastructure.adapters.finbert_adapter import FinBERTAdapter
    analyzer = FinBERTAdapter()
    texts = [
        "Lợi nhuận quý 2 của FPT tăng trưởng vượt bậc 25% nhờ mảng công nghệ nước ngoài.",
        "Áp lực bán tháo cổ phiếu đè nặng lên thị trường chứng khoán cuối phiên."
    ]
    scores = analyzer.analyze_sentiment(texts)
    logger.info("Sentiment scores:")
    for t, s in zip(texts, scores):
        print(f"Text: '{t}' -> Sentiment: {s}")

def test_gemini():
    logger.info("=== Testing GeminiAdapter ===")
    from src.infrastructure.config import Config
    if not Config.GEMINI_API_KEY:
        logger.warning("GEMINI_API_KEY is not configured in .env. Skipping Gemini test.")
        return
        
    from src.infrastructure.adapters.gemini_adapter import GeminiAdapter
    adapter = GeminiAdapter()
    res = adapter.generate_text(
        system_instruction="You are a financial analyst helper. Answer in one short sentence.",
        prompt="Explain what a P/E ratio is."
    )
    logger.info("Gemini response:")
    print(res)

def main():
    logger.info("Starting adapters verification...")
    test_vnstock()
    test_scraper()
    test_sentiment()
    test_gemini()
    logger.info("Verification complete.")

if __name__ == "__main__":
    main()
