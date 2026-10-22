# Backtesting

The backtester consumes time-ordered OHLCV data and a `TradingStrategy`. It models cash, integer shares, entry cost, commission, slippage, fills, closed-trade P&L, daily portfolio value, and exposure. It reports total/annualized return, Sharpe, Sortino, maximum drawdown, win rate, profit factor, average win/loss, trade count, exposure, volatility, and buy-and-hold benchmark return.

No strategy reads a future candle. Signals for each timestamp are executed using that timestamp's modeled fill and the resulting equity is recorded after execution.
