import asyncio
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import aiohttp
from cachetools import TTLCache

from tonutils.tonconnect.utils.logger import logger
from .exceptions import FetchWalletsError
from ..models.wallet import WalletApp


class FallbackWalletManager:
    """
    Provides a fallback mechanism for storing and retrieving wallet data
    locally as JSON, ensuring wallets can still be loaded if remote fetch fails.
    """

    FILE_PATH = Path(__file__).parent / "_data/fallback_wallets.json"

    def __init__(self, file_path: Optional[str] = None) -> None:
        if file_path:
            self.FILE_PATH = Path(file_path)
        self.lock = asyncio.Lock()

    async def load_wallets(self) -> List[Dict[str, Any]]:
        """
        Loads the fallback wallet data from a local JSON file.

        :return: A list of wallet dictionaries.
        """
        async with self.lock:
            try:
                with open(self.FILE_PATH, mode="r", encoding="utf-8") as file:
                    content = file.read()
                    return json.loads(content)
            except (json.JSONDecodeError, FileNotFoundError) as e:
                logger.error(f"Error loading wallets: {e}")
                return []

    async def save_wallets(self, wallets: List[Dict[str, Any]]) -> None:
        """
        Saves the provided wallets list to a local JSON file.

        :param wallets: A list of wallet dictionaries.
        """
        async with self.lock:
            try:
                self.FILE_PATH.parent.mkdir(parents=True, exist_ok=True)

                with open(self.FILE_PATH, mode="w", encoding="utf-8") as file:
                    file.write(json.dumps(wallets, indent=4))
            except Exception as e:
                logger.error(f"Error saving wallets: {e}")


class CachedWalletManager:
    """
    Manages an in-memory cache of wallet data, utilizing a TTL (Time To Live)
    to invalidate cached items after a specified duration.
    """

    def __init__(self, cache_ttl: Optional[int] = None) -> None:
        """
        Initializes the cached wallet manager with an optional TTL.

        :param cache_ttl: The cache duration in seconds. Defaults to 86400 (24h).
        """
        if cache_ttl is None:
            cache_ttl = 86400
        self.cache: TTLCache = TTLCache(maxsize=1, ttl=cache_ttl)
        self.lock = asyncio.Lock()

    async def get_wallets(self) -> Optional[List[Dict[str, Any]]]:
        """
        Retrieves wallets from the cache if available.

        :return: A list of wallet dictionaries, or None if not cached.
        """
        async with self.lock:
            return self.cache.get("wallets")

    async def save_wallets(self, wallets: List[Dict[str, Any]]) -> None:
        """
        Saves wallets to the cache.

        :param wallets: A list of wallet dictionaries.
        """
        async with self.lock:
            self.cache["wallets"] = wallets


class WalletsListManager:
    """
    Fetches and manages a list of wallets, supporting caching and fallback storage.
    Optionally filters wallets by inclusion/exclusion lists.
    """

    PROBLEMATIC_WALLETS = [  # These wallets are known to have issues
        "tobi",
        "GateWallet",
    ]
    DEFAULT_URL = "https://raw.githubusercontent.com/ton-blockchain/wallets-list/main/wallets-v2.json"

    def __init__(
            self,
            source_url: Optional[str] = None,
            include_wallets: Optional[List[str]] = None,
            exclude_wallets: Optional[List[str]] = None,
            wallets_order: Optional[List[str]] = None,
            fallback_file_path: Optional[str] = None,
            cache_ttl: Optional[int] = None,
    ) -> None:
        """
        Initializes the WalletsListManager with optional inclusion/exclusion/order lists,
        source URL, and cache TTL.

        :param source_url: A custom URL to fetch the wallet list from.
        :param include_wallets: A list of wallet `app_name` to explicitly include.
        :param exclude_wallets: A list of wallet `app_name` to exclude.
        :param wallets_order: A list of wallet `app_name` to order.
        :param fallback_file_path: A custom file path to use for fallback storage.
        :param cache_ttl: The time-to-live (TTL) for caching wallet data (in seconds).
        """
        self._cache_manager = CachedWalletManager(cache_ttl)
        self._fallback_manager = FallbackWalletManager(fallback_file_path)

        self.source_url = source_url or WalletsListManager.DEFAULT_URL

        self.include_wallets = set(include_wallets or [])
        self.exclude_wallets = set(exclude_wallets or [])
        self.wallets_order = wallets_order

        self.exclude_wallets.update(WalletsListManager.PROBLEMATIC_WALLETS)

    async def _fetch_wallets(self) -> List[Dict[str, Any]]:
        """
        Fetches wallet data from the remote source.

        :return: A list of wallet dictionaries from the remote source.
        :raises FetchWalletsError: If the fetch fails or the format is invalid.
        """
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(self.source_url) as response:
                    response.raise_for_status()
                    content = await response.text()
                    wallets = json.loads(content)
                    if not isinstance(wallets, list):
                        raise FetchWalletsError("Invalid format: expected a list of wallets.")
                    return wallets
            except aiohttp.ClientError as e:
                raise FetchWalletsError(f"Error fetching wallets: {e}")
            except Exception as e:
                raise FetchWalletsError(f"Unexpected error: {e}")

    def _filter_wallets(self, wallets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Filters out wallets based on the exclude and include sets.

        :param wallets: A list of wallet dictionaries.
        :return: A filtered list of wallet dictionaries.
        """
        filtered_wallets = [
            w for w in wallets if w.get("app_name") and w["app_name"] not in self.exclude_wallets
        ]
        if self.include_wallets:
            filtered_wallets = [
                w for w in filtered_wallets if w["app_name"] in self.include_wallets
            ]
        return filtered_wallets

    def _order_wallets(self, wallets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if self.wallets_order:
            default = len(self.wallets_order)
            order_map = {n: i for i, n in enumerate(self.wallets_order)}
            wallets = sorted(wallets, key=lambda w: order_map.get(w.get("app_name", ""), default))

        return wallets

    @staticmethod
    def _get_supported_wallets(wallets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Extracts wallets that have an SSE-based bridge URL.

        :param wallets: A list of wallet dictionaries.
        :return: A list of wallet dictionaries with `bridge_url` field set for SSE.
        """
        supported_wallets = []
        for wallet in wallets:
            app_name = wallet.get("app_name")
            if app_name is None:
                continue

            for bridge in wallet.get("bridge", []):
                if bridge.get("type") == "sse" and "url" in bridge:
                    wallet_copy = wallet.copy()
                    wallet_copy["bridge_url"] = bridge["url"]
                    supported_wallets.append(wallet_copy)
                    break

        return supported_wallets

    async def _save_wallets(self, wallets: List[Dict[str, Any]]) -> None:
        """
        Saves wallet data to both the in-memory cache and the fallback local JSON file.

        :param wallets: A list of wallet dictionaries.
        """
        if len(wallets) > 0:
            await self._cache_manager.save_wallets(wallets)
            await self._fallback_manager.save_wallets(wallets)

    async def get_wallets(self) -> List[WalletApp]:
        """
        Retrieves the wallet list. If the cache is empty, attempts to fetch from the remote source;
        if that fails, loads wallets from the fallback file.

        :return: A list of WalletApp objects filtered by inclusion/exclusion, and supporting SSE.
        """
        cached_wallets = await self._cache_manager.get_wallets()

        if cached_wallets is None:
            try:
                remote_wallets = await self._fetch_wallets()
            except FetchWalletsError:
                remote_wallets = await self._fallback_manager.load_wallets()

            await self._save_wallets(remote_wallets)
            wallets_to_return = remote_wallets
        else:
            wallets_to_return = cached_wallets

        filtered_wallets = self._filter_wallets(wallets_to_return)
        supported_wallets = self._get_supported_wallets(filtered_wallets)
        ordered_wallets = self._order_wallets(supported_wallets)

        return [WalletApp.from_dict(w) for w in ordered_wallets]
