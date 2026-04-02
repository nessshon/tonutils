from __future__ import annotations

import asyncio
import typing as t
from contextlib import suppress

from ton_core import (
    AdnlAddressListConfig,
    DhtNodeConfig,
    GlobalConfig,
    NetworkGlobalID,
    get_mainnet_global_config,
    get_testnet_global_config,
)

from tonutils.clients.config import resolve_config
from tonutils.clients.dht.models import (
    Bucket,
    Continuation,
    DhtKey,
    DhtNode,
    DhtValue,
    KeyLike,
    PriorityList,
    affinity,
    normalize_key,
)
from tonutils.exceptions import (
    ClientError,
    DhtValueNotFoundError,
    NotConnectedError,
    ProviderError,
    TransportError,
)

if t.TYPE_CHECKING:
    from tonutils.providers.dht import DhtProvider

_BUCKET_COUNT = 256


class DhtNetwork:
    """Multi-node DHT client with Kademlia routing and iterative lookups.

    Works exclusively with clean models — all TL knowledge is in
    ``DhtProvider`` / ``DhtCodec``.
    """

    def __init__(
        self,
        *,
        nodes: list[DhtNodeConfig],
        k: int = 7,
        connect_timeout: float = 5.0,
        request_timeout: float = 3.0,
    ) -> None:
        from tonutils.providers.dht import DhtProvider

        self._provider = DhtProvider(
            nodes=nodes,
            k=k,
            connect_timeout=connect_timeout,
            request_timeout=request_timeout,
        )
        self._gateway_id: bytes = self._provider.local_key_id
        self._buckets: list[Bucket] = [Bucket(k=k) for _ in range(_BUCKET_COUNT)]
        self._connected = False

    @property
    def provider(self) -> DhtProvider:
        """Return the underlying DHT provider."""
        return self._provider

    @property
    def connected(self) -> bool:
        """Return whether the network is connected."""
        return self._connected and self._provider.connected

    @classmethod
    def from_config(
        cls,
        *,
        config: GlobalConfig | dict[str, t.Any] | str,
        k: int = 7,
        connect_timeout: float = 5.0,
        request_timeout: float = 3.0,
    ) -> DhtNetwork:
        """Create a network instance from a global config."""
        config = resolve_config(config)
        if config.dht is None:
            raise ClientError("DhtNetwork.from_config: no DHT section in config")
        return cls(
            nodes=config.dht.nodes,
            k=k,
            connect_timeout=connect_timeout,
            request_timeout=request_timeout,
        )

    @classmethod
    def from_network_config(
        cls,
        network: NetworkGlobalID = NetworkGlobalID.MAINNET,
        *,
        k: int = 7,
        connect_timeout: float = 5.0,
        request_timeout: float = 3.0,
    ) -> DhtNetwork:
        """Create a network instance for mainnet or testnet."""
        config_getters = {
            NetworkGlobalID.MAINNET: get_mainnet_global_config,
            NetworkGlobalID.TESTNET: get_testnet_global_config,
        }
        config = config_getters[network]()
        return cls.from_config(
            config=config,
            k=k,
            connect_timeout=connect_timeout,
            request_timeout=request_timeout,
        )

    async def connect(self) -> None:
        """Connect to DHT bootstrap nodes and populate routing buckets."""
        if self._connected:
            return
        connected_nodes = await self._provider.connect()
        for adnl_id, dht_node in connected_nodes:
            bucket_idx = affinity(self._gateway_id, adnl_id)
            self._buckets[min(bucket_idx, _BUCKET_COUNT - 1)].add_node(dht_node)
        if not any(len(b) > 0 for b in self._buckets):
            raise ClientError("DhtNetwork: all DHT nodes failed to connect")
        self._connected = True

    async def close(self) -> None:
        """Close the network and disconnect from all nodes."""
        self._connected = False
        await self._provider.close()

    async def __aenter__(self) -> DhtNetwork:
        await self.connect()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: t.Any | None,
    ) -> None:
        with suppress(asyncio.CancelledError):
            await self.close()

    def _add_node(self, node_tl: dict[str, t.Any]) -> DhtNode | None:
        """Parse node via codec, verify signature, add to buckets."""
        dht_node = self._provider.codec.parse_node(node_tl)
        if dht_node is None or dht_node.adnl_id == self._gateway_id:
            return None
        bucket_idx = affinity(self._gateway_id, dht_node.adnl_id)
        self._buckets[min(bucket_idx, _BUCKET_COUNT - 1)].add_node(dht_node)
        return dht_node

    def _add_parsed_node(self, dht_node: DhtNode) -> None:
        """Add an already-parsed DhtNode to routing buckets."""
        if dht_node.adnl_id == self._gateway_id:
            return
        bucket_idx = affinity(self._gateway_id, dht_node.adnl_id)
        self._buckets[min(bucket_idx, _BUCKET_COUNT - 1)].add_node(dht_node)

    def _build_priority_list(self, target_id: bytes) -> PriorityList:
        k = self._provider.k
        good_count = k + k // 2
        bad_count = k // 2

        good: list[tuple[int, DhtNode]] = []
        bad: list[tuple[int, DhtNode]] = []

        for bucket in self._buckets:
            for node in bucket.get_nodes():
                aff = affinity(node.adnl_id, target_id)
                if node.bad_score == 0:
                    good.append((aff, node))
                else:
                    bad.append((aff, node))

        good.sort(key=lambda x: x[0], reverse=True)
        bad.sort(key=lambda x: x[0], reverse=True)

        plist = PriorityList(max_len=good_count, target_id=target_id)
        for _, node in good[:good_count]:
            plist.add(node)
        for _, node in bad[:bad_count]:
            plist.add(node)

        return plist

    async def find_value(
        self,
        key: DhtKey,
        continuation: Continuation | None = None,
    ) -> DhtValue | None:
        """Perform iterative ``dht.findValue`` with 3 concurrent workers.

        Provider returns ``DhtValue | list[DhtNode] | None``, so
        this method works entirely with models — no TL.
        """
        if not self.connected:
            raise NotConnectedError(component="DhtNetwork", operation="find_value")

        target = key.key_id
        plist = self._build_priority_list(target)

        if continuation is not None:
            for checked in continuation.checked_nodes:
                plist.mark_used(checked, True)

        if len(plist) == 0:
            return None

        k = self._provider.k
        timeout = self._provider.request_timeout
        result_value: DhtValue | None = None
        checked_nodes: list[DhtNode] = []
        found = False
        cond = asyncio.Condition()
        waiting_count = 0
        worker_count = 3

        async def worker() -> None:
            nonlocal result_value, found, waiting_count

            while not found:
                async with cond:
                    node, _ = plist.get()
                    if node is None:
                        waiting_count += 1
                        if waiting_count >= worker_count:
                            cond.notify_all()
                            return
                        try:
                            await asyncio.wait_for(cond.wait(), timeout=timeout)
                        except asyncio.TimeoutError:
                            return
                        finally:
                            waiting_count -= 1
                        continue
                    checked_nodes.append(node)

                try:
                    result = await self._provider.find_value_on_node(node, target, k)
                except (OSError, ProviderError, TransportError, asyncio.TimeoutError):
                    continue

                if isinstance(result, DhtValue):
                    result_value = result
                    found = True
                    async with cond:
                        cond.notify_all()
                    return

                if isinstance(result, list):
                    added_any = False
                    async with cond:
                        for dht_node in result:
                            self._add_parsed_node(dht_node)
                            if plist.add(dht_node):
                                added_any = True
                        if added_any:
                            cond.notify_all()

        tasks = [asyncio.create_task(worker()) for _ in range(worker_count)]
        try:
            await asyncio.gather(*tasks, return_exceptions=True)
        finally:
            found = True
            for task in tasks:
                if not task.done():
                    task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)

        if continuation is not None:
            continuation.checked_nodes.extend(checked_nodes)

        return result_value

    async def store(
        self,
        value: dict[str, t.Any],
        target: bytes,
    ) -> int:
        """Store a value on K closest nodes.

        Go parity: ``checked`` set, rebuild plist each iteration,
        expansion via affinity comparison.
        """
        if not self.connected:
            raise NotConnectedError(component="DhtNetwork", operation="store")

        k = self._provider.k
        checked: set[str] = set()
        final = PriorityList(max_len=k, target_id=target)

        while True:
            plist = self._build_priority_list(target)

            nodes_to_query: list[DhtNode] = []
            while True:
                node, _ = plist.get()
                if node is None:
                    break
                if node.id in checked:
                    continue
                checked.add(node.id)
                nodes_to_query.append(node)

            if not nodes_to_query:
                break

            async def _query_one(
                n: DhtNode,
            ) -> tuple[DhtNode, list[dict[str, t.Any]] | None]:
                try:
                    r = await self._provider.find_nodes(n, target, k)
                    return n, r
                except Exception:
                    return n, None

            results = await asyncio.gather(
                *[_query_one(n) for n in nodes_to_query],
                return_exceptions=True,
            )

            expansion = False
            for result in results:
                if isinstance(result, BaseException) or not isinstance(result, tuple):
                    continue
                queried_node, nodes_list = result
                if nodes_list is not None:
                    final.add(queried_node)
                    for nd in nodes_list:
                        dht_node = self._add_node(nd)
                        if dht_node is not None:
                            best = final.get_best_affinity()
                            if affinity(dht_node.adnl_id, target) >= best:
                                expansion = True

            if not expansion:
                break

        store_tasks: list[t.Coroutine[t.Any, t.Any, bool]] = []
        seen: set[str] = set()

        while True:
            node, _ = final.get()
            if node is None:
                break
            if node.id in seen:
                continue
            seen.add(node.id)
            store_tasks.append(self._provider.store_value_on_node(node, value))

        if not store_tasks:
            return 0

        store_results = await asyncio.gather(*store_tasks, return_exceptions=True)
        return sum(1 for r in store_results if r is True)

    async def find_addresses(
        self,
        key: KeyLike,
    ) -> tuple[AdnlAddressListConfig, bytes]:
        """Resolve ADNL address to address list and public key."""
        raw_key = normalize_key(key)
        dht_key = DhtKey(id=raw_key, name=b"address", idx=0)
        dht_value = await self.find_value(dht_key)
        if dht_value is None:
            raise DhtValueNotFoundError(key=raw_key)
        addr_list = self._provider.codec.parse_address_list(dht_value.value)
        pub_key = dht_value.key_description.id_public_key
        return addr_list, pub_key

    async def find_overlay_nodes(
        self,
        overlay_key: KeyLike,
    ) -> DhtValue | None:
        """Find overlay nodes via DHT."""
        raw_key = normalize_key(overlay_key)
        key_hash = self._provider.codec.compute_overlay_key_hash(raw_key)
        dht_key = DhtKey(id=key_hash, name=b"nodes", idx=0)
        return await self.find_value(dht_key)

    async def store_address(
        self,
        address_list: dict[str, t.Any],
        ttl: int,
        owner_key: bytes,
    ) -> int:
        """Store ADNL address in the DHT."""
        if not self.connected:
            raise NotConnectedError(component="DhtNetwork", operation="store_address")
        value_tl, target = self._provider.codec.build_store_address(address_list, ttl, owner_key)
        return await self.store(value_tl, target)

    async def store_overlay_nodes(
        self,
        overlay_key: KeyLike,
        nodes_list: dict[str, t.Any],
        ttl: int,
    ) -> int:
        """Store overlay nodes list in the DHT."""
        if not self.connected:
            raise NotConnectedError(component="DhtNetwork", operation="store_overlay_nodes")
        raw_key = normalize_key(overlay_key)
        value_tl, target = self._provider.codec.build_store_overlay(raw_key, nodes_list, ttl)
        return await self.store(value_tl, target)
