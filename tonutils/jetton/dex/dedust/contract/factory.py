from typing import List

from pytoniq_core import Cell, begin_cell, Address, Slice

from .asset import Asset
from .pool import PoolType, Pool
from .vault import VaultJetton, VaultNative
from ..op_codes import *
from .....client import Client, TonapiClient, ToncenterClient, LiteClient
from .....exceptions import UnknownClientError
from .....utils import boc_to_base64_string


class Factory:
    ADDRESS = "EQBfBWT7X2BHg9tXAxzhz2aKiNTU1tpt5NsiK0uSDW_YAJ67"  # noqa

    def __init__(self, client: Client) -> None:
        self.client = client

    @staticmethod
    def create_vault_payload(
            asset: Asset,
            query_id: int = 0
    ) -> Cell:
        return (
            begin_cell()
            .store_uint(CREATE_VAULT_OPCODE, 32)
            .store_uint(query_id, 64)
            .store_slice(asset.to_slice())
            .end_cell()
        )

    @classmethod
    async def get_vault_address(
            cls,
            client: Client,
            asset: Asset,
    ) -> Address:
        if isinstance(client, TonapiClient):
            method_result = await client.run_get_method(
                address=cls.ADDRESS,
                method_name="get_vault_address",
                stack=[asset.to_boc().hex()],
            )
            address = Slice.one_from_boc(method_result["stack"][0]["cell"]).load_address()
        elif isinstance(client, ToncenterClient):
            method_result = await client.run_get_method(
                address=cls.ADDRESS,
                method_name="get_vault_address",
                stack=[boc_to_base64_string(asset.to_boc())],
            )
            address = Slice.one_from_boc(method_result["stack"][0]["value"]).load_address()
        elif isinstance(client, LiteClient):
            method_result = await client.run_get_method(
                address=cls.ADDRESS,
                method_name="get_vault_address",
                stack=[asset.to_slice()],
            )
            address = method_result[0].load_address()
        else:
            raise UnknownClientError(client.__class__.__name__)

        return address

    async def get_native_vault(self) -> VaultNative:
        native_vault_address = await self.get_vault_address(self.client, Asset.native())

        return VaultNative(native_vault_address)

    async def get_jetton_vault(self, jetton_address: str) -> VaultJetton:
        jetton_vault_address = await self.get_vault_address(self.client, Asset.jetton(jetton_address))

        return VaultJetton(jetton_vault_address)

    @classmethod
    async def get_pool_address(
            cls,
            client: Client,
            pool_type: PoolType,
            assets: List[Asset],
    ) -> Address:
        if isinstance(client, TonapiClient):
            method_result = await client.run_get_method(
                address=cls.ADDRESS,
                method_name="get_pool_address",
                stack=[
                    assets[0].to_boc().hex(),
                    assets[1].to_boc().hex(),
                    pool_type.value,
                ]
            )
            address = Address(method_result["decoded"].get("pool_address"))
        elif isinstance(client, ToncenterClient):
            method_result = await client.run_get_method(
                address=cls.ADDRESS,
                method_name="get_pool_address",
                stack=[
                    pool_type.value,
                    boc_to_base64_string(assets[0].to_boc()),
                    boc_to_base64_string(assets[1].to_boc()),
                ]
            )
            address = Slice.one_from_boc(method_result["stack"][0]["value"]).load_address()
        elif isinstance(client, LiteClient):
            method_result = await client.run_get_method(
                address=cls.ADDRESS,
                method_name="get_pool_address",
                stack=[
                    pool_type.value,
                    assets[0].to_slice(),
                    assets[1].to_slice(),
                ]
            )
            address = method_result[0].load_address()
        else:
            raise UnknownClientError(client.__class__.__name__)

        return address

    async def get_pool(self, pool_type: PoolType, assets: List[Asset]) -> Pool:
        pool_address = await self.get_pool_address(self.client, pool_type, assets)

        return Pool(pool_address)
