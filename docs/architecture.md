# Architecture

TradeIQ uses a layered monolith so the business boundaries are visible without premature microservice complexity. FastAPI routes validate transport concerns and delegate to provider, feature, ML, strategy, backtest, risk, and broker modules. SQLAlchemy is the persistence boundary; Alembic owns schema changes.

The critical order path is one-way: prediction → strategy → risk decision → order state → broker → trade/portfolio journal. A model module never imports a broker. The independent risk manager applies the global kill switch, cash, position, exposure, and confidence constraints before an order can be submitted.

Redis carries worker liveness today and is the natural queue/cache boundary for scaled deployments. The APScheduler worker is intentionally separate from the web process. Frontend queries use JWT bearer authentication and explicit loading, error, empty, and success states.

The frontend is split into public (`/`, `/login`, `/signup`) and protected application routes. Startup restores a stored session through `/auth/me` before private UI is rendered. New accounts are redirected to `/onboarding` until a dedicated paper account exists.

User-owned records are resolved from the authenticated JWT identity, never a request-supplied user ID. Active paper-account IDs further scope orders, trades, snapshots, and reset history. Logout increments a server-side token version so previously issued access tokens stop working immediately.
