import asyncio
import time
from contextlib import suppress

from redis.asyncio import Redis
from tonutils.tonconnect import TonConnect


class TonConnectSessionManager:
    """
    Closes inactive TonConnect sessions using Redis-based activity tracking.
    """

    def __init__(
            self,
            redis: Redis,
            tc: TonConnect,
            session_lifetime: int = 3600,
            check_interval: int = 600,
            redis_key: str = "tonconnect:last_seen",
    ) -> None:
        """
        :param redis: Redis client instance.
        :param tc: TonConnect instance.
        :param session_lifetime: Inactivity threshold in seconds.
        :param check_interval: Interval between cleanup runs in seconds.
        :param redis_key: Redis sorted set key for storing user activity.
        """
        self.redis = redis
        self.tc = tc
        self.session_lifetime = session_lifetime
        self.check_interval = check_interval
        self.redis_key = redis_key
        self._running = False

    async def update(self, user_id: int) -> None:
        """
        Register user activity by storing a timestamp in Redis.

        :param user_id: Telegram user ID.
        """
        await self.redis.zadd(self.redis_key, {str(user_id): time.time()})

    async def _cleanup(self, cutoff: float) -> None:
        """
        Close sessions for users inactive since the given timestamp.

        :param cutoff: UNIX timestamp used as inactivity threshold.
        """
        user_ids = await self.redis.zrangebyscore(
            self.redis_key, min=0, max=cutoff, start=0, num=100
        )
        if not user_ids:
            return

        for raw_id in user_ids:
            user_id = int(raw_id)
            connector = await self.tc.get_connector(user_id)
            if connector and connector.connected and not connector.bridge.is_session_closed:
                with suppress(Exception):
                    await connector.bridge.pause_sse()

            await self.redis.zrem(self.redis_key, user_id)

    async def start(self) -> None:
        """
        Launch the background task for periodic session cleanup.
        """
        self._running = True
        while self._running:
            cutoff = time.time() - self.session_lifetime
            await self._cleanup(cutoff)

            await asyncio.sleep(self.check_interval)

    def run(self) -> None:
        loop = asyncio.get_running_loop()
        loop.create_task(self.start())

    def stop(self) -> None:
        """
        Stop the background cleanup loop.
        """
        self._running = False
