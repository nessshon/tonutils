from typing import Optional

from redis.asyncio import Redis

from tonutils.tonconnect import IStorage


class TCRedisStorage(IStorage):

    def __init__(self, redis_client: Redis):
        self.redis = redis_client

    async def set_item(self, key: str, value: str) -> None:
        async with self.redis.client() as client:
            await client.set(name=key, value=value)

    async def get_item(self, key: str, default_value: Optional[str] = None) -> Optional[str]:
        async with self.redis.client() as client:
            value = await client.get(name=key)
            return value if value else default_value

    async def remove_item(self, key: str) -> None:
        async with self.redis.client() as client:
            await client.delete(key)
