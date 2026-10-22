from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import uuid4

import httpx


class Broker(ABC):
    @abstractmethod
    async def get_account(self) -> dict: ...

    @abstractmethod
    async def get_positions(self) -> list[dict]: ...

    @abstractmethod
    async def get_orders(self) -> list[dict]: ...

    @abstractmethod
    async def submit_order(self, order: dict) -> dict: ...

    @abstractmethod
    async def cancel_order(self, order_id: str) -> dict: ...


class SimulatedBroker(Broker):
    def __init__(self, cash: float = 10_000) -> None:
        self.cash = cash
        self.orders: list[dict] = []
        self.positions: list[dict] = []

    async def get_account(self) -> dict:
        return {"cash": self.cash, "status": "ACTIVE", "mode": "simulation"}

    async def get_positions(self) -> list[dict]:
        return self.positions

    async def get_orders(self) -> list[dict]:
        return self.orders

    async def submit_order(self, order: dict) -> dict:
        filled = {**order, "id": str(uuid4()), "status": "FILLED"}
        self.orders.append(filled)
        return filled

    async def cancel_order(self, order_id: str) -> dict:
        return {"id": order_id, "status": "CANCELLED"}


class AlpacaPaperBroker(Broker):
    def __init__(self, key: str, secret: str, base_url: str = "https://paper-api.alpaca.markets") -> None:
        if "paper-api" not in base_url:
            raise ValueError("TradeIQ only permits Alpaca paper-trading endpoints")
        self.base_url = base_url.rstrip("/")
        self.headers = {"APCA-API-KEY-ID": key, "APCA-API-SECRET-KEY": secret}

    async def _request(self, method: str, path: str, json: dict | None = None) -> dict | list:
        async with httpx.AsyncClient(timeout=10, headers=self.headers) as client:
            response = await client.request(method, f"{self.base_url}{path}", json=json)
            response.raise_for_status()
            return response.json() if response.content else {}

    async def get_account(self) -> dict:
        return await self._request("GET", "/v2/account")  # type: ignore[return-value]

    async def get_positions(self) -> list[dict]:
        return await self._request("GET", "/v2/positions")  # type: ignore[return-value]

    async def get_orders(self) -> list[dict]:
        return await self._request("GET", "/v2/orders")  # type: ignore[return-value]

    async def submit_order(self, order: dict) -> dict:
        return await self._request("POST", "/v2/orders", order)  # type: ignore[return-value]

    async def cancel_order(self, order_id: str) -> dict:
        return await self._request("DELETE", f"/v2/orders/{order_id}")  # type: ignore[return-value]
