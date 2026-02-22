import typing as t

from pytoniq_core import Address, Cell

from tonutils.clients.protocol import ClientProtocol
from tonutils.contracts.protocol import ContractProtocol
from tonutils.types import AddressLike, Binary, PublicKey


async def seqno_get_method(
    client: ClientProtocol,
    address: AddressLike,
) -> int:
    """Call `seqno` on a wallet contract.

    :param client: TON client.
    :param address: Wallet contract address.
    :return: Current sequence number.
    """
    r = await client.run_get_method(
        address=address,
        method_name="seqno",
    )
    return int(r[0])


class SeqnoGetMethod(ContractProtocol):
    """Mixin for the `seqno` get-method."""

    async def seqno(self) -> int:
        """Return current sequence number."""
        return await seqno_get_method(
            client=self.client,
            address=self.address,
        )


async def get_public_key_get_method(
    client: ClientProtocol,
    address: AddressLike,
) -> PublicKey:
    """Call `get_public_key` on a wallet contract.

    :param client: TON client.
    :param address: Wallet contract address.
    :return: Ed25519 public key.
    """
    r = await client.run_get_method(
        address=address,
        method_name="get_public_key",
    )
    return t.cast(PublicKey, PublicKey(r[0]))


class GetPublicKeyGetMethod(ContractProtocol):
    """Mixin for the `get_public_key` get-method."""

    async def get_public_key(self) -> PublicKey:
        """Return Ed25519 public key stored in wallet data."""
        return await get_public_key_get_method(
            client=self.client,
            address=self.address,
        )


async def get_subwallet_id_get_method(
    client: ClientProtocol,
    address: AddressLike,
) -> int:
    """Call `get_subwallet_id` on a wallet contract.

    :param client: TON client.
    :param address: Wallet contract address.
    :return: Subwallet identifier.
    """
    r = await client.run_get_method(
        address=address,
        method_name="get_subwallet_id",
    )
    return int(r[0])


class GetSubwalletIDGetMethod(ContractProtocol):
    """Mixin for the `get_subwallet_id` get-method."""

    async def get_subwallet_id(self) -> int:
        """Return subwallet identifier."""
        return await get_subwallet_id_get_method(
            client=self.client,
            address=self.address,
        )


async def is_plugin_installed_get_method(
    client: ClientProtocol,
    address: AddressLike,
    plugin_address: AddressLike,
) -> bool:
    """Call `is_plugin_installed` on a wallet contract.

    :param client: TON client.
    :param address: Wallet contract address.
    :param plugin_address: Plugin contract address to check.
    :return: `True` if the plugin is installed.
    """
    if isinstance(plugin_address, str):
        plugin_address = Address(plugin_address)

    wc = plugin_address.wc
    hash_part = Binary(plugin_address.hash_part).as_int

    r = await client.run_get_method(
        address=address,
        method_name="is_plugin_installed",
        stack=[wc, hash_part],
    )
    return bool(r[0])


class IsPluginInstalledGetMethod(ContractProtocol):
    """Mixin for the `is_plugin_installed` get-method."""

    async def is_plugin_installed(
        self,
        plugin_address: AddressLike,
    ) -> bool:
        """Check whether a plugin is installed.

        :param plugin_address: Plugin contract address.
        :return: `True` if the plugin is installed.
        """
        return await is_plugin_installed_get_method(
            client=self.client,
            address=self.address,
            plugin_address=plugin_address,
        )


async def get_plugin_list_get_method(
    client: ClientProtocol,
    address: AddressLike,
) -> t.List[t.Any]:
    """Call `get_plugin_list` on a wallet contract.

    :param client: TON client.
    :param address: Wallet contract address.
    :return: List of plugin data.
    """
    return await client.run_get_method(
        address=address,
        method_name="get_plugin_list",
    )


class GetPluginListGetMethod(ContractProtocol):
    """Mixin for the `get_plugin_list` get-method."""

    async def get_plugin_list(self) -> t.List[t.Any]:
        """Return list of installed plugins."""
        return await get_plugin_list_get_method(
            client=self.client,
            address=self.address,
        )


async def is_signature_allowed_get_method(
    client: ClientProtocol,
    address: AddressLike,
) -> bool:
    """Call `is_signature_allowed` on a wallet contract.

    :param client: TON client.
    :param address: Wallet contract address.
    :return: `True` if signature authentication is enabled.
    """
    r = await client.run_get_method(
        address=address,
        method_name="is_signature_allowed",
    )
    return bool(r[0])


class IsSignatureAllowedGetMethod(ContractProtocol):
    """Mixin for the `is_signature_allowed` get-method."""

    async def is_signature_allowed(self) -> bool:
        """Return whether signature authentication is enabled."""
        return await is_signature_allowed_get_method(
            client=self.client,
            address=self.address,
        )


async def get_extensions_get_method(
    client: ClientProtocol,
    address: AddressLike,
) -> Cell:
    """Call `get_extensions` on a wallet contract.

    :param client: TON client.
    :param address: Wallet contract address.
    :return: Extensions dictionary `Cell`.
    """
    r = await client.run_get_method(
        address=address,
        method_name="get_extensions",
    )
    return t.cast(Cell, r[0])


class GetExtensionsGetMethod(ContractProtocol):
    """Mixin for the `get_extensions` get-method."""

    async def get_extensions(self) -> Cell:
        """Return extensions dictionary `Cell`."""
        return await get_extensions_get_method(
            client=self.client,
            address=self.address,
        )


async def processed_get_method(
    client: ClientProtocol,
    address: AddressLike,
    query_id: int,
    need_clean: t.Optional[bool] = None,
) -> bool:
    """Call `processed?` on a highload wallet contract.

    :param client: TON client.
    :param address: Highload wallet address.
    :param query_id: Query identifier to check.
    :param need_clean: Clean old queries during check, or `None`.
    :return: `True` if the query has been processed.
    """
    stack: t.List[t.Any] = [query_id]
    if need_clean is not None:
        stack.append(int(need_clean))

    r = await client.run_get_method(
        address=address,
        method_name="processed?",
        stack=stack,
    )
    return bool(r[0])


class ProcessedGetMethod(ContractProtocol):
    """Mixin for the `processed?` get-method."""

    async def processed(
        self,
        query_id: int,
        need_clean: t.Optional[bool] = None,
    ) -> bool:
        """Check whether a query has been processed.

        :param query_id: Query identifier to check.
        :param need_clean: Clean old queries during check, or `None`.
        :return: `True` if the query has been processed.
        """
        return await processed_get_method(
            client=self.client,
            address=self.address,
            query_id=query_id,
            need_clean=need_clean,
        )


async def get_last_clean_time_get_method(
    client: ClientProtocol,
    address: AddressLike,
) -> int:
    """Call `get_last_clean_time` on a highload wallet contract.

    :param client: TON client.
    :param address: Highload wallet address.
    :return: Unix timestamp of last query cleanup.
    """
    r = await client.run_get_method(
        address=address,
        method_name="get_last_clean_time",
    )
    return int(r[0])


class GetLastCleanTimeGetMethod(ContractProtocol):
    """Mixin for the `get_last_clean_time` get-method."""

    async def get_last_clean_time(self) -> int:
        """Return unix timestamp of last query cleanup."""
        return await get_last_clean_time_get_method(
            client=self.client,
            address=self.address,
        )


async def get_timeout_get_method(
    client: ClientProtocol,
    address: AddressLike,
) -> int:
    """Call `get_timeout` on a highload wallet contract.

    :param client: TON client.
    :param address: Highload wallet address.
    :return: Query timeout in seconds.
    """
    r = await client.run_get_method(
        address=address,
        method_name="get_timeout",
    )
    return int(r[0])


class GetTimeoutGetMethod(ContractProtocol):
    """Mixin for the `get_timeout` get-method."""

    async def get_timeout(self) -> int:
        """Return query timeout in seconds."""
        return await get_timeout_get_method(
            client=self.client,
            address=self.address,
        )
