from abc import ABC, abstractmethod
from typing import Optional


class IStorage(ABC):
    """
    Abstract base class defining the interface for a storage system
    that supports setting, getting, and removing key-value items.
    """

    KEY_LAST_EVENT_ID = "last_event_id"
    KEY_CONNECTION = "connection"

    @abstractmethod
    async def set_item(self, key: str, value: str) -> None:
        """
        Stores the given string value under the specified key.

        :param key: The storage key.
        :param value: The string value to store.
        """

    @abstractmethod
    async def get_item(self, key: str, default_value: Optional[str] = None) -> Optional[str]:
        """
        Retrieves a stored string value by its key.

        :param key: The storage key.
        :param default_value: The value to return if the key is not found.
        :return: The stored string or the default value if not found.
        """

    @abstractmethod
    async def remove_item(self, key: str) -> None:
        """
        Removes the item identified by the specified key from storage.

        :param key: The storage key to remove.
        """
