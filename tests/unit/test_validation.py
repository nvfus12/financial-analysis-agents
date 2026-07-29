import os
import pytest
import pypdf
from src.domain.services.validation_service import ValidationService

def test_validate_ticker_valid():
    """Test valid stock tickers pass validation."""
    valid_tickers = [("FPT", "VN"), ("AAPL", "US")]
    for symbol, market in valid_tickers:
        is_valid, msg = ValidationService.validate_ticker(symbol, market)
        assert is_valid is True
        assert msg == "Valid"

def test_validate_ticker_invalid():
    """Test invalid stock tickers fail validation format check."""
    invalid_tickers = ["", "   ", "TOOLONG123", "F@T", "HPG;DROP", "AB"]
    for symbol in invalid_tickers:
        is_valid, msg = ValidationService.validate_ticker(symbol)
        assert is_valid is False
        assert "không hợp lệ" in msg or "không được để trống" in msg

def test_validate_fake_ticker_existence():
    """Test fake non-existent ticker KKKKK is rejected by ValidationService."""
    is_valid, msg = ValidationService.validate_ticker("KKKKK", "VN")
    assert is_valid is False
    assert "không tồn tại" in msg

def test_validate_pdf_nonexistent():
    """Test non-existent PDF file path returns validation error."""
    is_valid, msg = ValidationService.validate_pdf("data/uploads/non_existent_file.pdf")
    assert is_valid is False
    assert "không tồn tại" in msg

def test_validate_pdf_invalid_magic_bytes(tmp_path):
    """Test fake PDF file with invalid magic bytes (e.g. txt file renamed to pdf)."""
    fake_pdf = tmp_path / "fake_report.pdf"
    fake_pdf.write_bytes(b"This is not a real PDF file content")
    
    is_valid, msg = ValidationService.validate_pdf(str(fake_pdf))
    assert is_valid is False
    assert "Magic Bytes" in msg

def test_validate_pdf_valid_magic_bytes(tmp_path):
    """Test real PDF structure created via pypdf passes validation."""
    real_pdf = tmp_path / "valid_report.pdf"
    writer = pypdf.PdfWriter()
    writer.add_blank_page(width=200, height=200)
    with open(real_pdf, "wb") as f:
        writer.write(f)
    
    is_valid, msg = ValidationService.validate_pdf(str(real_pdf))
    assert is_valid is True
    assert msg == "Valid"
