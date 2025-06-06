from typing import Optional

from redis.asyncio import Redis
from tonutils.tonconnect import IStorage


class RedisStorage(IStorage):
    """
    Redis-based implementation of the IStorage interface.
    Used for storing TonConnect session data.

    :param redis_client: Redis connection instance.
    """

    def __init__(self, redis_client: Redis):
        self.redis = redis_client

    async def set_item(self, key: str, value: str) -> None:
        """
        Store a key-value pair in Redis.

        :param key: The key to store.
        :param value: The value to associate with the key.
        """
        async with self.redis.client() as client:
            await client.set(name=key, value=value)

    async def get_item(self, key: str, default_value: Optional[str] = None) -> Optional[str]:
        """
        Retrieve a value from Redis by key.

        :param key: The key to retrieve.
        :param default_value: Value to return if key is not found.
        :return: Retrieved value or default_value.
        """
        async with self.redis.client() as client:
            value = await client.get(name=key)
            return value if value else default_value

    async def remove_item(self, key: str) -> None:
        """
        Remove a key-value pair from Redis.

        :param key: The key to remove.
        """
        async with self.redis.client() as client:
            await client.delete(key)
