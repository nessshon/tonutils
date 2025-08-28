import typing as t

from pytoniq_core import Address, Cell

from ...protocols import ClientProtocol
from ...types import AddressLike, PublicKey


class WalletGetMethods:

    @classmethod
    async def get_public_key(
        cls,
        client: ClientProtocol,
        address: AddressLike,
    ) -> PublicKey:
        method_result = await client.run_get_method(
            address=address,
            method_name="get_public_key",
        )
        return PublicKey(method_result[0])

    @classmethod
    async def seqno(
        cls,
        client: ClientProtocol,
        address: AddressLike,
    ) -> int:
        method_result = await client.run_get_method(
            address=address,
            method_name="seqno",
        )
        return method_result[0]

    @classmethod
    async def get_subwallet_id(
        cls,
        client: ClientProtocol,
        address: AddressLike,
    ) -> int:
        method_result = await client.run_get_method(
            address=address,
            method_name="get_subwallet_id",
        )
        return method_result[0]

    @classmethod
    async def is_plugin_installed(
        cls,
        client: ClientProtocol,
        address: AddressLike,
        plugin_address: AddressLike,
    ) -> bool:
        if isinstance(plugin_address, str):
            plugin_address = Address(plugin_address)

        wc, hash_part = plugin_address.wc, int.from_bytes(
            plugin_address.hash_part,
            byteorder="big",
        )
        method_result = await client.run_get_method(
            address=address,
            method_name="is_plugin_installed",
            stack=[wc, hash_part],
        )
        return bool(method_result[0])

    @classmethod
    async def get_plugin_list(
        cls,
        client: ClientProtocol,
        address: AddressLike,
    ) -> t.List[Address]:
        method_result = await client.run_get_method(
            address=address,
            method_name="get_plugin_list",
        )
        return [Address((wc, hash_part)) for wc, hash_part in method_result[0]]

    @classmethod
    async def is_signature_allowed(
        cls,
        client: ClientProtocol,
        address: AddressLike,
    ) -> bool:
        method_result = await client.run_get_method(
            address=address,
            method_name="is_signature_allowed",
        )
        return bool(method_result[0])

    @classmethod
    async def get_extensions(
        cls,
        client: ClientProtocol,
        address: AddressLike,
    ) -> Cell:
        method_result = await client.run_get_method(
            address=address,
            method_name="get_extensions",
        )
        return method_result[0]

    @classmethod
    async def processed(
        cls,
        client: ClientProtocol,
        address: AddressLike,
        query_id: int,
        need_clean: t.Optional[bool] = None,
    ) -> bool:
        stack = [query_id]
        if need_clean is not None:
            stack.append(int(need_clean))

        method_result = await client.run_get_method(
            address=address,
            method_name="processed?",
            stack=stack,
        )
        return bool(method_result[0])

    @classmethod
    async def get_last_clean_time(
        cls,
        client: ClientProtocol,
        address: AddressLike,
    ) -> int:
        method_result = await client.run_get_method(
            address=address,
            method_name="get_last_clean_time",
        )
        return method_result[0]

    @classmethod
    async def get_timout(
        cls,
        client: ClientProtocol,
        address: AddressLike,
    ) -> int:
        method_result = await client.run_get_method(
            address=address,
            method_name="get_timeout",
        )
        return method_result[0]
