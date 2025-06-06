import json
import os
from asyncio import Lock
from typing import Dict, Optional

import aiofiles

from tonutils.tonconnect import IStorage


class FileStorage(IStorage):
    """
    File-based asynchronous implementation of TonConnect IStorage interface.

    Stores key-value pairs in a local JSON file using asyncio-compatible file I/O.

    :param file_path: Path to the JSON file used for persistent storage.
    """

    def __init__(self, file_path: str):
        self.file_path = file_path
        self.lock = Lock()

        if not os.path.exists(self.file_path):
            with open(self.file_path, "w") as f:
                json.dump({}, f)

    async def _read_data(self) -> Dict[str, str]:
        """
        Read the current contents of the JSON storage file.

        :return: Dictionary containing all stored key-value pairs.
        """
        async with self.lock:
            async with aiofiles.open(self.file_path, "r") as f:
                content = await f.read()
                return json.loads(content) if content else {}

    async def _write_data(self, data: Dict[str, str]) -> None:
        """
        Write a new dictionary to the JSON storage file.

        :param data: Key-value pairs to persist.
        """
        async with self.lock:
            async with aiofiles.open(self.file_path, "w") as f:
                await f.write(json.dumps(data, indent=4))

    async def set_item(self, key: str, value: str) -> None:
        """
        Set a key-value pair in storage.

        :param key: Key to set.
        :param value: Value to associate with the key.
        """
        data = await self._read_data()
        data[key] = value
        await self._write_data(data)

    async def get_item(self, key: str, default_value: Optional[str] = None) -> Optional[str]:
        """
        Retrieve the value associated with a key.

        :param key: Key to retrieve.
        :param default_value: Value to return if the key is not found.
        :return: Stored value or default if not found.
        """
        data = await self._read_data()
        return data.get(key, default_value)

    async def remove_item(self, key: str) -> None:
        """
        Remove a key-value pair from storage.

        :param key: Key to remove.
        """
        data = await self._read_data()
        if key in data:
            del data[key]
            await self._write_data(data)
