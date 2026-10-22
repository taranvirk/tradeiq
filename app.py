from __future__ import annotations

from datetime import date, timedelta

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.backtest import buy_and_hold_backtest, rsi_mean_reversion_backtest, sma_crossover_backtest
from src.data import download_price_data, parse_tickers
from src.indicators import add_indicators
from src.metrics import calculate_metrics
from src.portfolio import build_portfolio_equity

st.set_page_config(
    page_title="Stock Portfolio & Backtesting Dashboard",
    page_icon="📈",
    layout="wide",
)

st.title("📈 Stock Portfolio & Strategy Backtesting Dashboard")
st.caption(
    "Analyze stocks, simulate a portfolio, and compare simple strategies using historical market data."
)


@st.cache_data(show_spinner=False, ttl=60 * 60)
def load_price_data(tickers: tuple[str, ...], start: str, end: str) -> dict[str, pd.DataFrame]:
    return download_price_data(list(tickers), start=start, end=end)



def format_pct(value: float) -> str:
    return f"{value:.2%}"



def parse_weight_input(raw: str, tickers: list[str]) -> dict[str, float] | None:
    cleaned = raw.strip()
    if not cleaned:
        return None

    parts = [part.strip() for part in cleaned.split(",") if part.strip()]
    if len(parts) != len(tickers):
        raise ValueError(f"Provide exactly {len(tickers)} weights, one for each selected ticker.")

    values = [float(part) for part in parts]
    mapping = dict(zip(tickers, values))
    return mapping



def metric_row(metrics: dict[str, float], cols: list) -> None:
    labels = [
        "Cumulative Return",
        "Annualized Return",
        "Annualized Volatility",
        "Sharpe Ratio",
        "Max Drawdown",
    ]
    for col, label in zip(cols, labels):
        value = metrics.get(label, 0.0)
        display = f"{value:.2f}" if label == "Sharpe Ratio" else format_pct(value)
        col.metric(label, display)



def build_candlestick_chart(frame: pd.DataFrame, ticker: str) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(
        go.Candlestick(
            x=frame.index,
            open=frame["Open"],
            high=frame["High"],
            low=frame["Low"],
            close=frame["Close"],
            name=ticker,
        )
    )

    fig.add_trace(go.Scatter(x=frame.index, y=frame["SMA20"], mode="lines", name="SMA20"))
    fig.add_trace(go.Scatter(x=frame.index, y=frame["SMA50"], mode="lines", name="SMA50"))
    fig.update_layout(
        title=f"{ticker} Price Chart",
        xaxis_title="Date",
        yaxis_title="Price",
        xaxis_rangeslider_visible=False,
        margin=dict(l=20, r=20, t=40, b=20),
        height=500,
    )
    return fig



def build_equity_chart(frame: pd.DataFrame, column: str, title: str) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=frame.index, y=frame[column], mode="lines", name=title))
    fig.update_layout(
        title=title,
        xaxis_title="Date",
        yaxis_title="Portfolio Value",
        margin=dict(l=20, r=20, t=40, b=20),
        height=400,
    )
    return fig


with st.sidebar:
    st.header("Controls")
    default_start = date.today() - timedelta(days=365 * 3)
    default_end = date.today()

    ticker_input = st.text_input("Tickers", value="AAPL, MSFT, NVDA, SPY")
    benchmark = st.text_input("Benchmark Ticker", value="SPY")
    start_date = st.date_input("Start Date", value=default_start)
    end_date = st.date_input("End Date", value=default_end)
    initial_capital = st.number_input("Initial Capital ($)", min_value=1000, max_value=1_000_000, value=10_000, step=1000)
    custom_weights_raw = st.text_input(
        "Custom Weights (optional)",
        value="",
        help="Comma-separated weights in the same order as the selected tickers, e.g. 40,30,20,10",
    )

    st.subheader("Backtest Settings")
    strategy_name = st.selectbox("Strategy", ["Buy and Hold", "SMA Crossover", "RSI Mean Reversion"])
    sma_short = st.slider("SMA Short Window", min_value=5, max_value=50, value=20)
    sma_long = st.slider("SMA Long Window", min_value=20, max_value=200, value=50)
    rsi_lower = st.slider("RSI Buy Threshold", min_value=10, max_value=45, value=30)
    rsi_upper = st.slider("RSI Sell Threshold", min_value=50, max_value=90, value=55)


tickers = parse_tickers(ticker_input)
if not tickers:
    st.warning("Enter at least one stock ticker to continue.")
    st.stop()

all_tickers = tickers.copy()
if benchmark and benchmark.upper() not in all_tickers:
    all_tickers.append(benchmark.upper())

try:
    data = load_price_data(tuple(all_tickers), start=str(start_date), end=str(end_date))
except Exception as exc:
    st.error(f"Unable to load market data: {exc}")
    st.stop()

available_tickers = [ticker for ticker in tickers if ticker in data]
if not available_tickers:
    st.error("None of the requested tickers returned valid data.")
    st.stop()

focus_ticker = st.selectbox("Focus Ticker", available_tickers)
focus_frame = add_indicators(data[focus_ticker])
price_series = focus_frame["Price"]
benchmark_metrics = None

if benchmark.upper() in data:
    benchmark_equity = initial_capital * (1 + data[benchmark.upper()]["Adj Close"].pct_change().fillna(0.0)).cumprod()
    benchmark_metrics = calculate_metrics(benchmark_equity).as_dict()

summary_metrics = calculate_metrics(initial_capital * (1 + price_series.pct_change().fillna(0.0)).cumprod()).as_dict()
summary_cols = st.columns(5)
metric_row(summary_metrics, summary_cols)

if benchmark_metrics:
    st.caption(
        f"Benchmark ({benchmark.upper()}) return over the selected period: {format_pct(benchmark_metrics['Cumulative Return'])}"
    )

st.plotly_chart(build_candlestick_chart(focus_frame, focus_ticker), use_container_width=True)

signal_col, indicator_col = st.columns([2, 1])
with signal_col:
    returns_table = pd.DataFrame(
        {
            "Close": focus_frame["Close"],
            "SMA20": focus_frame["SMA20"],
            "SMA50": focus_frame["SMA50"],
            "RSI14": focus_frame["RSI14"],
            "Daily Return": focus_frame["Daily Return"],
        }
    ).tail(10)
    st.subheader(f"Recent Data for {focus_ticker}")
    st.dataframe(returns_table.style.format({"Close": "{:.2f}", "SMA20": "{:.2f}", "SMA50": "{:.2f}", "RSI14": "{:.2f}", "Daily Return": "{:.2%}"}))

with indicator_col:
    latest = focus_frame.iloc[-1]
    st.subheader("Snapshot")
    st.metric("Last Close", f"${latest['Close']:.2f}")
    st.metric("RSI14", f"{latest['RSI14']:.1f}")
    st.metric("20-Day Volatility", format_pct(float(latest["Volatility20"]) if pd.notna(latest["Volatility20"]) else 0.0))
    trend = "Bullish" if latest["SMA20"] > latest["SMA50"] else "Bearish"
    st.metric("Trend", trend)

portfolio_frames = {ticker: data[ticker] for ticker in available_tickers}
try:
    parsed_weights = parse_weight_input(custom_weights_raw, available_tickers)
    portfolio_frame, portfolio_metrics, normalized_weights = build_portfolio_equity(
        portfolio_frames,
        initial_capital=initial_capital,
        weights=parsed_weights,
    )
except Exception as exc:
    st.error(f"Portfolio setup error: {exc}")
    st.stop()

st.divider()
st.subheader("Portfolio Overview")
portfolio_cols = st.columns(5)
metric_row(portfolio_metrics, portfolio_cols)

weights_df = pd.DataFrame(
    {
        "Ticker": list(normalized_weights.keys()),
        "Weight": list(normalized_weights.values()),
    }
)
left_col, right_col = st.columns([2, 1])
with left_col:
    st.plotly_chart(build_equity_chart(portfolio_frame, "Equity", "Portfolio Equity Curve"), use_container_width=True)
with right_col:
    st.dataframe(weights_df.style.format({"Weight": "{:.2%}"}), hide_index=True)

st.divider()
st.subheader(f"Backtest: {strategy_name} on {focus_ticker}")

try:
    if strategy_name == "Buy and Hold":
        backtest_result = buy_and_hold_backtest(data[focus_ticker], initial_capital=initial_capital)
    elif strategy_name == "SMA Crossover":
        backtest_result = sma_crossover_backtest(
            data[focus_ticker],
            short_window=sma_short,
            long_window=sma_long,
            initial_capital=initial_capital,
        )
    else:
        backtest_result = rsi_mean_reversion_backtest(
            data[focus_ticker],
            lower=rsi_lower,
            upper=rsi_upper,
            initial_capital=initial_capital,
        )
except Exception as exc:
    st.error(f"Backtest error: {exc}")
    st.stop()

backtest_cols = st.columns(5)
metric_row(backtest_result.metrics, backtest_cols)
st.plotly_chart(build_equity_chart(backtest_result.frame, "Equity", f"{backtest_result.strategy_name} Equity Curve"), use_container_width=True)

trade_col, raw_col = st.columns([1, 1])
with trade_col:
    st.markdown("**Trade Log**")
    if backtest_result.trades.empty:
        st.info("No trade events were generated for the selected settings.")
    else:
        st.dataframe(backtest_result.trades.style.format({"Price": "${:.2f}"}), hide_index=True)

with raw_col:
    st.markdown("**Backtest Data**")
    display_cols = [col for col in ["Price", "Signal", "Position", "Strategy Return", "Equity"] if col in backtest_result.frame.columns]
    st.dataframe(backtest_result.frame[display_cols].tail(15).style.format({"Price": "${:.2f}", "Strategy Return": "{:.2%}", "Equity": "${:,.2f}"}))

st.divider()
st.markdown(
    " This project demonstrates Python data ingestion, financial analytics, portfolio simulation, backtesting logic, and interactive dashboard development."
)
