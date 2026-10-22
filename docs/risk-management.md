# Risk management

TradeIQ starts in safe `simulation` mode with external trading disabled. Simulated and paper fills are allowed only after authentication and independent checks for positive notional, buying power, the user's bounded maximum position allocation, portfolio exposure, and optional minimum signal confidence. Sell requests also require sufficient owned quantity; short selling is not supported. `TRADING_ENABLED` never turns simulation into live-money execution, and the Alpaca adapter accepts paper endpoints only.

The sizing endpoint supports fixed-dollar, percentage-of-equity, and risk-based sizing. Risk-based sizing divides allowed account risk by stop distance. Rejections are persisted in `risk_events` and shown in the risk dashboard.
