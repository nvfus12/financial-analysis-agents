# FinAnalyst AI - Multi-Agent Stock Research System

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![Framework](https://img.shields.io/badge/Framework-FastAPI%20%7C%20LangGraph-green.svg)](https://fastapi.tiangolo.com/)
[![LLM Engine](https://img.shields.io/badge/LLM-Gemini%203.1%20Flash-purple.svg)](https://ai.google.dev/)
[![License](https://img.shields.io/badge/license-MIT-orange.svg)](LICENSE)

**FinAnalyst AI** is an intelligent, multi-agent financial research and stock analysis platform powered by **FastAPI**, **LangGraph V2**, and Google's **Gemini 3.1 Flash**. The system orchestrates specialized domain agents (Fundamental, Technical, and Market Sentiment) alongside an automated reflection auditor to deliver rigorous investment recommendations (`BUY`, `SELL`, `HOLD`).

---

## 🌟 Key Features

### 1. 🛡️ Pre-flight Validation Service (`ValidationService`)
- **Real-time Ticker Verification**: Performs format validation (regex `3-5` characters) and verifies active exchange listing on Vietnamese (VNINDEX) or US (NASDAQ/NYSE) markets via Yahoo Finance before making LLM calls.
- **PDF Financial Report Verification**:
  - Magic Bytes signature verification (`%PDF-`).
  - Strict file size limit enforcement (`<= 30MB`).
  - Detects password encryption and document corruption.
  - Scans first 3 pages for financial domain keyword relevance (*Balance Sheet, Income Statement, Revenue, Assets, Liabilities...*).

### 2. 🤖 Hierarchical Multi-Agent Architecture (LangGraph V2)
- **Deterministic Control Node (Router)**: Routes execution flows based on selected analysis mode (`full`, `fundamental`, `technical`).
- **Fundamental Analyst Agent**: Processes live financial ratios (P/E, P/B, ROE, D/E) and performs RAG context extraction on uploaded PDF reports.
- **Technical Analyst Agent**: Evaluates price history, moving averages (MA20, MA50), RSI (14), MACD crossovers, and exports 90-day price action series.
- **Market Sentiment Agent**: Scrapes financial news outlets (CafeF, Vietstock, Google News) and computes net sentiment scores (-1.0 to 1.0).
- **CIO Synthesis Agent**: Synthesizes all specialist insights into an executive investment memo.
- **Smart Auditor Node (Reflection Loop)**: Evaluates report quality and reasoning consistency. Triggers revisions if criteria are not met (up to 2 audit loops).

### 3. 🖥️ Modern Decoupled Web Interface (HTML5 / CSS3 / Vanilla JS)
- Premium **Slate Dark Mode Glassmorphism** design.
- **0ms Client-Side Latency**: Instant tab switching without page reloads or UI dimming.
- **Interactive Candlestick Charting (Plotly.js)**: Displays continuous 90-day price action without weekend gaps.
- **Localization Support**: Instant toggle between UI languages and report output languages (Vietnamese 🇻🇳 / English 🇺🇸).

### 4. 🗄️ SQLite Caching & History Persistence
- Caches raw stock price histories and sentiment scores to eliminate redundant API calls and optimize token usage.
- Persists historical analysis reports for review and management.

---

## 🏗️ System Architecture

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
                                    │ Approved Report
                     ┌──────────────▼───────────────┐
                     │   SQLite History & Cache     │
                     └──────────────────────────────┘
```

---

## 🛠️ Project Structure

```
financial-analysis-agents/
├── data/                       # Local cache database and PDF uploads
├── src/
│   ├── agents/                 # LangGraph nodes and execution graph
│   │   ├── nodes/              # fundamental, technical, sentiment, synthesis, critic
│   │   ├── graph.py            # LangGraph state workflow & reflection edges
│   │   └── prompts.py          # System instructions & templates
│   ├── api/                    # FastAPI REST API Backend
│   │   ├── routes/             # analysis.py, history.py
│   │   ├── main.py             # FastAPI App & Static Files Mount
│   │   └── schemas.py          # Pydantic Request/Response schemas
│   ├── domain/                 # Domain logic & models
│   │   ├── models/             # AgentState schema
│   │   └── services/           # validation_service.py, financial_calc.py
│   └── infrastructure/         # External integrations
│       ├── adapters/           # yfinance, vnstock, gemini, scraper
│       └── database/           # SQLite connection, cache_repo, migrations
├── static/                     # Web Frontend
│   ├── index.html              # HTML5 Layout
│   ├── style.css               # Slate Dark Mode CSS
│   └── app.js                  # Vanilla JS REST Client
├── tests/                      # Automated test suite (21 tests)
│   └── unit/
├── .gitignore
├── pytest.ini
├── requirements.txt
└── README.md
```

---

## 🚀 Quick Start Guide

### 1. Environment Setup
Requires **Python 3.10+**.

```bash
# Clone the repository
git clone https://github.com/nvfus12/financial-analysis-agents.git
cd financial-analysis-agents

# Create virtual environment
python -m venv venv

# Activate virtual environment (Windows)
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. API Key Configuration
Create a `.env` file in the project root directory and set your Google Gemini API Key:

```env
GEMINI_API_KEY=your_gemini_api_key_here
LLM_MODEL_NAME_FLASH=gemini-1.5-flash
```

### 3. Run the Backend & Web Server
Start the Uvicorn dev server:

```bash
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
```

Open your browser and navigate to:
👉 **[http://localhost:8000](http://localhost:8000)**

Interactive Swagger API documentation is available at:
👉 **[http://localhost:8000/docs](http://localhost:8000/docs)**

---

## 🧪 Automated Testing

Run the unit test suite to verify system integrity:

```bash
python -m pytest tests/
```

Test suite result: **21/21 Unit Tests Passed (100%)**.

---

## 📜 License

Distributed under the [MIT License](LICENSE).
