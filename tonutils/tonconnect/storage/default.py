from typing import Optional, Dict

from .base import IStorage


class MemoryStorage(IStorage):
    """
    A simple in-memory storage implementation of IStorage.
    It keeps items in a class-level dictionary for demonstration or testing.
    """

    DATA: Dict[str, str] = {}

    async def set_item(self, key: str, value: str) -> None:
        """
        Stores the provided key-value pair in an in-memory dictionary.

        :param key: The storage key.
        :param value: The string value to store.
        """
        self.DATA[key] = value

    async def get_item(self, key: str, default_value: Optional[str] = None) -> Optional[str]:
        """
        Retrieves the value associated with the given key from the in-memory dictionary.

        :param key: The storage key.
        :param default_value: The value to return if the key is not found.
        :return: The stored value, or the default value if the key does not exist.
        """
        return self.DATA.get(key, default_value)

    async def remove_item(self, key: str) -> None:
        """
        Removes the specified key (and its value) from the in-memory dictionary if it exists.

        :param key: The storage key to remove.
        """
        if key in self.DATA:
            del self.DATA[key]
