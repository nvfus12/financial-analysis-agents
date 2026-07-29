# FinAnalyst AI - Multi-Agent Stock Research System

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![Framework](https://img.shields.io/badge/Framework-FastAPI%20%7C%20LangGraph-green.svg)](https://fastapi.tiangolo.com/)
[![LLM Engine](https://img.shields.io/badge/LLM-Gemini%203.1%20Flash-purple.svg)](https://ai.google.dev/)
[![License](https://img.shields.io/badge/license-MIT-orange.svg)](LICENSE)

**FinAnalyst AI** là hệ thống trợ lý phân tích đầu tư và cổ phiếu thông minh đa đại lý (Multi-Agent System) được xây dựng trên nền tảng **FastAPI**, **LangGraph V2**, và mô hình ngôn ngữ thế hệ mới **Gemini 3.1 Flash**. Hệ thống phối hợp tự động giữa các Agent chuyên môn (Phân tích Cơ bản, Phân tích Kỹ thuật, Cảm xúc Thị trường) kết hợp bộ tự kiểm duyệt phản biện (Smart Reflection) để đưa ra báo cáo khuyến nghị đầu tư chuẩn xác.

---

## 🌟 Tính Năng Nổi Bật (Key Features)

### 1. 🛡️ Bộ Kiểm Soát Pre-flight Validation (`ValidationService`)
- **Xác thực Mã Cổ phiếu Real-time**: Kiểm tra định dạng Regex (`3-5` ký tự) và **xác thực sự tồn tại thực tế trên thị trường** chứng khoán Việt Nam (VNINDEX) hoặc Mỹ (NASDAQ/NYSE) qua Yahoo Finance trước khi gọi LLM.
- **Xác thực File BCTC (PDF)**:
  - Kiểm tra Magic Bytes (`%PDF-`) chống giả mạo định dạng.
  - Giới hạn dung lượng tệp (`<= 30MB`).
  - Phát hiện tệp bị đặt mật khẩu bảo vệ hoặc bị hỏng dữ liệu.
  - Quét mật độ từ khóa tài chính chuyên ngành (*Báo cáo tài chính, Balance sheet, Revenue, Doanh thu...*).

### 2. 🤖 Kiến Trúc Multi-Agent Phân Cấp (LangGraph V2)
- **Deterministic Control Node (Router)**: Điều phối luồng phân tích theo chế độ được yêu cầu (`full`, `fundamental`, `technical`).
- **Fundamental Analyst Agent**: Phân tích các chỉ số tài chính live (P/E, P/B, ROE, D/E...) kết hợp RAG trích xuất văn bản BCTC từ file PDF.
- **Technical Analyst Agent**: Tính toán các chỉ báo kỹ thuật (RSI-14, MACD, MA20, MA50) và mô hình giá.
- **Market Sentiment Agent**: Cào tin tức mới nhất từ các trang báo tài chính (CafeF, Vietstock) và chấm điểm cảm xúc thị trường (-1.0 đến 1.0).
- **CIO Synthesis Agent**: Tổng hợp báo cáo khuyến nghị đầu tư cuối cùng (`BUY`, `SELL`, `HOLD`).
- **Smart Auditor Node (Reflection Loop)**: Tự động phản biện chất lượng báo cáo. Nếu phát hiện sai sót hoặc thiếu căn cứ, Auditor yêu cầu Agent làm lại draft (tối đa 2 vòng phản biện).

### 3. 🖥️ Giao Diện Web Tách Biệt mượt mà (HTML5 + CSS3 + Vanilla JS)
- Giao diện **Slate Dark Mode Glassmorphism** hiện đại.
- **0ms Client-side Latency**: Chuyển đổi giữa các tab báo cáo tức thì không đơ mờ màn hình.
- **Biểu đồ Nến Nhật Tương tác (Plotly.js)**: Hiển thị 90 phiên giá liên tục không bị khoảng thưa cuối tuần.
- **Đa ngôn ngữ Linh hoạt**: Hỗ trợ chuyển đổi ngôn ngữ giao diện (UI) và ngôn ngữ báo cáo (Tiếng Việt 🇻🇳 / Tiếng Anh 🇺🇸).

### 4. 🗄️ Tầng Lưu Trữ & Bộ Nhớ Tạm (SQLite Cache)
- Cache dữ liệu giá và tin tức để tối ưu thời gian phản hồi và tiết kiệm Token API.
- Lưu trữ lịch sử tất cả các báo cáo phân tích phục vụ xem lại hoặc quản lý.

---

## 🏗️ Kiến Trúc Hệ Thống (System Architecture)

```
                     ┌──────────────────────────────┐
                     │    HTML5 / JS Web Client     │
                     └──────────────┬───────────────┘
                                    │ HTTP / REST API
                     ┌──────────────▼───────────────┐
                     │   FastAPI Engine (main.py)   │
                     └──────────────┬───────────────┘
                                    │ Pre-flight Check
                     ┌──────────────▼───────────────┐
                     │      ValidationService       │
                     └──────────────┬───────────────┘
                                    │ Verified Request
                     ┌──────────────▼───────────────┐
                     │     LangGraph Orchestrator   │
                     └──────┬───────┬───────┬───────┘
                            │       │       │
       ┌────────────────────┘       │       └────────────────────┐
       ▼                            ▼                            ▼
┌──────────────┐            ┌──────────────┐            ┌──────────────┐
│ Fundamental  │            │  Technical   │            │  Sentiment   │
│   Analyst    │            │   Analyst    │            │   Analyst    │
└──────┬───────┘            └──────┬───────┘            └──────┬───────┘
       │                            │                            │
       └────────────────────┐       │       ┌────────────────────┘
                            ▼       ▼       ▼
                     ┌──────────────────────────────┐
                     │     CIO Synthesis Agent      │
                     └──────────────┬───────────────┘
                                    │ Review Draft
                     ┌──────────────▼───────────────┐
                     │     Smart Auditor Critic     │
                     └──────────────┬───────────────┘
                                    │ Passed / Approved
                     ┌──────────────▼───────────────┐
                     │   SQLite History & Cache     │
                     └──────────────────────────────┘
```

---

## 🛠️ Cấu Trúc Thư Mục Dự Án (Project Structure)

```
financial-analysis-agents/
├── data/                       # Thư mục lưu cache.db và file PDF uploads
├── src/
│   ├── agents/                 # Các đại lý AI & LangGraph Graph
│   │   ├── nodes/              # fundamental, technical, sentiment, synthesis, critic
│   │   ├── graph.py            # LangGraph state workflow & reflection edges
│   │   └── prompts.py          # System instructions & prompts
│   ├── api/                    # Tầng REST API Backend (FastAPI)
│   │   ├── routes/             # analysis.py, history.py
│   │   ├── main.py             # FastAPI App & Static Mounting
│   │   └── schemas.py          # Pydantic Request/Response models
│   ├── domain/                 # Nghiệp vụ cốt lõi
│   │   ├── models/             # State schema
│   │   └── services/           # validation_service.py, financial_calc.py
│   └── infrastructure/         # Tầng giao tiếp hạ tầng
│       ├── adapters/           # yfinance, vnstock, gemini, scraper
│       └── database/           # SQLite connection, cache_repo, migrations
├── static/                     # Giao diện Web tĩnh Frontend
│   ├── index.html              # HTML5 Layout
│   ├── style.css               # Slate Dark Mode CSS
│   └── app.js                  # Vanilla JS REST Client
├── tests/                      # Unit tests (21 tests passed 100%)
│   └── unit/
├── .gitignore
├── pytest.ini
├── requirements.txt
└── README.md
```

---

## 🚀 Hướng Dẫn Cài Đặt & Khởi Chạy (Quick Start)

### 1. Chuẩn bị Môi trường
Yêu cầu **Python 3.10** trở lên.

```bash
# Clone repository
git clone https://github.com/your-username/financial-analysis-agents.git
cd financial-analysis-agents

# Tạo môi trường ảo venv
python -m venv venv

# Kích hoạt venv (Windows)
venv\Scripts\activate

# Cài đặt các thư viện phụ thuộc
pip install -r requirements.txt
```

### 2. Cấu hình Key API
Tạo file `.env` tại thư mục gốc của dự án và khai báo Google Gemini API Key:

```env
GEMINI_API_KEY=your_gemini_api_key_here
LLM_MODEL_NAME_FLASH=gemini-1.5-flash
```

### 3. Khởi chạy Ứng dụng Backend & Web Frontend
Chạy lệnh khởi tạo Uvicorn Server:

```bash
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
```

Sau khi máy chủ khởi chạy, truy cập giao diện Web trên trình duyệt tại địa chỉ:
👉 **[http://localhost:8000](http://localhost:8000)**

Tài liệu API Swagger UI có sẵn tại:
👉 **[http://localhost:8000/docs](http://localhost:8000/docs)**

---

## 🧪 Chạy Kiểm Thử Tự Động (Automated Testing)

Dự án được bảo vệ bởi bộ test tự động kiểm thử toàn bộ các chức năng Validation, API, Cache và Thuật toán:

```bash
python -m pytest tests/
```

Kịch bản kiểm thử bao gồm **21/21 Unit Tests passed 100%**.

---

## 📜 Giấy Phép (License)

Dự án được phân phối dưới giấy phép [MIT License](LICENSE).
