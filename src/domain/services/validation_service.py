import re
import os
import logging
import pypdf
import yfinance as yf
from typing import Tuple

logger = logging.getLogger(__name__)

# List of common financial keywords in Vietnamese and English for domain relevance scan
FINANCIAL_KEYWORDS = [
    "báo cáo tài chính", "bảng cân đối kế toán", "báo cáo kết quả hoạt động kinh doanh",
    "báo cáo lưu chuyển tiền tệ", "thuyết minh báo cáo tài chính", "doanh thu",
    "lợi nhuận", "tài sản", "nợ phải trả", "vốn chủ sở hữu", "cổ phiếu",
    "financial statements", "balance sheet", "income statement", "cash flows",
    "revenue", "net income", "annual report", "assets", "liabilities"
]

class ValidationService:
    """
    Service responsible for pre-flight validation of stock tickers and uploaded PDF documents
    before invoking LLM APIs or vector storage operations.
    """

    @staticmethod
    def validate_ticker(ticker: str, market: str = "VN") -> Tuple[bool, str]:
        """
        Validates stock ticker format, regex, and active existence on financial exchanges.
        Returns (is_valid, error_message).
        """
        if not ticker or not isinstance(ticker, str):
            return False, "❌ Mã cổ phiếu không được để trống."

        cleaned_ticker = ticker.strip().upper()

        # 1. Format Regex Check (3 to 5 alphanumeric characters, no spaces or special chars)
        if not re.match(r"^[A-Z0-9]{3,5}$", cleaned_ticker):
            return False, f"❌ Mã cổ phiếu '{cleaned_ticker}' không hợp lệ (Phải từ 3 đến 5 ký tự chữ hoặc số, không chứa ký tự đặc biệt)."

        # 2. Real Market Existence Check via yfinance
        try:
            symbols_to_try = [cleaned_ticker]
            if market.upper() == "VN":
                symbols_to_try = [f"{cleaned_ticker}.VN", cleaned_ticker]

            found_data = False
            for sym in symbols_to_try:
                t = yf.Ticker(sym)
                hist = t.history(period="5d")
                if hist is not None and not hist.empty:
                    found_data = True
                    break

            if not found_data:
                market_name = "Việt Nam (VNINDEX)" if market.upper() == "VN" else "Mỹ (NASDAQ/NYSE)"
                return False, f"❌ Mã cổ phiếu '{cleaned_ticker}' không tồn tại hoặc không có dữ liệu giao dịch trên thị trường {market_name}."

        except Exception as e:
            logger.warning(f"Ticker existence check error for {cleaned_ticker}: {e}")
            # If network error occurs during yfinance check, fallback to regex pass

        return True, "Valid"

    @staticmethod
    def validate_pdf(pdf_path: str, max_mb: int = 30) -> Tuple[bool, str]:
        """
        Validates uploaded PDF document for file existence, magic bytes, max size, encryption,
        corruption, and financial domain relevance.
        Returns (is_valid, error_message).
        """
        if not pdf_path or not os.path.exists(pdf_path):
            return False, "❌ Tệp PDF không tồn tại trên hệ thống."

        # 1. Magic Bytes Check (File Signature)
        try:
            with open(pdf_path, "rb") as f:
                header = f.read(5)
                if header != b"%PDF-":
                    return False, "❌ Tệp tải lên không phải là định dạng PDF hợp lệ (Sai định dạng Magic Bytes)."
        except Exception as e:
            return False, f"❌ Không thể đọc tệp PDF: {str(e)}"

        # 2. File Size Limit Check
        size_mb = os.path.getsize(pdf_path) / (1024 * 1024)
        if size_mb > max_mb:
            return False, f"❌ Dung lượng tệp PDF ({size_mb:.1f} MB) vượt quá giới hạn cho phép ({max_mb} MB)."

        # 3. Password Protection & Corrupt Structure Check
        try:
            reader = pypdf.PdfReader(pdf_path)
            if reader.is_encrypted:
                return False, "❌ Tệp PDF đã bị khóa bằng mật khẩu. Vui lòng mở khóa tệp trước khi tải lên."
            
            num_pages = len(reader.pages)
            if num_pages == 0:
                return False, "❌ Tệp PDF rỗng (không có trang nào)."

            # 4. Domain Relevance Keyword Density Check (Scans first 3 pages)
            try:
                extracted_text = ""
                pages_to_scan = min(num_pages, 3)
                for i in range(pages_to_scan):
                    text = reader.pages[i].extract_text()
                    if text:
                        extracted_text += text.lower() + " "

                if extracted_text.strip():
                    has_financial_keyword = any(kw in extracted_text for kw in FINANCIAL_KEYWORDS)
                    if not has_financial_keyword:
                        return False, "❌ Tệp PDF không liên quan đến Báo cáo tài chính hoặc thông tin tài chính doanh nghiệp."
            except Exception as scan_err:
                logger.warning(f"Text extraction scan warning for {pdf_path}: {scan_err}")

        except Exception as e:
            logger.error(f"PDF validation error for {pdf_path}: {e}")
            return False, f"❌ Tệp PDF bị hỏng hoặc cấu trúc không hợp lệ: {str(e)}"

        return True, "Valid"
