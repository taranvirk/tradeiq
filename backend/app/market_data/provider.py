from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from datetime import UTC, datetime

import httpx


class MarketDataError(RuntimeError):
    pass


class MarketDataProvider(ABC):
    @abstractmethod
    async def get_historical_data(
        self, symbol: str, period: str = "1y", interval: str = "1d"
    ) -> list[dict]: ...

    @abstractmethod
    async def get_latest_quote(self, symbol: str) -> dict: ...


class YahooMarketDataProvider(MarketDataProvider):
    """Small resilient adapter around Yahoo's public chart response."""

    base_url = "https://query1.finance.yahoo.com/v8/finance/chart"

    async def _request(self, symbol: str, params: dict) -> dict:
        last_error: Exception | None = None
        for attempt in range(3):
            try:
                async with httpx.AsyncClient(timeout=8, headers={"User-Agent": "TradeIQ/1.0"}) as client:
                    response = await client.get(f"{self.base_url}/{symbol}", params=params)
                    response.raise_for_status()
                    return response.json()
            except (httpx.HTTPError, ValueError) as exc:
                last_error = exc
                if attempt < 2:
                    await asyncio.sleep(0.25 * (2**attempt))
        raise MarketDataError(f"Market provider unavailable for {symbol}") from last_error

    async def get_historical_data(self, symbol: str, period: str = "1y", interval: str = "1d") -> list[dict]:
        payload = await self._request(
            symbol.upper(), {"range": period, "interval": interval, "events": "history"}
        )
        try:
            result = payload["chart"]["result"][0]
            quote = result["indicators"]["quote"][0]
            adjusted = result["indicators"].get("adjclose", [{}])[0].get("adjclose", quote["close"])
            rows = []
            for index, unix_time in enumerate(result["timestamp"]):
                values = {key: quote[key][index] for key in ("open", "high", "low", "close", "volume")}
                if any(value is None for value in values.values()):
                    continue
                rows.append(
                    {
                        "symbol": symbol.upper(),
                        "timestamp": datetime.fromtimestamp(unix_time, UTC),
                        **values,
                        "adjusted_close": adjusted[index] or values["close"],
                        "interval": interval,
                        "source": "yahoo",
                    }
                )
            return validate_candles(rows)
        except (KeyError, IndexError, TypeError) as exc:
            raise MarketDataError(f"Malformed market response for {symbol}") from exc

    async def get_latest_quote(self, symbol: str) -> dict:
        candles = await self.get_historical_data(symbol, period="5d", interval="1d")
        if not candles:
            raise MarketDataError(f"No market data for {symbol}")
        latest = candles[-1]
        previous = candles[-2]["close"] if len(candles) > 1 else latest["close"]
        return {**latest, "change_percent": (latest["close"] / previous - 1) * 100}


def validate_candles(rows: list[dict]) -> list[dict]:
    if not rows:
        raise MarketDataError("Market provider returned no candles")
    seen: set[tuple[str, datetime]] = set()
    previous: datetime | None = None
    normalized: list[dict] = []
    for row in sorted(rows, key=lambda item: item["timestamp"]):
        if not row.get("symbol"):
            raise MarketDataError("Candle is missing a symbol")
        if any(float(row[field]) <= 0 for field in ("open", "high", "low", "close", "adjusted_close")):
            raise MarketDataError("Candle contains a non-positive price")
        if int(row["volume"]) < 0:
            raise MarketDataError("Candle contains negative volume")
        key = (row["symbol"], row["timestamp"])
        if key in seen:
            raise MarketDataError("Duplicate candle detected")
        if previous and row["timestamp"] <= previous:
            raise MarketDataError("Candle timestamps are out of order")
        seen.add(key)
        previous = row["timestamp"]
        normalized.append(row)
    return normalized
