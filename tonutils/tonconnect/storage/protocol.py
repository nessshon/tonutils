import typing as t


class StorageProtocol(t.Protocol):
    """Key-value storage for TonConnect session data."""

    async def set_item(self, key: str, value: t.Any) -> None:
        """Store a value.

        :param key: Storage key.
        :param value: Value to store.
        """

    async def get_item(self, key: str) -> t.Optional[t.Any]:
        """Retrieve a value, or `None` if missing.

        :param key: Storage key.
        """

    async def remove_item(self, key: str) -> None:
        """Remove a value.

        :param key: Storage key.
        """
