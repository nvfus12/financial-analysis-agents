import os
import uuid
import logging
import streamlit as st
import pandas as pd
from datetime import datetime

# Import project modules
from src.infrastructure.config import Config
from src.infrastructure.database.migrations import run_migrations
from src.infrastructure.database.cache_repo import (
    get_analysis_history,
    get_analysis_report_by_id,
    get_cached_stock_data,
    delete_analysis_report
)
from src.agents.graph import build_graph
from src.ui.charts import create_financial_chart

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("streamlit_app")

# Page Configuration
st.set_page_config(
    page_title="FinAnalyst Multi-Agent System",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize Database Migrations on Startup
run_migrations()

# Ensure Uploads Directory exists
os.makedirs("data/uploads", exist_ok=True)

# ------------------------------------------------------------------------------
# Premium CSS Styling (Dark Mode Slate & Glassmorphism)
# ------------------------------------------------------------------------------
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap');
    
    /* Main Background & Fonts */
    .stApp {
        background-color: #0b0f19;
        color: #f1f5f9;
        font-family: 'Outfit', sans-serif;
    }
    
    /* Custom Sidebar Header */
    .sidebar-header {
        font-size: 1.5rem;
        font-weight: 700;
        background: linear-gradient(135deg, #3b82f6 0%, #10b981 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 1.5rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    /* Glassmorphic Cards */
    .glass-card {
        background: rgba(30, 41, 59, 0.45);
        backdrop-filter: blur(16px);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
    }
    
    /* Glowing Recommendation Badges */
    .badge-buy {
        display: inline-block;
        padding: 0.4rem 1.2rem;
        font-size: 1rem;
        font-weight: 700;
        color: #10b981;
        background: rgba(16, 185, 129, 0.1);
        border: 1px solid #10b981;
        border-radius: 20px;
        box-shadow: 0 0 12px rgba(16, 185, 129, 0.2);
        margin-bottom: 1rem;
    }
    .badge-sell {
        display: inline-block;
        padding: 0.4rem 1.2rem;
        font-size: 1rem;
        font-weight: 700;
        color: #ef4444;
        background: rgba(239, 68, 68, 0.1);
        border: 1px solid #ef4444;
        border-radius: 20px;
        box-shadow: 0 0 12px rgba(239, 68, 68, 0.2);
        margin-bottom: 1rem;
    }
    .badge-hold {
        display: inline-block;
        padding: 0.4rem 1.2rem;
        font-size: 1rem;
        font-weight: 700;
        color: #f59e0b;
        background: rgba(245, 158, 11, 0.1);
        border: 1px solid #f59e0b;
        border-radius: 20px;
        box-shadow: 0 0 12px rgba(245, 158, 11, 0.2);
        margin-bottom: 1rem;
    }
    
    /* Streamlit overrides */
    div[data-testid="stExpander"] {
        background: rgba(30, 41, 59, 0.2);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 8px;
    }
    
    [data-testid="stSidebar"] {
        background-color: #0f172a !important;
        border-right: 1px solid rgba(255, 255, 255, 0.05) !important;
    }
    
    h1, h2, h3 {
        font-family: 'Outfit', sans-serif !important;
        font-weight: 600 !important;
    }
    
    /* White-label branding (Hide Streamlit default header/footer) */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {background: transparent !important;} /* Make header transparent so sidebar toggle works */
    
    /* Style sidebar buttons as Gemini-style text links */
    [data-testid="stSidebar"] button {
        background-color: transparent !important;
        border: none !important;
        color: #e2e8f0 !important;
        text-align: left !important;
        justify-content: flex-start !important;
        font-size: 0.92rem !important;
        font-weight: 500 !important;
        padding: 0.5rem 0.8rem !important;
        margin: 0.2rem 0 !important;
        width: 100% !important;
        border-radius: 8px !important;
        transition: all 0.2s ease !important;
        display: flex !important;
        align-items: center !important;
        box-shadow: none !important;
    }
    
    [data-testid="stSidebar"] button:hover {
        background-color: rgba(255, 255, 255, 0.08) !important;
        color: #ffffff !important;
    }
    
    [data-testid="stSidebar"] button:active {
        background-color: rgba(255, 255, 255, 0.12) !important;
    }
    
    /* Target the second column (the trash can button) for red hover styling and centering */
    [data-testid="stSidebar"] [data-testid="stHorizontalBlock"] div + div button,
    [data-testid="stSidebar"] [data-testid="column"] ~ [data-testid="column"] button,
    [data-testid="stSidebar"] [data-testid="column"]:nth-of-type(2) button,
    [data-testid="stSidebar"] .element-container:nth-child(2) button {
        justify-content: center !important;
        text-align: center !important;
        padding: 0.5rem 0 !important;
    }
    
    [data-testid="stSidebar"] [data-testid="stHorizontalBlock"] div + div button:hover,
    [data-testid="stSidebar"] [data-testid="column"] ~ [data-testid="column"] button:hover,
    [data-testid="stSidebar"] [data-testid="column"]:nth-of-type(2) button:hover {
        color: #ef4444 !important;
        background-color: rgba(239, 68, 68, 0.15) !important;
    }
    
    /* Vertically align the sidebar columns to the center */
    [data-testid="stSidebar"] [data-testid="stHorizontalBlock"],
    [data-testid="stSidebar"] [data-testid="column"] {
        align-items: center !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# ------------------------------------------------------------------------------
# Translation Dictionary & Localization Helper
# ------------------------------------------------------------------------------
TRANSLATIONS = {
    "vi": {
        "title": "🤖 Hệ thống Nghiên cứu Tài chính & Phân tích Cổ phiếu Multi-Agent",
        "subtitle": "Hệ thống đại lý LangGraph phân cấp điều phối phân tích cơ bản, kỹ thuật và cảm xúc thị trường để đưa ra khuyến nghị đầu tư.",
        "kpi_total_reports": "TỔNG SỐ BÁO CÁO ĐÃ CHẠY",
        "kpi_last_ticker": "MÃ CỔ PHIẾU GẦN NHẤT",
        "kpi_last_rec": "KHUYẾN NGHỊ GẦN NHẤT",
        "kpi_last_date": "NGÀY PHÂN TÍCH GẦN NHẤT",
        "recent_reports": "GẦN ĐÂY",
        "market_label": "Thị trường",
        "market_help": "Chọn sàn giao dịch chứng khoán (Việt Nam hoặc Mỹ).",
        "ticker_label": "Mã Cổ phiếu",
        "ticker_help": "Ví dụ: FPT, HPG (Việt Nam) hoặc AAPL, TSLA, NVDA (Mỹ)",
        "mode_label": "Chế độ Phân tích",
        "mode_help": "'full' chạy tất cả các agent, 'fundamental' chạy tỷ số + PDF RAG, 'technical' đánh giá xu hướng kỹ thuật.",
        "pdf_label": "Tải lên Báo cáo tài chính (PDF)",
        "pdf_help": "Yêu cầu cho chế độ RAG phân tích cơ bản.",
        "run_btn": "🚀 Chạy Phân tích Multi-Agent",
        "tab_synthesis": "📋 Báo cáo Tổng hợp (CIO)",
        "tab_analysts": "🕵️ Báo cáo Chi tiết",
        "tab_charts": "📈 Biểu đồ Kỹ thuật",
        "tab_logs": "⚙️ Nhật ký thực thi",
        "trace_header": "🔍 Nhật ký thực thi Agent",
        "no_report_msg": "Chưa có báo cáo nào được tạo. Điền mã cổ phiếu và bấm nút chạy ở trên hoặc chọn báo cáo cũ trong lịch sử.",
        "no_history_msg": "Chưa có báo cáo nào được lưu.",
        "loading_report_toast": "Đã tải báo cáo của {ticker} thành công!",
        "success_msg": "✅ Phân tích hoàn tất thành công!",
        "fail_msg": "❌ Phân tích thất bại",
        "toast_upload_pdf": "Tải báo cáo PDF thành công. Đang chuẩn bị Vector DB...",
        "settings_header": "⚙️ Cấu hình hệ thống",
        "ui_lang_label": "Ngôn ngữ giao diện (UI)",
        "report_lang_label": "Ngôn ngữ báo cáo (Report)",
        "exp_fundamental": "🔍 Báo cáo của Agent Phân tích Cơ bản",
        "exp_technical": "📉 Báo cáo của Agent Phân tích Kỹ thuật",
        "exp_sentiment": "📰 Báo cáo của Agent Tin tức & Cảm xúc",
        "chart_title": "Biểu đồ lịch sử giá & Chỉ báo kỹ thuật",
        "chart_warn": "Biểu đồ giá không khả dụng. Vui lòng chạy phân tích kỹ thuật để tải dữ liệu giá.",
        "spinner_msg": "Agent Orchestrator đang lập kế hoạch phân tích cho",
        "result_header": "Kết quả phân tích cho",
        "history_loaded_trace": "Đã tải báo cáo đã lưu từ {created_at}",
        "error_no_ticker": "❌ Vui lòng nhập mã cổ phiếu hợp lệ (ví dụ: FPT hoặc AAPL).",
        "error_no_gemini": "❌ Khóa API Google Gemini bị thiếu! Vui lòng cấu hình trong tệp .env của bạn.",
        "error_no_9router": "❌ Khóa API 9router bị thiếu! Vui lòng cấu hình trong tệp .env của bạn."
    },
    "en": {
        "title": "🤖 Multi-Agent Financial Research & Stock Analysis System",
        "subtitle": "A hierarchical LangGraph agent workspace coordinating fundamental, technical, and market sentiment analysis to generate investment recommendations.",
        "kpi_total_reports": "TOTAL REPORTS RUN",
        "kpi_last_ticker": "LAST TICKER ANALYZED",
        "kpi_last_rec": "LAST RECOMMENDATION",
        "kpi_last_date": "LAST ANALYSIS DATE",
        "recent_reports": "RECENT REPORTS",
        "market_label": "Market",
        "market_help": "Select the stock exchange market (Vietnam or United States).",
        "ticker_label": "Stock Ticker Symbol",
        "ticker_help": "E.g. FPT, HPG (Vietnam) or AAPL, TSLA, NVDA (United States)",
        "mode_label": "Analysis Mode",
        "mode_help": "'full' schedules all agents, 'fundamental' runs ratios + PDF RAG, 'technical' evaluates price indicators.",
        "pdf_label": "Upload Financial Report (PDF)",
        "pdf_help": "Required for PDF RAG semantic analysis under fundamental mode.",
        "run_btn": "🚀 Run Multi-Agent Analysis",
        "tab_synthesis": "📋 CIO Synthesis Memo",
        "tab_analysts": "🕵️ Specialist Deep-Dives",
        "tab_charts": "📈 Technical Charting",
        "tab_logs": "⚙️ Agent Execution Log",
        "trace_header": "🔍 Agent Conversation Trace Logs",
        "no_report_msg": "No reports generated yet. Enter stock ticker and click run above, or select a previous report from history.",
        "no_history_msg": "No saved reports found in history.",
        "loading_report_toast": "Loaded report for {ticker} successfully!",
        "success_msg": "✅ Analysis completed successfully!",
        "fail_msg": "❌ Analysis failed",
        "toast_upload_pdf": "PDF report uploaded successfully. Preparing vectors...",
        "settings_header": "⚙️ System Settings",
        "ui_lang_label": "UI Language",
        "report_lang_label": "Report Language",
        "exp_fundamental": "🔍 Fundamental Analyst Report",
        "exp_technical": "📉 Technical Analyst Report",
        "exp_sentiment": "📰 Market News & Sentiment Report",
        "chart_title": "Price History & Technical Overlays",
        "chart_warn": "Price history chart unavailable. Run a technical analysis query to load price data.",
        "spinner_msg": "Agent Orchestrator planning analysis for",
        "result_header": "Analysis Result for",
        "history_loaded_trace": "Loaded saved analysis from {created_at}",
        "error_no_ticker": "❌ Please specify a valid stock symbol (e.g. FPT).",
        "error_no_gemini": "❌ Google Gemini API Key is missing! Please configure it in your .env file.",
        "error_no_9router": "❌ 9router API Key is missing! Please configure it in your .env file."
    }
}

def t(key):
    lang = st.session_state.get("ui_lang", "vi")
    return TRANSLATIONS[lang].get(key, key)

# ------------------------------------------------------------------------------
# Session State Initialization
# ------------------------------------------------------------------------------
if "ui_lang" not in st.session_state:
    st.session_state.ui_lang = "en"
if "report_lang" not in st.session_state:
    st.session_state.report_lang = "en"
if "current_report" not in st.session_state:
    st.session_state.current_report = None
if "current_report_id" not in st.session_state:
    st.session_state.current_report_id = None
if "current_ticker" not in st.session_state:
    st.session_state.current_ticker = None
if "current_market" not in st.session_state:
    st.session_state.current_market = "VN"
if "current_rec" not in st.session_state:
    st.session_state.current_rec = None
if "sub_insights" not in st.session_state:
    st.session_state.sub_insights = {
        "fundamental": "",
        "technical": "",
        "sentiment": ""
    }
if "trace_logs" not in st.session_state:
    st.session_state.trace_logs = []

# ------------------------------------------------------------------------------
# Sidebar Configuration & Historical Reports Panel
# ------------------------------------------------------------------------------
with st.sidebar:
    st.markdown('<div class="sidebar-header">📈 FinAnalyst Agent</div>', unsafe_allow_html=True)
    st.markdown("---")
    
    # Language Selectors Section
    st.markdown('<div style="font-size: 0.85rem; color: #64748b; font-weight: 600; margin-bottom: 0.5rem; letter-spacing: 0.5px;">LANGUAGE SETTINGS</div>', unsafe_allow_html=True)
    ui_lang_choice = st.selectbox(
        t("ui_lang_label"),
        options=["Tiếng Việt", "English"],
        index=0 if st.session_state.ui_lang == "vi" else 1
    )
    st.session_state.ui_lang = "vi" if ui_lang_choice == "Tiếng Việt" else "en"
    
    report_lang_choice = st.selectbox(
        t("report_lang_label"),
        options=["Tiếng Việt", "English"],
        index=0 if st.session_state.report_lang == "vi" else 1
    )
    st.session_state.report_lang = "vi" if report_lang_choice == "Tiếng Việt" else "en"
    
    st.markdown("---")
    
    # Recent Reports History Links
    recent_label = t("recent_reports")
    st.markdown(f'<div style="font-size: 0.85rem; color: #64748b; font-weight: 600; margin-bottom: 0.8rem; letter-spacing: 0.5px;">{recent_label}</div>', unsafe_allow_html=True)
    
    # Fetch previous analysis runs from DB
    history_items = get_analysis_history(limit=10)
    
    if history_items:
        for item in history_items:
            report_word = "Báo cáo" if st.session_state.ui_lang == "vi" else "Report"
            btn_label = f"💬 {report_word} {item['ticker']} ({item['recommendation']})"
            
            col_link, col_del = st.columns([5, 1])
            with col_link:
                # Clicking the button loads the report
                if st.button(btn_label, key=f"hist_{item['id']}", use_container_width=True):
                    full_record = get_analysis_report_by_id(item["id"])
                    if full_record:
                        st.session_state.current_report = full_record["report_markdown"]
                        st.session_state.current_report_id = full_record["id"]
                        st.session_state.current_ticker = full_record["ticker"]
                        st.session_state.current_market = full_record.get("market", "VN")
                        st.session_state.current_rec = full_record["recommendation"]
                        st.session_state.sub_insights = {
                            "fundamental": "Historical run details embedded in Synthesis report tab." if st.session_state.ui_lang == "en" else "Chi tiết lịch sử được đính kèm ở tab Báo cáo Tổng hợp.",
                            "technical": "Historical run details embedded in Synthesis report tab." if st.session_state.ui_lang == "en" else "Chi tiết lịch sử được đính kèm ở tab Báo cáo Tổng hợp.",
                            "sentiment": "Historical run details embedded in Synthesis report tab." if st.session_state.ui_lang == "en" else "Chi tiết lịch sử được đính kèm ở tab Báo cáo Tổng hợp."
                        }
                        st.session_state.trace_logs = [t("history_loaded_trace").format(created_at=full_record['created_at'])]
                        st.toast(t("loading_report_toast").format(ticker=full_record['ticker']))
                        st.rerun()
            with col_del:
                # Deleting the report directly from the sidebar row
                if st.button("🗑️", key=f"del_{item['id']}", use_container_width=True, help="Xóa báo cáo này" if st.session_state.ui_lang == "vi" else "Delete this report"):
                    success = delete_analysis_report(item["id"])
                    if success:
                        st.toast("🗑️ " + ("Xóa báo cáo thành công!" if st.session_state.ui_lang == "vi" else "Report deleted successfully!"))
                        if st.session_state.get("current_report_id") == item["id"]:
                            st.session_state.current_report = None
                            st.session_state.current_ticker = None
                            st.session_state.current_market = "VN"
                            st.session_state.current_rec = None
                            st.session_state.current_report_id = None
                            st.session_state.trace_logs = []
                            st.session_state.sub_insights = {
                                "fundamental": "",
                                "technical": "",
                                "sentiment": ""
                            }
                        st.rerun()
    else:
        st.info(t("no_history_msg"))

# ------------------------------------------------------------------------------
# App Main Title Layout
# ------------------------------------------------------------------------------
st.markdown(f"## {t('title')}")
st.markdown(t('subtitle'))

# --- KPI Metric Cards Dashboard ---
history = get_analysis_history(limit=5)
total_runs = len(get_analysis_history(limit=1000))
last_ticker = history[0]["ticker"] if history else "N/A"
last_rec = history[0]["recommendation"] if history else "N/A"
last_date = history[0]["created_at"].split()[0] if history else "N/A"

rec_color = "#f59e0b"  # Default: HOLD
if last_rec == "BUY":
    rec_color = "#10b981"
elif last_rec == "SELL":
    rec_color = "#ef4444"

m_col1, m_col2, m_col3, m_col4 = st.columns(4)
with m_col1:
    st.markdown(
        f'<div class="glass-card" style="text-align: center; padding: 0.8rem; margin-bottom: 1.5rem;">'
        f'<div style="font-size: 0.8rem; color: #94a3b8; font-weight: 500; letter-spacing: 0.5px;">{t("kpi_total_reports")}</div>'
        f'<div style="font-size: 1.8rem; font-weight: 700; color: #3b82f6; margin-top: 0.2rem;">{total_runs}</div>'
        f'</div>',
        unsafe_allow_html=True
    )
with m_col2:
    st.markdown(
        f'<div class="glass-card" style="text-align: center; padding: 0.8rem; margin-bottom: 1.5rem;">'
        f'<div style="font-size: 0.8rem; color: #94a3b8; font-weight: 500; letter-spacing: 0.5px;">{t("kpi_last_ticker")}</div>'
        f'<div style="font-size: 1.8rem; font-weight: 700; color: #f1f5f9; margin-top: 0.2rem;">{last_ticker}</div>'
        f'</div>',
        unsafe_allow_html=True
    )
with m_col3:
    st.markdown(
        f'<div class="glass-card" style="text-align: center; padding: 0.8rem; margin-bottom: 1.5rem;">'
        f'<div style="font-size: 0.8rem; color: #94a3b8; font-weight: 500; letter-spacing: 0.5px;">{t("kpi_last_rec")}</div>'
        f'<div style="font-size: 1.8rem; font-weight: 700; color: {rec_color}; margin-top: 0.2rem;">{last_rec}</div>'
        f'</div>',
        unsafe_allow_html=True
    )
with m_col4:
    st.markdown(
        f'<div class="glass-card" style="text-align: center; padding: 0.8rem; margin-bottom: 1.5rem;">'
        f'<div style="font-size: 0.8rem; color: #94a3b8; font-weight: 500; letter-spacing: 0.5px;">{t("kpi_last_date")}</div>'
        f'<div style="font-size: 1.8rem; font-weight: 700; color: #10b981; margin-top: 0.2rem;">{last_date}</div>'
        f'</div>',
        unsafe_allow_html=True
    )

# Main Form Container (Input Controls)
with st.container():
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    col0, col1, col2, col3 = st.columns([1, 1, 1, 2])
    
    with col0:
        market_input = st.selectbox(
            t("market_label"),
            options=["VN", "US"],
            index=0,
            help=t("market_help")
        )
        
    with col1:
        ticker_input = st.text_input(
            t("ticker_label"),
            value="",
            max_chars=5,
            help=t("ticker_help")
        ).strip().upper()
        
    with col2:
        mode_input = st.selectbox(
            t("mode_label"),
            options=["full", "fundamental", "technical"],
            index=0,
            help=t("mode_help")
        )
        
    with col3:
        uploaded_pdf = st.file_uploader(
            t("pdf_label"),
            type=["pdf"],
            help=t("pdf_help")
        )
        
    run_clicked = st.button(
        t("run_btn"),
        use_container_width=True,
        type="primary"
    )
    st.markdown('</div>', unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# Run Logic ( LangGraph State Machine Execution )
# ------------------------------------------------------------------------------
if run_clicked:
    has_gemini = bool(os.getenv("GEMINI_API_KEYS", "").strip() or os.getenv("GEMINI_API_KEY", "").strip())
    has_9router = bool(os.getenv("NINE_ROUTER_API_KEY", "").strip())
    primary = os.getenv("PRIMARY_PROVIDER", "gemini")
    
    # Filter placeholder values
    if has_gemini and "your_gemini_api_key_here" in (os.getenv("GEMINI_API_KEYS", "") or os.getenv("GEMINI_API_KEY", "")):
        has_gemini = False
        
    is_valid_keys = False
    error_msg = ""
    if primary == "9router":
        if not has_9router:
            error_msg = t("error_no_9router")
        else:
            is_valid_keys = True
    else:
        if not has_gemini:
            error_msg = t("error_no_gemini")
        else:
            is_valid_keys = True
            
    if not is_valid_keys:
        st.error(error_msg)
    elif not ticker_input:
        st.error(t("error_no_ticker"))
    else:
        # Save uploaded PDF to file system if present
        pdf_temp_path = ""
        if uploaded_pdf is not None:
            pdf_temp_path = os.path.join("data/uploads", f"{ticker_input}_{uuid.uuid4().hex[:6]}.pdf")
            with open(pdf_temp_path, "wb") as f:
                f.write(uploaded_pdf.getbuffer())
            logger.info(f"Saved uploaded PDF to {pdf_temp_path}")
            st.toast(t("toast_upload_pdf"))
            
        # Run graph execution under loader spinner
        with st.spinner(f"{t('spinner_msg')} {ticker_input}..."):
            try:
                # Compile State Graph
                graph = build_graph()
                
                # Setup conversation session parameters
                config = {"configurable": {"thread_id": str(uuid.uuid4())}}
                initial_state = {
                    "ticker": ticker_input,
                    "market": market_input,
                    "analysis_mode": mode_input,
                    "pdf_path": pdf_temp_path,
                    "logs": [f"Session initialized at {datetime.now().strftime('%H:%M:%S')}."],
                    "raw_financials": {},
                    "technical_signals": {},
                    "scraped_news": [],
                    "report_language": st.session_state.report_lang
                }
                
                # Execute graph synchronously
                final_state = graph.invoke(initial_state, config=config)
                
                # Save results in session state
                st.session_state.current_report = final_state.get("final_report_markdown", "")
                st.session_state.current_ticker = final_state.get("ticker", ticker_input)
                st.session_state.current_market = final_state.get("market", market_input)
                st.session_state.current_rec = final_state.get("final_recommendation", "HOLD")
                
                # Dynamic fetch of the latest report ID from DB
                latest_runs = get_analysis_history(limit=1)
                if latest_runs:
                    st.session_state.current_report_id = latest_runs[0]["id"]
                st.session_state.sub_insights = {
                    "fundamental": final_state.get("fundamental_insights", "N/A"),
                    "technical": final_state.get("technical_insights", "N/A"),
                    "sentiment": final_state.get("sentiment_insights", "N/A")
                }
                st.session_state.trace_logs = final_state.get("logs", [])
                
                st.success(t("success_msg"))
                st.rerun() # Refresh to show in KPIs
                
            except Exception as e:
                st.error(f"{t('fail_msg')}: {e}")
                logger.exception("Graph execution crashed:")

# ------------------------------------------------------------------------------
# Main Dashboard Panel Renders
# ------------------------------------------------------------------------------
if st.session_state.current_report:
    rec = st.session_state.current_rec
    badge_class = "badge-hold"
    if rec == "BUY":
        badge_class = "badge-buy"
    elif rec == "SELL":
        badge_class = "badge-sell"

    st.markdown(
        f'<div class="glass-card">'
        f'<h3>{t("result_header")} {st.session_state.current_ticker}</h3>'
        f'<span class="{badge_class}">{rec}</span>'
        f'</div>',
        unsafe_allow_html=True
    )
    
    # 2. Main Dashboard Tabs
    tab_report, tab_analysts, tab_charts, tab_logs = st.tabs([
        t("tab_synthesis"),
        t("tab_analysts"),
        t("tab_charts"),
        t("tab_logs")
    ])
    
    # Tab 1: Synthesis markdown memo
    with tab_report:
        st.markdown(st.session_state.current_report)
        
    # Tab 2: Individual specialist collapse accordions
    with tab_analysts:
        with st.expander(t("exp_fundamental"), expanded=True):
            st.markdown(st.session_state.sub_insights["fundamental"])
            
        with st.expander(t("exp_technical"), expanded=True):
            st.markdown(st.session_state.sub_insights["technical"])
            
        with st.expander(t("exp_sentiment"), expanded=True):
            st.markdown(st.session_state.sub_insights["sentiment"])
            
    # Tab 3: Interactive Plotly Chart
    with tab_charts:
        st.subheader(t("chart_title"))
        # Load cached stock prices
        cached_prices = get_cached_stock_data(st.session_state.current_ticker, "prices")
        if cached_prices:
            # Reconstruct pandas DataFrame
            import json
            price_df = pd.read_json(json.dumps(cached_prices), orient="index")
            price_df.index = pd.to_datetime(price_df.index)
            price_df.sort_index(inplace=True)
            
            # Generate and draw chart
            plotly_fig = create_financial_chart(price_df, market=st.session_state.current_market)
            st.plotly_chart(plotly_fig, use_container_width=True)
        else:
            st.warning(t("chart_warn"))
            
    # Tab 4: Agent thought logs
    with tab_logs:
        st.subheader(t("trace_header"))
        for log in st.session_state.trace_logs:
            st.code(log, language="text")
            
else:
    # Initial landing screen placeholder card
    st.markdown(
        f"""
        <div class="glass-card" style="text-align: center; padding: 4rem 2rem;">
            <h2>📈 FinAnalyst Agent Dashboard</h2>
            <p style="color: #94a3b8; font-size: 1.1rem; max-width: 600px; margin: 1rem auto;">
                {t("no_report_msg")}
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )
