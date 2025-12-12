import typing as t

from pytoniq_core import Address, Cell

from tonutils.protocols.client import ClientProtocol
from tonutils.protocols.contract import ContractProtocol
from tonutils.types import AddressLike, Binary, PublicKey


async def seqno_get_method(
    client: ClientProtocol,
    address: AddressLike,
) -> int:
    """
    Get current sequence number from a wallet contract.

    :param client: TON client for blockchain interactions
    :param address: Wallet contract address
    :return: Current sequence number
    """
    r = await client.run_get_method(
        address=address,
        method_name="seqno",
    )
    return int(r[0])


class SeqnoGetMethod(ContractProtocol):
    """Mixin providing seqno() get method for wallet contracts."""

    async def seqno(self) -> int:
        """
        Get current sequence number of this wallet.

        Used for transaction ordering and replay protection.

        :return: Current sequence number
        """
        return await seqno_get_method(
            client=self.client,
            address=self.address,
        )


async def get_public_key_get_method(
    client: ClientProtocol,
    address: AddressLike,
) -> PublicKey:
    """
    Get public key from a wallet contract.

    :param client: TON client for blockchain interactions
    :param address: Wallet contract address
    :return: Ed25519 public key instance
    """
    r = await client.run_get_method(
        address=address,
        method_name="get_public_key",
    )
    return t.cast(PublicKey, PublicKey(r[0]))


class GetPublicKeyGetMethod(ContractProtocol):
    """Mixin providing get_public_key() get method for wallet contracts."""

    async def get_public_key(self) -> PublicKey:
        """
        Get public key of this wallet.

        :return: Ed25519 public key instance stored in wallet data
        """
        return await get_public_key_get_method(
            client=self.client,
            address=self.address,
        )


async def get_subwallet_id_get_method(
    client: ClientProtocol,
    address: AddressLike,
) -> int:
    """
    Get subwallet ID from a wallet contract.

    :param client: TON client for blockchain interactions
    :param address: Wallet contract address
    :return: Subwallet identifier
    """
    r = await client.run_get_method(
        address=address,
        method_name="get_subwallet_id",
    )
    return int(r[0])


class GetSubwalletIDGetMethod(ContractProtocol):
    """Mixin providing get_subwallet_id() get method for wallet contracts."""

    async def get_subwallet_id(self) -> int:
        """
        Get subwallet ID of this wallet.

        Used to isolate multiple wallets derived from the same keypair.

        :return: Subwallet identifier (typically 698983191 for default)
        """
        return await get_subwallet_id_get_method(
            client=self.client,
            address=self.address,
        )


async def is_plugin_installed_get_method(
    client: ClientProtocol,
    address: AddressLike,
    plugin_address: AddressLike,
) -> bool:
    """
    Check if a plugin is installed in a wallet contract.

    :param client: TON client for blockchain interactions
    :param address: Wallet contract address
    :param plugin_address: Plugin contract address to check
    :return: True if plugin is installed, False otherwise
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
    """Mixin providing is_plugin_installed() get method for v4/v5 wallets."""

    async def is_plugin_installed(
        self,
        plugin_address: AddressLike,
    ) -> bool:
        """
        Check if a plugin is installed in this wallet.

        :param plugin_address: Plugin contract address (Address or string)
        :return: True if plugin is installed, False otherwise
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
    """
    Get list of installed plugins from a wallet contract.

    :param client: TON client for blockchain interactions
    :param address: Wallet contract address
    :return: List of plugin data
    """
    return await client.run_get_method(
        address=address,
        method_name="get_plugin_list",
    )


class GetPluginListGetMethod(ContractProtocol):
    """Mixin providing get_plugin_list() get method for v4/v5 wallets."""

    async def get_plugin_list(self) -> t.List[t.Any]:
        """
        Get list of all installed plugins in this wallet.

        :return: List of plugin data (addresses and metadata)
        """
        return await get_plugin_list_get_method(
            client=self.client,
            address=self.address,
        )


async def is_signature_allowed_get_method(
    client: ClientProtocol,
    address: AddressLike,
) -> bool:
    """
    Check if signature authentication is allowed in a wallet contract.

    :param client: TON client for blockchain interactions
    :param address: Wallet contract address
    :return: True if signature authentication is enabled, False otherwise
    """
    r = await client.run_get_method(
        address=address,
        method_name="is_signature_allowed",
    )
    return bool(r[0])


class IsSignatureAllowedGetMethod(ContractProtocol):
    """Mixin providing is_signature_allowed() get method for v5 wallets."""

    async def is_signature_allowed(self) -> bool:
        """
        Check if signature authentication is allowed in this wallet.

        Wallet v5 feature allowing signature-based auth to be disabled.

        :return: True if signature authentication is enabled, False otherwise
        """
        return await is_signature_allowed_get_method(
            client=self.client,
            address=self.address,
        )


async def get_extensions_get_method(
    client: ClientProtocol,
    address: AddressLike,
) -> Cell:
    """
    Get extensions dictionary from a wallet contract.

    :param client: TON client for blockchain interactions
    :param address: Wallet contract address
    :return: Cell containing extensions dictionary
    """
    r = await client.run_get_method(
        address=address,
        method_name="get_extensions",
    )
    return t.cast(Cell, r[0])


class GetExtensionsGetMethod(ContractProtocol):
    """Mixin providing get_extensions() get method for v5 wallets."""

    async def get_extensions(self) -> Cell:
        """
        Get extensions dictionary from this wallet.

        Returns dictionary cell containing installed wallet extensions.

        :return: Cell containing extensions dictionary
        """
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
    """
    Check if a query has been processed by a highload wallet.

    :param client: TON client for blockchain interactions
    :param address: Highload wallet contract address
    :param query_id: Query identifier to check
    :param need_clean: Whether to clean old queries during check (optional)
    :return: True if query has been processed, False otherwise
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
    """Mixin providing processed() get method for highload wallets."""

    async def processed(
        self,
        query_id: int,
        need_clean: t.Optional[bool] = None,
    ) -> bool:
        """
        Check if a query has been processed by this highload wallet.

        Used for replay protection in highload wallets.

        :param query_id: Query identifier to check
        :param need_clean: Whether to clean old queries during check (optional)
        :return: True if query has been processed, False otherwise
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
    """
    Get last cleanup timestamp from a highload wallet.

    :param client: TON client for blockchain interactions
    :param address: Highload wallet contract address
    :return: Unix timestamp of last query cleanup
    """
    r = await client.run_get_method(
        address=address,
        method_name="get_last_clean_time",
    )
    return int(r[0])


class GetLastCleanTimeGetMethod(ContractProtocol):
    """Mixin providing get_last_clean_time() get method for highload v3 wallets."""

    async def get_last_clean_time(self) -> int:
        """
        Get last cleanup timestamp from this highload wallet.

        Returns when old queries were last cleaned from storage.

        :return: Unix timestamp of last query cleanup
        """
        return await get_last_clean_time_get_method(
            client=self.client,
            address=self.address,
        )


async def get_timeout_get_method(
    client: ClientProtocol,
    address: AddressLike,
) -> int:
    """
    Get query timeout from a highload wallet.

    :param client: TON client for blockchain interactions
    :param address: Highload wallet contract address
    :return: Query timeout in seconds
    """
    r = await client.run_get_method(
        address=address,
        method_name="get_timeout",
    )
    return int(r[0])


class GetTimeoutGetMethod(ContractProtocol):
    """Mixin providing get_timeout() get method for highload v3 wallets."""

    async def get_timeout(self) -> int:
        """
        Get query timeout from this highload wallet.

        Returns how long queries remain valid before expiration.

        :return: Query timeout in seconds (typically 300 seconds / 5 minutes)
        """
        return await get_timeout_get_method(
            client=self.client,
            address=self.address,
        )
