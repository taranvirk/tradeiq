# API

Swagger UI at `/docs` is the authoritative interactive contract. Business endpoints use `/api/v1`; health remains `/health`. Protected routes require `Authorization: Bearer <JWT>`.

Errors use a stable envelope:

```json
{"error":"REQUEST_FAILED","message":"Unknown ticker"}
```

Validation failures use `VALIDATION_ERROR`. Order risk failures return HTTP 403 and an `X-TradeIQ-Error` code. Market-provider failures return 503 after bounded exponential retries.

## Accounts

- `POST /api/v1/auth/register` validates first name, last name, unique email, matching passwords, and password strength.
- `POST /api/v1/auth/login` returns a signed, expiring JWT without revealing whether an email exists.
- `POST /api/v1/auth/logout` increments the user's token version, immediately invalidating the presented token and any older sessions.
- `GET /api/v1/auth/me` restores the current user and reports whether onboarding is required.
- `POST /api/v1/auth/demo` enters the populated recruiter demo account.

## Paper portfolios

- `POST /api/v1/paper-account` creates the authenticated user's first paper account with a backend-validated starting balance.
- `GET /api/v1/paper-account` returns the active paper account and its risk preferences.
- `POST /api/v1/paper-account/reset` requires the exact confirmation `RESET`, archives the prior simulation, and creates a clean account.
- `GET/PATCH /api/v1/settings/profile` manages safe profile fields.
- `GET/PATCH /api/v1/settings/trading` manages bounded paper-trading preferences.

Private queries derive ownership exclusively from the authenticated token. Portfolio, watchlist, prediction, backtest, order, trade, and settings routes never accept a client-supplied `user_id`.

`POST /api/v1/orders` accepts exactly one of `quantity` or `notional_amount`. Dollar orders are converted to fractional shares using the current simulated fill price. Short selling is rejected, and filled orders atomically update cash, positions, trades, and portfolio snapshots.

## Cross-border market research

- `GET /api/v1/stocks?q=&exchange=&limit=100` searches the curated market universe. Supported exchange filters are `NASDAQ`, `NYSE` (including NYSE Arca), `TSX`, and `TSXV`.
- `GET /api/v1/stocks/{symbol}/history` provides the candles used by charts, signals, and backtests.
- `POST /api/v1/models/train/{symbol}` trains and saves an authenticated user's signal for the chosen stock.
- `POST /api/v1/backtests` runs a selected strategy on the requested stock and saves the result for that user.

Yahoo-compatible Canadian symbols use `.TO` for TSX and `.V` for TSX Venture. The API returns `quote_currency` (`USD` or `CAD`) with each stock. Demo paper accounting does not perform foreign-exchange conversion.
