from __future__ import annotations

import json
from datetime import UTC, datetime

from apscheduler.schedulers.blocking import BlockingScheduler
from redis import Redis

from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger

settings = get_settings()
configure_logging(settings.log_level)
logger = get_logger(__name__)


def heartbeat() -> None:
    if settings.redis_url:
        redis = Redis.from_url(settings.redis_url, decode_responses=True)
        redis.setex("tradeiq:worker:heartbeat", 120, json.dumps({"timestamp": datetime.now(UTC).isoformat()}))
    logger.info("Background worker heartbeat", extra={"event_type": "WORKER_HEARTBEAT"})


def main() -> None:
    scheduler = BlockingScheduler(timezone="UTC")
    scheduler.add_job(heartbeat, "interval", seconds=60, id="heartbeat", max_instances=1)
    heartbeat()
    scheduler.start()


if __name__ == "__main__":
    main()
