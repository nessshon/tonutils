import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import aiohttp
from cachetools import TTLCache

from tonutils.tonconnect.models.wallet import WalletApp
from .exceptions import FetchWalletsError


class FallbackWalletManager:
    """
    Provides a fallback mechanism for storing and retrieving wallet data
    locally as JSON, ensuring wallets can still be loaded if remote fetch fails.
    """

    FILE_PATH = Path(__file__).parent / "_data/fallback_wallets.json"

    @staticmethod
    def load_wallets() -> List[Dict[str, Any]]:
        """
        Loads the fallback wallet data from a local JSON file.

        :return: A list of wallet dictionaries.
        """
        if not FallbackWalletManager.FILE_PATH.exists():
            FallbackWalletManager.save_wallets([])
            return []

        with open(FallbackWalletManager.FILE_PATH, "r", encoding="utf-8") as file:
            return json.load(file)

    @staticmethod
    def save_wallets(wallets: List[Dict[str, Any]]) -> None:
        """
        Saves the provided wallets list to a local JSON file.

        :param wallets: A list of wallet dictionaries.
        """
        FallbackWalletManager.FILE_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(FallbackWalletManager.FILE_PATH, "w", encoding="utf-8") as file:
            file.write(json.dumps(wallets, indent=4))


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

    def get_wallets(self) -> Optional[List[Dict[str, Any]]]:
        """
        Retrieves wallets from the cache if available.

        :return: A list of wallet dictionaries, or None if not cached.
        """
        return self.cache.get("wallets")

    def save_wallets(self, wallets: List[Dict[str, Any]]) -> None:
        """
        Saves wallets to the cache.

        :param wallets: A list of wallet dictionaries.
        """
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
            cache_ttl: Optional[int] = None,
    ) -> None:
        """
        Initializes the WalletsListManager with optional inclusion/exclusion lists,
        source URL, and cache TTL.

        :param source_url: A custom URL to fetch the wallet list from.
        :param include_wallets: A list of wallet names/IDs to explicitly include.
        :param exclude_wallets: A list of wallet names/IDs to exclude.
        :param cache_ttl: The time-to-live (TTL) for caching wallet data (in seconds).
        """
        self._cache_manager = CachedWalletManager(cache_ttl)
        self._fallback_manager = FallbackWalletManager()

        self.source_url = source_url or WalletsListManager.DEFAULT_URL

        self.include_wallets = set(include_wallets or [])
        self.exclude_wallets = set(exclude_wallets or [])
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
        filtered_wallets = [w for w in wallets if w["app_name"] not in self.exclude_wallets]
        if self.include_wallets:
            filtered_wallets = [
                w for w in filtered_wallets if w["app_name"] in self.include_wallets
            ]
        return filtered_wallets

    @staticmethod
    def _get_supported_wallets(wallets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Extracts wallets that have an SSE-based bridge URL.

        :param wallets: A list of wallet dictionaries.
        :return: A list of wallet dictionaries with `bridge_url` field set for SSE.
        """
        supported_wallets = []
        for wallet in wallets:
            for bridge in wallet.get("bridge", []):
                if bridge.get("type") == "sse" and "url" in bridge:
                    wallet_copy = wallet.copy()
                    wallet_copy["bridge_url"] = bridge["url"]
                    supported_wallets.append(wallet_copy)
                    break
        return supported_wallets

    def _save_wallets(self, wallets: List[Dict[str, Any]]) -> None:
        """
        Saves wallet data to both the in-memory cache and the fallback local JSON file.

        :param wallets: A list of wallet dictionaries.
        """
        self._cache_manager.save_wallets(wallets)
        self._fallback_manager.save_wallets(wallets)

    async def get_wallets(self) -> List[WalletApp]:
        """
        Retrieves the wallet list. If the cache is empty, attempts to fetch from the remote source;
        if that fails, loads wallets from the fallback file.

        :return: A list of WalletApp objects filtered by inclusion/exclusion, and supporting SSE.
        """
        cached_wallets = self._cache_manager.get_wallets()
        if cached_wallets is None:
            try:
                remote_wallets = await self._fetch_wallets()
            except FetchWalletsError:
                remote_wallets = self._fallback_manager.load_wallets()

            self._save_wallets(remote_wallets)
            wallets_to_return = remote_wallets
        else:
            wallets_to_return = cached_wallets

        filtered_wallets = self._filter_wallets(wallets_to_return)
        supported_wallets = self._get_supported_wallets(filtered_wallets)
        return [WalletApp.from_dict(w) for w in supported_wallets]
