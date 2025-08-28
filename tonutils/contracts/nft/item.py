import abc
import typing as t

from pytoniq_core import Address, Slice

from .get_methods import NFTItemGetMethods
from ..base import BaseContract
from ...types import (
    NFTItemEditableData,
    NFTItemSoulboundData,
    NFTItemStandardData,
    NFTItemVersion,
    OffchainItemContent,
)

D = t.TypeVar(
    "D",
    bound=t.Union[
        NFTItemEditableData,
        NFTItemSoulboundData,
        NFTItemStandardData,
    ],
)
C = t.TypeVar("C", bound=OffchainItemContent)

DStandard = t.TypeVar("DStandard", bound=NFTItemStandardData)
DEditable = t.TypeVar("DEditable", bound=NFTItemEditableData)
DSoulbound = t.TypeVar("DSoulbound", bound=NFTItemSoulboundData)


class BaseNFTItem(BaseContract[D], t.Generic[D, C], abc.ABC):
    _data_model: t.Type[D]

    @property
    def state_data(self) -> D:
        return super().state_data

    @property
    def index(self) -> int:
        return self.state_data.index

    @property
    def owner_address(self) -> Address:
        return self.state_data.owner_address

    @property
    def collection_address(self) -> Address:
        return self.state_data.collection_address

    @property
    def content(self) -> C:
        return self.state_data.content

    async def get_nft_data(
        self,
    ) -> t.Tuple[
        bool,
        int,
        t.Optional[Address],
        t.Optional[Address],
        OffchainItemContent,
    ]:
        method_result = await NFTItemGetMethods.get_nft_data(
            client=self.client,
            address=self.address,
        )
        content_cs: Slice = method_result[4].begin_parse()
        return (
            bool(method_result[0]),
            method_result[1],
            method_result[2],
            method_result[3],
            OffchainItemContent.deserialize(content_cs),
        )


class NFTItemStandard(BaseNFTItem[DStandard, C]):
    _data_model = NFTItemStandardData
    VERSION = NFTItemVersion.NFTItemStandard


class NFTItemEditable(BaseNFTItem[DEditable, C]):
    _data_model = NFTItemEditableData
    VERSION = NFTItemVersion.NFTItemStandard

    @property
    def editor_address(self) -> Address:
        return self.state_data.editor_address

    async def get_editor_address(self) -> t.Optional[Address]:
        return await NFTItemGetMethods.get_editor(
            client=self.client,
            address=self.address,
        )


class NFTItemSoulbound(BaseNFTItem[DSoulbound, C]):
    _data_model = NFTItemSoulboundData
    VERSION = NFTItemVersion.NFTItemStandard

    @property
    def authority_address(self) -> t.Optional[Address]:
        return self.state_data.authority_address

    @property
    def revoked_at(self) -> int:
        return self.state_data.revoked_at

    async def get_authority_address(self) -> t.Optional[Address]:
        return await NFTItemGetMethods.get_authority_address(
            client=self.client,
            address=self.address,
        )

    async def get_revoked_time(self) -> int:
        return await NFTItemGetMethods.get_revoked_time(
            client=self.client,
            address=self.address,
        )
