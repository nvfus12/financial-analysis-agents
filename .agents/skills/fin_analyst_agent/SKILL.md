---
name: fin_analyst_agent
description: Guidelines for building the financial analysis agent workflow (LangGraph, LlamaIndex, vnstock, FinBERT, SQLite, ChromaDB).
---

# Financial Analyst Agent Domain Guidelines

This skill guides the implementation of the core financial reasoning graph, the document RAG engine, API integration, and sentiment scoring models.

## 1. LangGraph State Management

- **Graph State Schema**:
  - Define a strict `AgentState` as a Python `TypedDict` containing input ticker, mode, sub-agent intermediate insights, and final synthesis fields.
  - Do not pollute the state with large raw payloads. Store parsed dataclasses or summarized JSON structures instead of raw objects.
- **Node Principles**:
  - Every Node function must accept the current `AgentState` and return a dictionary of fields to update.
  - Nodes must be side-effect free concerning other nodes (no node should depend on another node's private state; all coordination goes through the shared schema).
  - Add explicit debug logs using `logging` at the beginning and end of each node to trace graph state changes.

## 2. Table-Aware Financial RAG

- **Layout-Aware PDF Parsing**:
  - Use `LlamaParse` configured with Markdown output mode to extract text and preserve tables from financial reports.
  - Verify that parsed markdown files represent table structures using markdown headers and grid borders (e.g., `| Year | Revenue |`).
- **Semantic Vector Storage**:
  - Split parsed documents using markdown-header-aware splitters to avoid breaking financial tables into separate chunks.
  - Embed chunks using the Gemini Embedding API (`text-embedding-004`) and store them in ChromaDB.
  - Filter queries using chunk metadata (e.g., matching the specific ticker or document type).

## 3. Financial APIs & Caching

- **`vnstock` Integration**:
  - Always wrap calls to `vnstock` in a repository class (`VnStockAdapter`) that implements the `StockDataProvider` interface.
  - Wrap calls in a caching layer (using SQLite `stock_data_cache`) to avoid redundant API hits within the same day.
  - Add retry loops with exponential backoff (e.g., using the `tenacity` library) to handle network drops or rate-limit warnings from stock broker APIs.

## 4. News Sentiment Analysis

- **Web Scraping**:
  - Keep scrapers lightweight. Target CafeF or Vietstock using specific URL patterns and parse text inside article bodies.
  - Cache scraped articles in `news_cache` to save time and API costs.
- **FinBERT Sentiment scoring**:
  - Load the FinBERT model locally using Hugging Face pipeline (`transformers`).
  - Cache the model weights in a shared directory (`data/models/` or `~/.cache/huggingface`) to prevent redownloading.
  - Map categorical model labels to numerical scores:
    - `"positive"` → `1.0`
    - `"neutral"` → `0.0`
    - `"negative"` → `-1.0`
