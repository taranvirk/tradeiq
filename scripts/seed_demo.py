from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.database.seed import seed_demo_database  # noqa: E402
from app.database.session import SessionLocal  # noqa: E402

if __name__ == "__main__":
    with SessionLocal() as database:
        seed_demo_database(database)
    print("TradeIQ demo account and market data are ready.")
