import logging
from datetime import datetime, timedelta
from typing import Dict, Any
import pandas as pd
from src.domain.ports.stock_provider import StockDataProvider

logger = logging.getLogger(__name__)

class VnStockAdapter(StockDataProvider):
    """
    Adapter implementing the StockDataProvider interface using the new vnstock.api package.
    Fuses VCI and KBS brokers as data sources to maximize data completeness.
    """

    def get_historical_prices(self, ticker: str, days: int) -> pd.DataFrame:
        ticker = ticker.upper()
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        start_str = start_date.strftime("%Y-%m-%d")
        end_str = end_date.strftime("%Y-%m-%d")
        
        try:
            logger.info(f"Fetching historical prices for {ticker} from VCI (range: {start_str} to {end_str})...")
            from vnstock.api.quote import Quote
            
            q = Quote(symbol=ticker, source="vci")
            df = q.history(start=start_str, end=end_str)
            
            if df is None or df.empty:
                logger.warning(f"No price data returned for {ticker}. Returning empty DataFrame.")
                return pd.DataFrame(columns=["open", "high", "low", "close", "volume"])
                
            # vnstock columns: ['time', 'open', 'high', 'low', 'close', 'volume']
            # Format to match interface
            df["time"] = pd.to_datetime(df["time"])
            df.set_index("time", inplace=True)
            
            # Select and rename core columns if needed
            core_cols = ["open", "high", "low", "close", "volume"]
            df = df[core_cols]
            
            # Convert values to float
            for col in ["open", "high", "low", "close"]:
                df[col] = df[col].astype(float)
            df["volume"] = df["volume"].astype(float)
            
            return df
        except Exception as e:
            logger.error(f"Error fetching prices for {ticker} via vnstock: {e}")
            # Return empty DataFrame as fallback
            return pd.DataFrame(columns=["open", "high", "low", "close", "volume"])

    def get_financial_ratios(self, ticker: str) -> Dict[str, Any]:
        ticker = ticker.upper()
        try:
            logger.info(f"Fetching financial ratios for {ticker} from KBS...")
            from vnstock.api.financial import Finance
            
            f = Finance(symbol=ticker, source="kbs", period="quarter")
            df = f.ratio()
            
            if df is None or df.empty:
                logger.warning(f"No financial ratios returned for {ticker}.")
                return {}
                
            # Find the most recent quarter column (first column after 'item' and 'item_id')
            metadata_cols = ["item", "item_id", "item_en"]
            available_cols = df.columns.tolist()
            quarter_cols = [c for c in available_cols if c not in metadata_cols]
            
            if not quarter_cols:
                logger.warning(f"No quarter columns found in financial ratios for {ticker}.")
                return {}
                
            # Usually the first quarter column is the most recent (e.g. '2026-Q1', '2025-Q4')
            # Let's sort them to verify or take the first one
            latest_quarter = quarter_cols[0]
            logger.info(f"Extracting FPT ratios for quarter: {latest_quarter}")
            
            # Map Vietnamese ratio items to standard keys
            # Using partial matching to handle slight string changes
            ratios = {
                "pe": None,
                "pb": None,
                "roe": None,
                "roa": None,
                "eps": None,
                "gross_margin": None,
                "net_margin": None,
                "debt_to_equity": None
            }
            
            mapping = {
                "pe": "Chỉ số giá thị trường trên thu nhập (P/E)",
                "pb": "Chỉ số giá thị trường trên giá trị sổ sách (P/B)",
                "roe": "ROE bình quân 4 quý gần nhất",
                "roa": "ROA bình quân 4 quý gần nhất",
                "eps": "Thu nhập trên mỗi cổ phần của 4 quý gần nhất (EPS)",
                "gross_margin": "Tỷ suất lợi nhuận gộp biên",
                "net_margin": "Tỷ suất sinh lợi trên doanh thu thuần",
                "debt_to_equity": "Tỷ số Nợ trên Vốn chủ sở hữu"
            }
            
            for key, vi_name in mapping.items():
                row = df[df["item"].str.contains(vi_name, case=False, na=False, regex=False)]
                if not row.empty:
                    val = row.iloc[0][latest_quarter]
                    try:
                        # Clean up value and convert to float
                        if val is not None and str(val).strip() not in ["", "-", "None"]:
                            # Remove '%' if present, clean whitespace
                            val_str = str(val).replace("%", "").strip()
                            # Handle localized Vietnamese commas for decimals
                            val_str = val_str.replace(",", ".")
                            ratios[key] = float(val_str)
                    except ValueError:
                        logger.warning(f"Could not convert ratio value '{val}' for {key} to float.")
            
            return ratios
        except Exception as e:
            logger.error(f"Error fetching financial ratios for {ticker} via vnstock: {e}")
            return {}

    def get_company_profile(self, ticker: str) -> Dict[str, Any]:
        ticker = ticker.upper()
        try:
            logger.info(f"Fetching company profile for {ticker} from KBS...")
            from vnstock.api.company import Company
            
            c = Company(symbol=ticker, source="kbs")
            df = c.overview()
            
            if df is None or df.empty:
                logger.warning(f"No company overview returned for {ticker}.")
                return {}
                
            row = df.iloc[0]
            
            # Map to standard profile dict
            profile = {
                "ticker": ticker,
                "name": row.get("symbol", ticker),
                "industry": row.get("company_type", "Chưa xác định"),
                "description": row.get("business_model", "Không có mô tả."),
                "capital_size": float(row.get("charter_capital", 0.0)) / 1e9  # Convert to Billions if in raw units
            }
            return profile
        except Exception as e:
            logger.error(f"Error fetching company profile for {ticker} via vnstock: {e}")
            return {
                "ticker": ticker,
                "name": ticker,
                "industry": "Chưa xác định",
                "description": "Không có mô tả.",
                "capital_size": 0.0
            }
