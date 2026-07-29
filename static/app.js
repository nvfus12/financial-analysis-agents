/**
 * FinAnalyst Vanilla JavaScript Async REST Client
 * Interacts with FastAPI Backend endpoints (/api/v1/analyze, /api/v1/history)
 * Supports UI Language Localization & Report Output Language Selection.
 */

const UI_TRANSLATIONS = {
    vi: {
        lblUiLang: "NGÔN NGỮ GIAO DIỆN",
        lblReportLang: "NGÔN NGỮ BÁO CÁO",
        lblHistory: "LỊCH SỬ PHÂN TÍCH",
        appTitle: "Phân Tích Cổ Phiếu Thông Minh Bằng AI",
        appSubtitle: "Trợ lý AI tự động tổng hợp số liệu tài chính, biểu đồ kỹ thuật và tin tức thị trường giúp bạn đưa ra quyết định đầu tư hiệu quả.",
        kpiTotalTitle: "TỔNG SỐ BÁO CÁO",
        kpiTickerTitle: "MÃ PHÂN TÍCH GẦN NHẤT",
        kpiRecTitle: "KHUYẾN NGHỊ GẦN NHẤT",
        kpiDateTitle: "NGÀY CHẠY GẦN NHẤT",
        lblMarket: '<i class="fa-solid fa-globe"></i> Thị trường',
        lblTicker: '<i class="fa-solid fa-dollar-sign"></i> Mã Cổ phiếu',
        lblMode: '<i class="fa-solid fa-sliders"></i> Chế độ Phân tích',
        lblPdf: '<i class="fa-solid fa-file-pdf"></i> Tải BCTC (PDF)',
        optVn: "Việt Nam (VNINDEX)",
        optUs: "Mỹ (NASDAQ / NYSE)",
        optModeFull: "Phân tích Toàn diện",
        optModeFund: "Phân tích Báo cáo Tài chính",
        optModeTech: "Phân tích Biểu đồ & Xu hướng",
        btnRun: '<i class="fa-solid fa-rocket"></i> Chạy Phân Tích',
        tabSynthesis: '<i class="fa-solid fa-file-contract"></i> Báo cáo Tổng hợp',
        tabDeepDive: '<i class="fa-solid fa-layer-group"></i> Phân tích Chi tiết',
        tabLogs: '<i class="fa-solid fa-clock-rotate-left"></i> Nhật ký Xử lý',
        hdrFund: '<i class="fa-solid fa-chart-pie"></i> Phân tích Tài chính & Báo cáo',
        hdrTech: '<i class="fa-solid fa-chart-line"></i> Phân tích Biểu đồ Kỹ thuật',
        hdrSent: '<i class="fa-solid fa-newspaper"></i> Phân tích Tin tức & Thị trường',
        hdrResultPrefix: "Kết quả phân tích cho "
    },
    en: {
        lblUiLang: "UI LANGUAGE",
        lblReportLang: "REPORT LANGUAGE",
        lblHistory: "ANALYSIS HISTORY",
        appTitle: "Smart AI Stock Research",
        appSubtitle: "AI-powered research assistant aggregating financial reports, technical indicators, and market news to guide your investment decisions.",
        kpiTotalTitle: "TOTAL REPORTS RUN",
        kpiTickerTitle: "LAST TICKER ANALYZED",
        kpiRecTitle: "LAST RECOMMENDATION",
        kpiDateTitle: "LAST ANALYSIS DATE",
        lblMarket: '<i class="fa-solid fa-globe"></i> Market',
        lblTicker: '<i class="fa-solid fa-dollar-sign"></i> Stock Ticker Symbol',
        lblMode: '<i class="fa-solid fa-sliders"></i> Analysis Mode',
        lblPdf: '<i class="fa-solid fa-file-pdf"></i> Upload Financial PDF',
        optVn: "Vietnam (VNINDEX)",
        optUs: "United States (NASDAQ / NYSE)",
        optModeFull: "Comprehensive Analysis",
        optModeFund: "Financial Reports Only",
        optModeTech: "Technical Trends Only",
        btnRun: '<i class="fa-solid fa-rocket"></i> Start Analysis',
        tabSynthesis: '<i class="fa-solid fa-file-contract"></i> Executive Summary',
        tabDeepDive: '<i class="fa-solid fa-layer-group"></i> Detailed Breakdown',
        tabLogs: '<i class="fa-solid fa-clock-rotate-left"></i> Processing Log',
        hdrFund: '<i class="fa-solid fa-chart-pie"></i> Financial Performance',
        hdrTech: '<i class="fa-solid fa-chart-line"></i> Technical Chart Analysis',
        hdrSent: '<i class="fa-solid fa-newspaper"></i> Market News & Sentiment',
        hdrResultPrefix: "Analysis Result for "
    }
};

function initApp() {
    // DOM Elements
    const uiLangSelect = document.getElementById("uiLangSelect");
    const reportLangSelect = document.getElementById("reportLangSelect");
    const analysisForm = document.getElementById("analysisForm");
    const btnSubmit = document.getElementById("btnSubmit");
    const alertBox = document.getElementById("alertBox");
    const loadingOverlay = document.getElementById("loadingOverlay");
    const resultsSection = document.getElementById("resultsSection");
    const historyList = document.getElementById("historyList");

    // KPI Elements
    const kpiTotal = document.getElementById("kpiTotal");
    const kpiLastTicker = document.getElementById("kpiLastTicker");
    const kpiLastRec = document.getElementById("kpiLastRec");
    const kpiLastDate = document.getElementById("kpiLastDate");

    // Output Elements
    const resultTicker = document.getElementById("resultTicker");
    const resultBadge = document.getElementById("resultBadge");
    const reportMarkdownContent = document.getElementById("reportMarkdownContent");
    const fundamentalInsight = document.getElementById("fundamentalInsight");
    const technicalInsight = document.getElementById("technicalInsight");
    const sentimentInsight = document.getElementById("sentimentInsight");
    const logsConsole = document.getElementById("logsConsole");

    // Tab Buttons & Content
    const tabBtns = document.querySelectorAll(".tab-btn");
    const tabContents = document.querySelectorAll(".tab-content");

    let currentUiLang = "vi";
    let activeReportId = null;
    let alertTimer = null;

    // Safe DOM helpers
    function safeSetText(id, text) {
        const el = document.getElementById(id);
        if (el) el.textContent = text;
    }

    function safeSetHtml(id, html) {
        const el = document.getElementById(id);
        if (el) el.innerHTML = html;
    }

    // --------------------------------------------------------------------------
    // 0. UI Language Switcher
    // --------------------------------------------------------------------------
    if (uiLangSelect) {
        uiLangSelect.addEventListener("change", (e) => {
            currentUiLang = e.target.value;
            applyUiLanguage(currentUiLang);
            loadHistory();
        });
    }

    function applyUiLanguage(lang) {
        const dict = UI_TRANSLATIONS[lang] || UI_TRANSLATIONS.vi;
        
        safeSetText("lblUiLang", dict.lblUiLang);
        safeSetText("lblReportLang", dict.lblReportLang);
        safeSetText("lblHistory", dict.lblHistory);
        
        const h1 = document.querySelector(".app-header h1");
        if (h1) h1.textContent = dict.appTitle;
        const sub = document.querySelector(".subtitle");
        if (sub) sub.textContent = dict.appSubtitle;
        
        const kpiTitles = document.querySelectorAll(".kpi-title");
        if (kpiTitles.length >= 4) {
            kpiTitles[0].textContent = dict.kpiTotalTitle;
            kpiTitles[1].textContent = dict.kpiTickerTitle;
            kpiTitles[2].textContent = dict.kpiRecTitle;
            kpiTitles[3].textContent = dict.kpiDateTitle;
        }

        safeSetHtml("lblMarket", dict.lblMarket);
        safeSetHtml("lblTicker", dict.lblTicker);
        safeSetHtml("lblMode", dict.lblMode);
        safeSetHtml("lblPdf", dict.lblPdf);

        safeSetText("optVn", dict.optVn);
        safeSetText("optUs", dict.optUs);

        safeSetText("optModeFull", dict.optModeFull);
        safeSetText("optModeFund", dict.optModeFund);
        safeSetText("optModeTech", dict.optModeTech);

        if (btnSubmit) btnSubmit.innerHTML = dict.btnRun;

        safeSetHtml("btnTabSynthesis", dict.tabSynthesis);
        safeSetHtml("btnTabDeepDive", dict.tabDeepDive);
        safeSetHtml("btnTabLogs", dict.tabLogs);

        safeSetHtml("hdrFund", dict.hdrFund);
        safeSetHtml("hdrTech", dict.hdrTech);
        safeSetHtml("hdrSent", dict.hdrSent);
        safeSetText("hdrResultPrefix", dict.hdrResultPrefix);
    }

    // Initialize UI language and load history on startup
    applyUiLanguage(currentUiLang);
    loadHistory();

    // --------------------------------------------------------------------------
    // 1. Tab Switching Logic
    // --------------------------------------------------------------------------
    if (tabBtns) {
        tabBtns.forEach(btn => {
            btn.addEventListener("click", () => {
                tabBtns.forEach(b => b.classList.remove("active"));
                tabContents.forEach(c => c.classList.add("hidden"));

                btn.classList.add("active");
                const targetTabId = btn.getAttribute("data-tab");
                const targetContent = document.getElementById(targetTabId);
                if (targetContent) {
                    targetContent.classList.remove("hidden");
                }
            });
        });
    }

    // --------------------------------------------------------------------------
    // 2. Analysis Form Submission & Button Click Handler
    // --------------------------------------------------------------------------
    async function handleFormSubmit(e) {
        if (e) e.preventDefault();
        hideAlert();

        const tickerInput = document.getElementById("tickerInput");
        const tickerVal = (tickerInput ? tickerInput.value : "").trim().toUpperCase();

        if (!tickerVal) {
            showAlert(currentUiLang === "vi" ? "❌ Vui lòng nhập mã cổ phiếu hợp lệ (VD: FPT, HPG)." : "❌ Please enter a valid stock ticker symbol.", "error");
            return;
        }

        showLoading(tickerVal);
        if (btnSubmit) btnSubmit.disabled = true;

        try {
            const formData = new FormData(analysisForm || document.getElementById("analysisForm"));
            if (reportLangSelect) {
                formData.append("report_language", reportLangSelect.value);
            }

            const res = await fetch("/api/v1/analyze", {
                method: "POST",
                body: formData
            });

            const data = await res.json();

            if (!res.ok) {
                const errorDetail = data.detail || `Lỗi HTTP ${res.status}`;
                showAlert(errorDetail, "error");
                hideLoading();
                if (btnSubmit) btnSubmit.disabled = false;
                return;
            }

            renderResults(data);
            showAlert(currentUiLang === "vi" ? "✅ Phân tích hoàn tất thành công!" : "✅ Analysis completed successfully!", "success");
            loadHistory();

        } catch (err) {
            console.error("Analysis Request Error:", err);
            showAlert(`❌ Không thể kết nối tới Server API Backend: ${err.message}`, "error");
        } finally {
            hideLoading();
            if (btnSubmit) btnSubmit.disabled = false;
        }
    }

    if (analysisForm) {
        analysisForm.addEventListener("submit", handleFormSubmit);
    }

    if (btnSubmit) {
        btnSubmit.addEventListener("click", (e) => {
            if (analysisForm) {
                // If form is valid, execute submit
                if (!analysisForm.checkValidity || analysisForm.checkValidity()) {
                    handleFormSubmit(e);
                }
            }
        });
    }

    // --------------------------------------------------------------------------
    // 3. Render Results & Plotly Chart
    // --------------------------------------------------------------------------
    function renderResults(data) {
        if (resultTicker) resultTicker.textContent = data.ticker || "N/A";
        
        if (resultBadge) {
            const rec = (data.final_recommendation || "HOLD").toUpperCase();
            resultBadge.textContent = rec;
            resultBadge.className = "rec-badge";
            if (rec === "BUY") resultBadge.classList.add("badge-buy");
            else if (rec === "SELL") resultBadge.classList.add("badge-sell");
            else resultBadge.classList.add("badge-hold");
        }

        if (reportMarkdownContent) {
            const markdownText = data.final_report_markdown || "# Không có báo cáo";
            reportMarkdownContent.innerHTML = typeof marked !== 'undefined' ? marked.parse(markdownText) : markdownText;
        }

        if (fundamentalInsight) fundamentalInsight.innerHTML = typeof marked !== 'undefined' ? marked.parse(data.fundamental_insights || "Không có thông tin.") : (data.fundamental_insights || "");
        if (technicalInsight) technicalInsight.innerHTML = typeof marked !== 'undefined' ? marked.parse(data.technical_insights || "Không có thông tin.") : (data.technical_insights || "");
        if (sentimentInsight) sentimentInsight.innerHTML = typeof marked !== 'undefined' ? marked.parse(data.sentiment_insights || "Không có thông tin.") : (data.sentiment_insights || "");

        if (logsConsole) {
            const logs = data.logs || [];
            logsConsole.textContent = logs.join("\n");
        }

        // Render Plotly Candlestick Chart
        const priceHistory = data.technical_signals ? data.technical_signals.price_history : null;
        renderPriceChart(data.ticker, priceHistory);

        if (resultsSection) {
            resultsSection.classList.remove("hidden");
            resultsSection.scrollIntoView({ behavior: "smooth" });
        }
    }

    function renderPriceChart(ticker, priceHistory) {
        const container = document.getElementById("chartContainer");
        const chartDiv = document.getElementById("stockPlotlyChart");
        if (!priceHistory || priceHistory.length === 0 || !chartDiv || typeof Plotly === 'undefined') {
            if (container) container.classList.add("hidden");
            return;
        }

        try {
            const dates = priceHistory.map(item => item.date);
            const closes = priceHistory.map(item => item.close);
            const opens = priceHistory.map(item => item.open);
            const highs = priceHistory.map(item => item.high);
            const lows = priceHistory.map(item => item.low);

            const traceCandlestick = {
                x: dates,
                open: opens,
                high: highs,
                low: lows,
                close: closes,
                type: 'candlestick',
                name: ticker,
                increasing: { line: { color: '#10b981' } },
                decreasing: { line: { color: '#ef4444' } }
            };

            const layout = {
                title: {
                    text: currentUiLang === "vi" ? `Biểu đồ nến Nhật xu hướng giá 90 ngày cho ${ticker}` : `90-Day Candlestick Chart for ${ticker}`,
                    font: { color: '#60a5fa', family: 'Be Vietnam Pro, sans-serif', size: 15 }
                },
                paper_bgcolor: 'rgba(15, 23, 42, 0.0)',
                plot_bgcolor: 'rgba(15, 23, 42, 0.0)',
                xaxis: {
                    type: 'category',
                    gridcolor: 'rgba(255, 255, 255, 0.06)',
                    tickfont: { color: '#94a3b8' },
                    rangeslider: { visible: false },
                    nticks: 10
                },
                yaxis: {
                    gridcolor: 'rgba(255, 255, 255, 0.06)',
                    tickfont: { color: '#94a3b8' }
                },
                margin: { l: 45, r: 25, t: 40, b: 35 }
            };

            Plotly.newPlot(chartDiv, [traceCandlestick], layout, { responsive: true, displayModeBar: false });
            if (container) container.classList.remove("hidden");
        } catch (err) {
            console.warn("Plotly render warning:", err);
            if (container) container.classList.add("hidden");
        }
    }

    // --------------------------------------------------------------------------
    // 4. Load History & Detail
    // --------------------------------------------------------------------------
    async function loadHistory() {
        try {
            const res = await fetch("/api/v1/history?limit=15");
            if (!res.ok) return;

            const items = await res.json();
            renderHistoryUI(items);
            updateKPIs(items);
        } catch (err) {
            console.warn("Failed to load history:", err);
        }
    }

    function renderHistoryUI(items) {
        if (!historyList) return;
        if (!items || items.length === 0) {
            historyList.innerHTML = `<div style="color: var(--text-muted); font-size: 0.85rem;">${currentUiLang === 'vi' ? 'Chưa có báo cáo nào.' : 'No saved reports.'}</div>`;
            return;
        }

        historyList.innerHTML = "";
        items.forEach(item => {
            const div = document.createElement("div");
            div.className = "history-item";
            div.innerHTML = `
                <span>💬 <strong>${item.ticker}</strong> (${item.recommendation})</span>
                <button class="btn-del-hist" data-id="${item.id}" title="Xóa báo cáo"><i class="fa-solid fa-trash"></i></button>
            `;

            div.addEventListener("click", async (e) => {
                if (e.target.closest(".btn-del-hist")) return;
                await loadHistoryDetail(item.id);
            });

            const delBtn = div.querySelector(".btn-del-hist");
            if (delBtn) {
                delBtn.addEventListener("click", async (e) => {
                    e.stopPropagation();
                    if (confirm(currentUiLang === "vi" ? `Bạn có chắc muốn xóa báo cáo ${item.ticker}?` : `Delete report for ${item.ticker}?`)) {
                        await deleteHistoryItem(item.id);
                    }
                });
            }

            historyList.appendChild(div);
        });
    }

    async function loadHistoryDetail(id) {
        if (currentUiLang === "vi") {
            showLoadingText("Đang tải báo cáo lịch sử...", "Vui lòng chờ trong giây lát");
        } else {
            showLoadingText("Loading historical report...", "Please wait a moment");
        }
        try {
            const res = await fetch(`/api/v1/history/${id}`);
            if (!res.ok) return;
            const data = await res.json();

            activeReportId = id;
            renderResults({
                ticker: data.ticker,
                final_recommendation: data.recommendation,
                final_report_markdown: data.report_markdown,
                fundamental_insights: currentUiLang === "vi" ? "Chi tiết được đính kèm ở tab Báo cáo Tổng hợp." : "Historical details embedded in Synthesis memo tab.",
                technical_insights: currentUiLang === "vi" ? "Chi tiết được đính kèm ở tab Báo cáo Tổng hợp." : "Historical details embedded in Synthesis memo tab.",
                sentiment_insights: currentUiLang === "vi" ? "Chi tiết được đính kèm ở tab Báo cáo Tổng hợp." : "Historical details embedded in Synthesis memo tab.",
                logs: [`Loaded report from SQLite DB at ${data.created_at}`]
            });
            showAlert(currentUiLang === "vi" ? `Đã tải báo cáo của ${data.ticker} thành công!` : `Loaded report for ${data.ticker}!`, "success");
        } catch (err) {
            showAlert("Không thể tải chi tiết báo cáo lịch sử.", "error");
        } finally {
            hideLoading();
        }
    }

    async function deleteHistoryItem(id) {
        try {
            const res = await fetch(`/api/v1/history/${id}`, { method: "DELETE" });
            if (res.ok) {
                showAlert(currentUiLang === "vi" ? "Đã xóa báo cáo thành công!" : "Report deleted successfully!", "success");
                
                if (resultsSection && (activeReportId === id || resultsSection.classList.contains("hidden") === false)) {
                    resultsSection.classList.add("hidden");
                    activeReportId = null;
                }
                
                loadHistory();
            }
        } catch (err) {
            showAlert("Xóa báo cáo thất bại.", "error");
        }
    }

    function updateKPIs(items) {
        if (kpiTotal) kpiTotal.textContent = items ? items.length : 0;
        if (items && items.length > 0) {
            const first = items[0];
            if (kpiLastTicker) kpiLastTicker.textContent = first.ticker;
            if (kpiLastRec) kpiLastRec.textContent = first.recommendation;
            if (kpiLastDate) kpiLastDate.textContent = (first.created_at || "").split("T")[0].split(" ")[0];
        } else {
            if (kpiLastTicker) kpiLastTicker.textContent = "N/A";
            if (kpiLastRec) kpiLastRec.textContent = "N/A";
            if (kpiLastDate) kpiLastDate.textContent = "N/A";
        }
    }

    // Helpers
    function showAlert(msg, type = "error") {
        if (!alertBox) return;
        if (alertTimer) clearTimeout(alertTimer);
        const icon = type === "success" ? `<i class="fa-solid fa-circle-check"></i>` : `<i class="fa-solid fa-circle-exclamation"></i>`;
        alertBox.innerHTML = `${icon} <span>${msg}</span>`;
        alertBox.className = `alert-card ${type}`;
        alertBox.classList.remove("hidden");

        alertTimer = setTimeout(() => {
            hideAlert();
        }, 3500);
    }

    function hideAlert() {
        if (alertBox) alertBox.classList.add("hidden");
    }

    function showLoading(ticker) {
        const textEl = document.getElementById("loadingText");
        const subEl = document.getElementById("loadingSub");
        if (currentUiLang === "vi") {
            if (textEl) textEl.textContent = `Đang phân tích cổ phiếu ${ticker}...`;
            if (subEl) subEl.textContent = "Đang thu thập dữ liệu tài chính, biểu đồ và tin tức mới nhất...";
        } else {
            if (textEl) textEl.textContent = `Analyzing stock ${ticker}...`;
            if (subEl) subEl.textContent = "Gathering financial data, technical charts, and latest market news...";
        }
        if (loadingOverlay) loadingOverlay.classList.remove("hidden");
    }

    function showLoadingText(title, sub) {
        const textEl = document.getElementById("loadingText");
        const subEl = document.getElementById("loadingSub");
        if (textEl) textEl.textContent = title;
        if (subEl) subEl.textContent = sub || "";
        if (loadingOverlay) loadingOverlay.classList.remove("hidden");
    }

    function hideLoading() {
        if (loadingOverlay) loadingOverlay.classList.add("hidden");
    }
}

// Ensure initApp is executed regardless of document readiness timing
if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initApp);
} else {
    initApp();
}
