# TradeIQ

**AI-Powered Algorithmic Trading & Portfolio Analytics Platform**

TradeIQ is a full-stack fintech research platform that turns validated market data into explainable predictions, risk-gated simulated orders, portfolio accounting, and recruiter-friendly analytics. It is built as a product—not a prediction notebook.

> Educational and portfolio software only. This is not investment advice. Live trading is not implemented and all execution defaults to disabled simulation mode.

## Features

- professional responsive React dashboard with accessible loading, error, empty, and success states
- public landing page plus real signup, login, server-invalidated logout, protected routes, and persistent sessions
- first-time onboarding with configurable $100-$10,000,000 simulated starting balances
- dedicated, user-owned paper accounts with fractional/notional orders, reset archiving, settings, and profile management
- recruiter-friendly populated demo account with user-specific watchlist, portfolio, research, and order data
- real Yahoo market-data adapter with retries, timeouts, validation, normalization, and PostgreSQL persistence
- 65-symbol US/Canadian catalog spanning NASDAQ, NYSE/NYSE Arca, TSX, and TSX Venture, with exchange-aware search
- candlestick explorer with volume-ready OHLC data, SMA, RSI, and MACD analytics
- 24-feature technical pipeline covering returns, trend, momentum, volatility, volume, and price structure
- leakage-safe Logistic Regression, Random Forest, Gradient Boosting, and XGBoost comparison
- chronological train/test splits, three-window walk-forward validation, model artifacts, registry, and experiment history
- searchable stock pickers for per-symbol AI signals and backtests, plus feature-based prediction explanations
- moving-average, RSI mean-reversion, and ML strategy interfaces
- cost-aware backtesting with commission, slippage, order fills, SPY-style benchmark, equity curves, and 12 metrics
- portfolio positions, snapshots, trade journal, attribution, monthly returns, and drawdown analytics
- simulated broker plus credential-gated Alpaca paper-broker adapter; no secrets enter the frontend
- independent position sizing and risk gate with exposure, buying power, confidence, and kill-switch controls
- REST/OpenAPI API, market WebSocket, Redis worker heartbeat, structured JSON logs, and audit tables
- PostgreSQL/Alembic, Docker Compose, automated tests, and GitHub Actions CI

## Product pages

1. Public product landing page
2. Signup, login, and paper-portfolio onboarding
3. Portfolio command center
4. Market explorer, stock detail, and reviewed paper order ticket
5. AI opportunity scanner and model registry
6. Backtesting strategy laboratory
7. Portfolio analytics and trading journal
8. Risk center, profile, trading settings, and deliberate portfolio reset

See the [landing page](docs/screenshots/landing.png), [login](docs/screenshots/login.png), and [demo dashboard](docs/screenshots/dashboard.png) screenshots.

## Architecture

```text
React + TypeScript + React Query
          │ REST / WebSocket
          ▼
FastAPI authentication and API layer
          │
┌─────────┼────────────────────────────────────┐
│ Market  │ Features │ ML │ Strategies │ Risk │
│ Data    │          │    │ Backtests  │ OMS  │
└─────────┼────────────────────────────────────┘
          │
   PostgreSQL + Redis worker
          │
 Yahoo market data / Alpaca paper trading
```

The execution boundary is intentional:

```text
AI analyzes → Strategy decides → Risk validates → Broker executes → Database records → Dashboard explains
```

Detailed design: [`docs/architecture.md`](docs/architecture.md).

## Tech stack

| Layer | Technology |
|---|---|
| Frontend | React, TypeScript, Vite, Tailwind CSS, Recharts, Axios, React Query |
| API | FastAPI, Pydantic, JWT, Argon2 |
| Data | PostgreSQL, SQLAlchemy, Alembic, Redis |
| ML | pandas, NumPy, scikit-learn, XGBoost, joblib |
| Engineering | Docker Compose, APScheduler, pytest, Ruff, ESLint, Vitest, GitHub Actions |

## Quick start

Requirements: Docker Desktop with the engine running.

```powershell
cd "C:\Users\taran\Desktop\Python Project\stock_resume_project"
docker compose up --build
```

Open:

- application landing page: http://localhost:5173
- Swagger API: http://localhost:8000/docs
- health: http://localhost:8000/health

The first startup applies migrations, trains the demo model comparison on deterministic simulated candles, and seeds the demo account. Subsequent starts reuse the PostgreSQL volume.

Stop without deleting data:

```powershell
docker compose down
```

## Accounts and demo

Create a personal account through `/signup`, choose a simulated balance during onboarding, and return later through `/login`. For a no-setup recruiter experience, select **View demo account** or sign in with:

```text
demo@tradeiq.dev / tradeiq-demo
```

Reset demo data only when intentional:

```powershell
docker compose down -v
docker compose up --build
```

Manual seeding is also available:

```powershell
python scripts/seed_demo.py
```

## Local development

Backend:

```powershell
Copy-Item .env.example .env
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Set-Location backend
..\.venv\Scripts\alembic.exe upgrade head
..\.venv\Scripts\uvicorn.exe app.main:app --reload
```

Frontend, using Node 22.13 or newer:

```powershell
Set-Location frontend
npm install
npm run dev
```

## Environment variables

| Variable | Purpose | Default posture |
|---|---|---|
| `DATABASE_URL` | SQLAlchemy connection | local SQLite if omitted |
| `REDIS_URL` | worker/cache connection | optional locally |
| `JWT_SECRET` | token signing secret | replace outside local development |
| `MARKET_DATA_PROVIDER` | provider selection | `yahoo` |
| `ALPACA_API_KEY` / `ALPACA_SECRET_KEY` | paper account credentials | empty |
| `ALPACA_BASE_URL` | brokerage endpoint | paper API only |
| `TRADING_MODE` | backtest/simulation/paper | `simulation` |
| `TRADING_ENABLED` | global order kill switch | `false` |
| `DEMO_MODE` | safe recruiter dataset | `true` |
| `MIN_PAPER_BALANCE` / `MAX_PAPER_BALANCE` | onboarding/reset balance bounds | `100` / `10000000` |
| `DEFAULT_PAPER_BALANCE` | onboarding default | `10000` |

Never commit `.env`. The Alpaca adapter rejects non-paper base URLs.

## API highlights

| Method | Route | Purpose |
|---|---|---|
| POST | `/api/v1/auth/register`, `/login`, `/logout`, `/demo` | account lifecycle and JWT authentication |
| GET | `/api/v1/auth/me` | server-validated session restoration |
| GET/POST | `/api/v1/paper-account` | paper-account onboarding and current account |
| POST | `/api/v1/paper-account/reset` | deliberate `RESET`-confirmed portfolio reset |
| GET/PATCH | `/api/v1/settings/profile`, `/settings/trading` | user and risk preferences |
| GET | `/api/v1/stocks`, `/stocks/{symbol}/history` | exchange-filtered search and validated candles |
| GET/POST/DELETE | `/api/v1/watchlist` | user-specific watchlist |
| GET | `/api/v1/predictions/{symbol}`, `/scanner` | explainable AI signals |
| POST | `/api/v1/models/train/{symbol}` | chronological model comparison |
| GET | `/api/v1/models`, `/experiments` | registry and experiment tracking |
| POST/GET | `/api/v1/backtests` | strategy research |
| GET | `/api/v1/portfolio`, `/positions`, `/trades`, `/analytics` | portfolio intelligence |
| POST/GET | `/api/v1/orders` | risk-gated OMS |
| POST | `/api/v1/risk/position-size` | position sizing |
| WS | `/api/v1/ws/market` | live quote updates |

Full API guide: [`docs/api.md`](docs/api.md).

`GET /api/v1/stocks` accepts `q`, `exchange` (`NASDAQ`, `NYSE`, `TSX`, or `TSXV`), and `limit`. Canadian provider symbols use `.TO` for TSX and `.V` for TSX Venture. Demo quotes are labeled by source and Canadian quotes display in CAD; the paper-account demo intentionally does not model FX conversion.

## Machine learning

The target is the probability of a positive next-period return. Data is never randomly shuffled. Imputers, scalers, and models are fitted only on training windows. Every artifact has a unique version, metrics, feature list, date range, and file path. See [`docs/machine-learning.md`](docs/machine-learning.md).

## Trading strategies and backtesting

Strategies emit desired exposure; they never submit orders. The backtester tracks cash, shares, entry cost, fills, commission, slippage, portfolio value, P&L, drawdown, exposure, and benchmark performance. See [`docs/backtesting.md`](docs/backtesting.md) and [`docs/trading-engine.md`](docs/trading-engine.md).

## Risk management

Every order is authenticated and passes buying-power, ownership, confidence, position-size, and exposure checks. Safe simulation and paper modes can execute persisted simulated fills; external/live execution remains unavailable unless explicitly configured, and the Alpaca adapter rejects non-paper URLs. See [`docs/risk-management.md`](docs/risk-management.md).

## Testing

```powershell
.\.venv\Scripts\python.exe -m ruff check backend scripts
.\.venv\Scripts\python.exe -m pytest
Set-Location frontend
npm run lint
npm run typecheck
npm test
npm run build
```

Tests cover market-data quality, indicators, strategy/backtest behavior, risk rejections, authentication, protected API routes, error envelopes, and the connected dashboard shell. External providers are not required by tests.

## Deployment

Images are stateless; persistent state belongs in managed PostgreSQL/Redis and model artifacts should use durable object storage in a hosted environment. Set production CORS origins, rotate `JWT_SECRET`, terminate TLS at the platform edge, and leave live trading unavailable. The included containers run on Render, Railway, Fly.io, or a standard container host.

## Legacy prototype

The original Streamlit modules remain under `app.py` and `src/` as a historical prototype. The production React/FastAPI path is under `frontend/` and `backend/`.

## Future improvements

- durable object storage for model artifacts
- Celery workers for high-volume multi-symbol retraining
- broker WebSocket reconciliation and partial-fill simulation
- Sentry/OpenTelemetry export
- deployment-specific infrastructure-as-code
