from __future__ import annotations

import asyncio
import typing as t
from contextlib import suppress

from ton_core import (
    AdnlAddressConfig,
    AdnlAddressListConfig,
    BinaryLike,
    DhtNodeConfig,
    GlobalConfig,
    NetworkGlobalID,
    get_mainnet_global_config,
    get_testnet_global_config,
    load_global_config,
)

from tonutils.clients.dht.models import (
    DhtKey,
    DhtNode,
    DhtValue,
    KeyLike,
    compute_key_id,
    normalize_key,
    normalize_pub_key,
)
from tonutils.exceptions import ClientError, NotConnectedError

if t.TYPE_CHECKING:
    from tonutils.providers.dht import DhtProvider


class DhtClient:
    """Single DHT node client for direct operations.

    For iterative Kademlia lookups across multiple nodes, use ``DhtNetwork``.
    """

    def __init__(
        self,
        *,
        host: str,
        port: int,
        public_key: BinaryLike,
        connect_timeout: float = 5.0,
        request_timeout: float = 3.0,
    ) -> None:
        pub_key = normalize_pub_key(public_key)
        adnl_id = compute_key_id(pub_key)

        config_node = DhtNodeConfig(
            id=pub_key.hex(),
            addr_list=AdnlAddressListConfig(
                addrs=[AdnlAddressConfig(ip=host, port=port)],
            ),
            version=0,
            signature="",
        )
        from tonutils.providers.dht import DhtProvider

        self._provider = DhtProvider(
            nodes=[config_node],
            k=7,
            connect_timeout=connect_timeout,
            request_timeout=request_timeout,
        )
        self._node: DhtNode | None = None
        self._adnl_id = adnl_id
        self._host = host
        self._port = port
        self._pub_key = pub_key

    @property
    def provider(self) -> DhtProvider:
        """Underlying DHT provider."""
        return self._provider

    @property
    def connected(self) -> bool:
        """Whether the client is connected to the DHT node."""
        return self._node is not None and self._provider.transport.bound

    @property
    def host(self) -> str:
        """Remote node IP address."""
        return self._host

    @property
    def port(self) -> int:
        """Remote node port."""
        return self._port

    @property
    def adnl_id(self) -> bytes:
        """ADNL identifier of the remote node."""
        return self._adnl_id

    @property
    def node(self) -> DhtNode | None:
        """Connected DHT node descriptor, or ``None`` if not connected."""
        return self._node

    @classmethod
    def from_config(
        cls,
        *,
        config: GlobalConfig | dict[str, t.Any] | str,
        index: int,
        connect_timeout: float = 5.0,
        request_timeout: float = 3.0,
    ) -> DhtClient:
        """Create a client from a global config and a node index."""
        if isinstance(config, str):
            config = load_global_config(config)
        if isinstance(config, dict):
            config = GlobalConfig.from_dict(config)
        if config.dht is None:
            raise ClientError("DhtClient.from_config: no DHT section in config")
        nodes = config.dht.nodes
        if not 0 <= index < len(nodes):
            raise ClientError(
                f"DhtClient.from_config: node index {index} out of range (0..{len(nodes) - 1})."
            )
        node = nodes[index]
        return cls(
            host=node.host,
            port=node.port,
            public_key=node.pub_key,
            connect_timeout=connect_timeout,
            request_timeout=request_timeout,
        )

    @classmethod
    def from_network_config(
        cls,
        network: NetworkGlobalID = NetworkGlobalID.MAINNET,
        *,
        index: int,
        connect_timeout: float = 5.0,
        request_timeout: float = 3.0,
    ) -> DhtClient:
        """Create a client from a built-in mainnet/testnet config."""
        config_getters = {
            NetworkGlobalID.MAINNET: get_mainnet_global_config,
            NetworkGlobalID.TESTNET: get_testnet_global_config,
        }
        config = config_getters[network]()
        return cls.from_config(
            config=config,
            index=index,
            connect_timeout=connect_timeout,
            request_timeout=request_timeout,
        )

    async def connect(self) -> None:
        """Open an ADNL channel to the remote DHT node."""
        if self._node is not None:
            return
        await self._provider.bind()
        dht_node = DhtNode(
            adnl_id=self._adnl_id,
            addr=f"{self._host}:{self._port}",
            server_key=self._pub_key,
        )
        await self._provider.ensure_channel(dht_node)
        self._node = dht_node

    async def close(self) -> None:
        """Close the connection and release resources."""
        self._node = None
        await self._provider.close()

    async def __aenter__(self) -> DhtClient:
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

    def _require_connected(self, operation: str) -> DhtNode:
        if self._node is None or not self.connected:
            raise NotConnectedError(component="DhtClient", operation=operation)
        return self._node

    async def ping(self) -> float:
        """Ping and return RTT in seconds."""
        node = self._require_connected("ping")
        loop = asyncio.get_running_loop()
        start = loop.time()
        await self._provider.ping_node(node)
        return loop.time() - start

    async def find_nodes(self, target: KeyLike, k: int = 7) -> list[dict[str, t.Any]]:
        """Ask this node for nodes closest to a target.

        :return: List of raw ``dht.node`` TL dicts.
        """
        node = self._require_connected("find_nodes")
        return await self._provider.find_nodes(node, normalize_key(target), k)

    async def find_value(self, key: DhtKey) -> DhtValue | list[DhtNode] | None:
        """Single-node, non-iterative find_value."""
        node = self._require_connected("find_value")
        return await self._provider.find_value_on_node(
            node, key.key_id, self._provider.k
        )

    async def get_signed_address_list(self) -> dict[str, t.Any]:
        """Retrieve the signed address list from the node."""
        node = self._require_connected("get_signed_address_list")
        return await self._provider.get_signed_address_list(node)

    async def store(self, value: dict[str, t.Any]) -> bool:
        """Store a DHT value on the node."""
        node = self._require_connected("store")
        return await self._provider.store_value_on_node(node, value)
