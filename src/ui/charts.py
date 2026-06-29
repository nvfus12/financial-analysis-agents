import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import Dict, Any

def create_financial_chart(df: pd.DataFrame) -> go.Figure:
    """
    Generates a premium, unified dark-themed financial chart.
    Includes Candlestick + MA overlays, RSI sub-chart, and MACD indicators.
    """
    if df is None or df.empty:
        # Return empty placeholder figure
        fig = go.Figure()
        fig.add_annotation(text="No price data available.", x=0.5, y=0.5, showarrow=False)
        fig.update_layout(template="plotly_dark")
        return fig

    # Ensure index is datetime and sorted
    df = df.copy()
    df.index = pd.to_datetime(df.index)
    df.sort_index(inplace=True)

    # Compute MAs for plotting
    df["MA20"] = df["close"].rolling(window=20).mean()
    df["MA50"] = df["close"].rolling(window=50).mean()

    # Compute RSI
    delta = df["close"].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / (loss + 1e-10)
    df["RSI"] = 100 - (100 / (1 + rs))

    # Compute MACD
    exp12 = df["close"].ewm(span=12, adjust=False).mean()
    exp26 = df["close"].ewm(span=26, adjust=False).mean()
    df["MACD"] = exp12 - exp26
    df["Signal"] = df["MACD"].ewm(span=9, adjust=False).mean()
    df["Hist"] = df["MACD"] - df["Signal"]

    # Create subplots (3 rows: Price + MAs, RSI, MACD)
    fig = make_subplots(
        rows=3, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.06,
        row_heights=[0.5, 0.25, 0.25]
    )

    # 1. Candlestick & Moving Averages (Row 1)
    fig.add_trace(
        go.Candlestick(
            x=df.index,
            open=df["open"],
            high=df["high"],
            low=df["low"],
            close=df["close"],
            name="OHLC",
            increasing_line_color="#26a69a",  # Sleek Emerald Green
            decreasing_line_color="#ef5350",  # Sleek Coral Red
            increasing_fillcolor="#26a69a",
            decreasing_fillcolor="#ef5350"
        ),
        row=1, col=1
    )

    fig.add_trace(
        go.Scatter(
            x=df.index, y=df["MA20"],
            line=dict(color="#29b6f6", width=1.5),  # Electric Blue
            name="MA20"
        ),
        row=1, col=1
    )

    fig.add_trace(
        go.Scatter(
            x=df.index, y=df["MA50"],
            line=dict(color="#ab47bc", width=1.5),  # Vibrant Purple
            name="MA50"
        ),
        row=1, col=1
    )

    # 2. RSI Subplot (Row 2)
    fig.add_trace(
        go.Scatter(
            x=df.index, y=df["RSI"],
            line=dict(color="#ffca28", width=1.5),  # Gold Line
            name="RSI (14)"
        ),
        row=2, col=1
    )

    # RSI threshold lines (70 overbought, 30 oversold)
    fig.add_hline(y=70, line_dash="dash", line_color="#ef5350", line_width=1, row=2, col=1)
    fig.add_hline(y=30, line_dash="dash", line_color="#26a69a", line_width=1, row=2, col=1)
    # Shaded neutral area
    fig.add_hrect(y0=30, y1=70, fillcolor="#ffffff", opacity=0.04, line_width=0, row=2, col=1)

    # 3. MACD Subplot (Row 3)
    fig.add_trace(
        go.Scatter(
            x=df.index, y=df["MACD"],
            line=dict(color="#26c6da", width=1.2),  # Cyan
            name="MACD"
        ),
        row=3, col=1
    )

    fig.add_trace(
        go.Scatter(
            x=df.index, y=df["Signal"],
            line=dict(color="#ff7043", width=1.2),  # Orange-red
            name="Signal"
        ),
        row=3, col=1
    )

    # MACD Histogram bars (green for positive, red for negative)
    hist_colors = [
        "#26a69a" if val >= 0 else "#ef5350" for val in df["Hist"]
    ]
    fig.add_trace(
        go.Bar(
            x=df.index, y=df["Hist"],
            marker_color=hist_colors,
            name="Histogram"
        ),
        row=3, col=1
    )

    # Adjust Layout settings for clean premium appearance
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(15, 23, 42, 0.8)",  # Dark Blue-slate transparent
        plot_bgcolor="rgba(15, 23, 42, 0.8)",
        margin=dict(l=20, r=20, t=10, b=20),
        xaxis_rangeslider_visible=False,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            bgcolor="rgba(0, 0, 0, 0)"
        ),
        hovermode="x unified",
        height=680
    )

    # Configure axes formatting
    fig.update_yaxes(title_text="Price (VND)", row=1, col=1, gridcolor="rgba(255, 255, 255, 0.05)")
    fig.update_yaxes(title_text="RSI", row=2, col=1, range=[10, 90], gridcolor="rgba(255, 255, 255, 0.05)")
    fig.update_yaxes(title_text="MACD", row=3, col=1, gridcolor="rgba(255, 255, 255, 0.05)")
    fig.update_xaxes(gridcolor="rgba(255, 255, 255, 0.05)")

    return fig
