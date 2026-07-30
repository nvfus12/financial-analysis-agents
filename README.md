# FinAnalyst AI - Multi-Agent Stock Research System

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![Framework](https://img.shields.io/badge/Framework-FastAPI%20%7C%20LangGraph-green.svg)](https://fastapi.tiangolo.com/)
[![LLM Engine](https://img.shields.io/badge/LLM-Gemini%203.1%20Flash-purple.svg)](https://ai.google.dev/)
[![License](https://img.shields.io/badge/license-MIT-orange.svg)](LICENSE)

FinAnalyst AI is a financial analysis application built with **FastAPI**, **LangGraph**, and **Gemini 3.1 Flash**. It uses a multi-agent structure to gather stock data, analyze technical indicators, evaluate news sentiment, and generate investment analysis reports (`BUY`, `SELL`, `HOLD`).

---

## Features & Functionality

### 1. Pre-flight Input Validation (`ValidationService`)
- **Stock Ticker Validation**: Validates ticker format (3–5 characters) and verifies exchange listing on Vietnamese (VNINDEX) or US (NASDAQ/NYSE) markets via Yahoo Finance before graph execution.
- **PDF Financial Report Checking**:
  - Checks PDF file header (`%PDF-`).
  - Restricts file size (`<= 30MB`).
  - Checks for file corruption or password protection.
  - Scans for relevant financial terms (*Balance Sheet, Income Statement, Revenue, Assets, Liabilities...*).

### 2. Multi-Agent System (LangGraph)
- **Router Node**: Directs execution flow based on selected analysis mode (`full`, `fundamental`, `technical`).
- **Fundamental Analyst Agent**: Collects financial ratios (P/E, P/B, ROE, D/E) and extracts text from uploaded PDF reports.
- **Technical Analyst Agent**: Calculates moving averages (MA20, MA50), RSI (14), MACD, and extracts price history for charting.
- **Market Sentiment Agent**: Scrapes financial news articles (CafeF, Vietstock, Google News) and computes sentiment scores (-1.0 to 1.0).
- **CIO Synthesis Agent**: Combines outputs from specialized agents into a unified final report.
- **Smart Auditor Node (Reflection Loop)**: Evaluates report completeness and triggers revisions if necessary (up to 2 iterations).

### 3. Web Interface (HTML5 / CSS3 / Vanilla JS)
- Slate dark mode layout.
- Client-side tab navigation without full page reloads.
- Plotly.js candlestick price chart.
- Language selection for UI and report output (Vietnamese / English).

### 4. SQLite Storage & Caching
- Caches price histories and sentiment data to reduce duplicate API requests.
- Stores historical analysis reports in a local database.

---

## System Architecture

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
  ┌──────────────────┤     LangGraph Orchestrator   │
  │                  └──────┬───────┬───────┬───────┘
  │                         │       │       │
  │    ┌────────────────────┘       │       └────────────────────┐
  │    ▼                            ▼                            ▼
  │ ┌──────────────┐            ┌──────────────┐            ┌──────────────┐
  │ │ Fundamental  │            │  Technical   │            │  Sentiment   │
  │ │   Analyst    │            │   Analyst    │            │   Analyst    │
  │ └──────┬───────┘            └──────┬───────┘            └──────┬───────┘
  │        │                            │                            │
  │        └────────────────────┐       │       ┌────────────────────┘
  │                             ▼       ▼       ▼
  │                      ┌──────────────────────────────┐
  │                      │     CIO Synthesis Agent      │
  │                      └──────────────┬───────────────┘
  │                                     │ Review Draft
  │                      ┌──────────────▼───────────────┐
  └──────────────────────┤     Smart Auditor Critic     │ (Revision Loop on Failure)
                         └──────────────┬───────────────┘
                                        │ Approved Report (Passed Audit)
                         ┌──────────────▼───────────────┐
                         │   SQLite History & Cache     │
                         └──────────────────────────────┘
```

---

## Project Structure

```
financial-analysis-agents/
├── data/                       # Local database cache and PDF uploads
├── src/
│   ├── agents/                 # LangGraph nodes and state graph
│   │   ├── nodes/              # fundamental, technical, sentiment, synthesis, critic
│   │   ├── graph.py            # LangGraph workflow definition
│   │   └── prompts.py          # System prompts
│   ├── api/                    # FastAPI REST API Backend
│   │   ├── routes/             # analysis.py, history.py
│   │   ├── main.py             # FastAPI entry point
│   │   └── schemas.py          # Pydantic schemas
│   ├── domain/                 # Domain logic and state models
│   │   ├── models/             # AgentState schema
│   │   └── services/           # validation_service.py, financial_calc.py
│   └── infrastructure/         # External tools and databases
│       ├── adapters/           # yfinance, vnstock, gemini, scraper
│       └── database/           # SQLite connection, cache_repo, migrations
├── static/                     # Web Frontend
│   ├── index.html              # HTML structure
│   ├── style.css               # CSS styling
│   └── app.js                  # Frontend REST API client
├── tests/                      # Unit test suite
│   └── unit/
├── .gitignore
├── pytest.ini
├── requirements.txt
└── README.md
```

---

## Setup & Running

### 1. Requirements
- Python 3.10+

```bash
# Clone repository
git clone https://github.com/nvfus12/financial-analysis-agents.git
cd financial-analysis-agents

# Create virtual environment
python -m venv venv

# Activate environment (Windows)
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Environment Variables
Create a `.env` file in the root directory:

```env
GEMINI_API_KEY=your_gemini_api_key_here
LLM_MODEL_NAME_FLASH=gemini-1.5-flash
```

### 3. Start Application
Run the server:

```bash
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
```

- Web Interface: [http://localhost:8000](http://localhost:8000)
- API Docs (Swagger): [http://localhost:8000/docs](http://localhost:8000/docs)

---

## Automated Tests

Run pytest to execute the test suite:

```bash
python -m pytest tests/
```

---

## License

MIT License.
