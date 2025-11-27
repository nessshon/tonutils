import typing as t

from pytoniq_core import Address, Cell

from tonutils.protocols.client import ClientProtocol
from tonutils.protocols.contract import ContractProtocol
from tonutils.types import AddressLike, Binary, PublicKey


async def seqno_get_method(
    client: ClientProtocol,
    address: AddressLike,
) -> int:
    r = await client.run_get_method(
        address=address,
        method_name="seqno",
    )
    return int(r[0])


class SeqnoGetMethod(ContractProtocol):
    async def seqno(self) -> int:
        return await seqno_get_method(
            client=self.client,
            address=self.address,
        )


async def get_public_key_get_method(
    client: ClientProtocol,
    address: AddressLike,
) -> PublicKey:
    r = await client.run_get_method(
        address=address,
        method_name="get_public_key",
    )
    return t.cast(PublicKey, PublicKey(r[0]))


class GetPublicKeyGetMethod(ContractProtocol):
    async def get_public_key(self) -> PublicKey:
        return await get_public_key_get_method(
            client=self.client,
            address=self.address,
        )


async def get_subwallet_id_get_method(
    client: ClientProtocol,
    address: AddressLike,
) -> int:
    r = await client.run_get_method(
        address=address,
        method_name="get_subwallet_id",
    )
    return int(r[0])


class GetSubwalletIDGetMethod(ContractProtocol):
    async def get_subwallet_id(self) -> int:
        return await get_subwallet_id_get_method(
            client=self.client,
            address=self.address,
        )


async def is_plugin_installed_get_method(
    client: ClientProtocol,
    address: AddressLike,
    plugin_address: AddressLike,
) -> bool:
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
    async def is_plugin_installed(
        self,
        plugin_address: AddressLike,
    ) -> bool:
        return await is_plugin_installed_get_method(
            client=self.client,
            address=self.address,
            plugin_address=plugin_address,
        )


async def get_plugin_list_get_method(
    client: ClientProtocol,
    address: AddressLike,
) -> t.List[t.Any]:
    return await client.run_get_method(
        address=address,
        method_name="get_plugin_list",
    )


class GetPluginListGetMethod(ContractProtocol):
    async def get_plugin_list(self) -> t.List[t.Any]:
        return await get_plugin_list_get_method(
            client=self.client,
            address=self.address,
        )


async def is_signature_allowed_get_method(
    client: ClientProtocol,
    address: AddressLike,
) -> bool:
    r = await client.run_get_method(
        address=address,
        method_name="is_signature_allowed",
    )
    return bool(r[0])


class IsSignatureAllowedGetMethod(ContractProtocol):
    async def is_signature_allowed(self) -> bool:
        return await is_signature_allowed_get_method(
            client=self.client,
            address=self.address,
        )


async def get_extensions_get_method(
    client: ClientProtocol,
    address: AddressLike,
) -> Cell:
    r = await client.run_get_method(
        address=address,
        method_name="get_extensions",
    )
    return t.cast(Cell, r[0])


class GetExtensionsGetMethod(ContractProtocol):
    async def get_extensions(self) -> Cell:
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
    async def processed(
        self,
        query_id: int,
        need_clean: t.Optional[bool] = None,
    ) -> bool:
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
    r = await client.run_get_method(
        address=address,
        method_name="get_last_clean_time",
    )
    return int(r[0])


class GetLastCleanTimeGetMethod(ContractProtocol):
    async def get_last_clean_time(self) -> int:
        return await get_last_clean_time_get_method(
            client=self.client,
            address=self.address,
        )


async def get_timeout_get_method(
    client: ClientProtocol,
    address: AddressLike,
) -> int:
    r = await client.run_get_method(
        address=address,
        method_name="get_timeout",
    )
    return int(r[0])


class GetTimeoutGetMethod(ContractProtocol):
    async def get_timeout(self) -> int:
        return await get_timeout_get_method(
            client=self.client,
            address=self.address,
        )
