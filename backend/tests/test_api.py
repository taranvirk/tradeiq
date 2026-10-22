import asyncio

from httpx import ASGITransport, AsyncClient

from app.main import app
from app.market_data.catalog import STOCK_CATALOG


async def get(path: str, token: str | None = None):
    transport = ASGITransport(app=app)
    headers = {"Authorization": f"Bearer {token}"} if token else None
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        return await client.get(path, headers=headers)


async def post(path: str, json: dict | None = None, token: str | None = None):
    transport = ASGITransport(app=app)
    headers = {"Authorization": f"Bearer {token}"} if token else None
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        return await client.post(path, json=json, headers=headers)


def test_root_returns_application_identity() -> None:
    response = asyncio.run(get("/"))

    assert response.status_code == 200
    assert response.json()["name"] == "TradeIQ"


def test_health_reports_database_connection() -> None:
    response = asyncio.run(get("/health"))

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "healthy"
    assert payload["database"] == "connected"
    assert payload["redis"] == "not_configured"
    assert payload["market_api"] == "connected"


def test_meta_defaults_to_safe_trading_mode() -> None:
    response = asyncio.run(get("/api/v1/meta"))

    assert response.status_code == 200
    payload = response.json()
    assert payload["trading_mode"] == "simulation"
    assert payload["trading_enabled"] is False


def test_demo_authentication_and_protected_portfolio() -> None:
    login = asyncio.run(post("/api/v1/auth/demo"))
    assert login.status_code == 200
    token = login.json()["access_token"]

    async def protected_get():
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            return await client.get("/api/v1/portfolio", headers={"Authorization": f"Bearer {token}"})

    response = asyncio.run(protected_get())
    assert response.status_code == 200
    assert response.json()["equity"] == 10_000


def test_unknown_ticker_returns_consistent_error() -> None:
    response = asyncio.run(get("/api/v1/stocks/NOTREAL"))
    assert response.status_code == 404
    assert response.json() == {"error": "REQUEST_FAILED", "message": "Unknown ticker"}


def test_catalog_covers_major_us_and_canadian_exchanges() -> None:
    exchanges = {stock.exchange for stock in STOCK_CATALOG.values()}

    assert len(STOCK_CATALOG) >= 60
    assert {"NASDAQ", "NYSE", "TSX", "TSXV"}.issubset(exchanges)


def test_stock_search_can_filter_canadian_exchange_and_reports_currency() -> None:
    response = asyncio.run(get("/api/v1/stocks?exchange=TSX"))

    assert response.status_code == 200
    assert [stock["symbol"] for stock in response.json()] == ["SHOP.TO"]
    assert response.json()[0]["quote_currency"] == "CAD"


def test_complete_account_onboarding_trade_and_session_persistence() -> None:
    weak = asyncio.run(
        post(
            "/api/v1/auth/register",
            {
                "first_name": "New",
                "last_name": "Trader",
                "email": "new.trader@example.com",
                "password": "weakpass",
                "confirm_password": "weakpass",
            },
        )
    )
    assert weak.status_code == 422

    credentials = {
        "first_name": "New",
        "last_name": "Trader",
        "email": "new.trader@example.com",
        "password": "StrongPass1",
        "confirm_password": "StrongPass1",
    }
    registered = asyncio.run(post("/api/v1/auth/register", credentials))
    assert registered.status_code == 201
    token = registered.json()["access_token"]
    assert registered.json()["onboarding_required"] is True

    duplicate = asyncio.run(post("/api/v1/auth/register", credentials))
    assert duplicate.status_code == 409
    assert asyncio.run(get("/api/v1/portfolio", token)).status_code == 404

    account = asyncio.run(
        post("/api/v1/paper-account", {"starting_balance": 25_000}, token)
    )
    assert account.status_code == 201
    assert account.json()["initial_balance"] == 25_000
    assert asyncio.run(get("/api/v1/auth/me", token)).json()["onboarding_required"] is False

    order = asyncio.run(
        post(
            "/api/v1/orders",
            {
                "symbol": "AAPL",
                "side": "BUY",
                "notional_amount": 500,
                "order_type": "market",
                "client_order_id": "new-trader-first-order",
            },
            token,
        )
    )
    assert order.status_code == 201
    assert order.json()["quantity"] == 5
    portfolio = asyncio.run(get("/api/v1/portfolio", token)).json()
    assert portfolio["cash"] == 24_500
    assert portfolio["equity"] == 25_000
    assert portfolio["total_pnl"] == 0

    logout = asyncio.run(post("/api/v1/auth/logout", token=token))
    assert logout.status_code == 204
    assert asyncio.run(get("/api/v1/portfolio", token)).status_code == 401

    login = asyncio.run(
        post(
            "/api/v1/auth/login",
            {"email": credentials["email"], "password": credentials["password"]},
        )
    )
    restored = asyncio.run(get("/api/v1/portfolio", login.json()["access_token"]))
    assert restored.status_code == 200
    assert restored.json()["positions"][0]["symbol"] == "AAPL"
