import typing as t

from pytoniq_core import Address

from tonutils.contracts.base import BaseContract
from tonutils.contracts.nft.methods import (
    GetNFTDataGetMethod,
    GetEditorGetMethod,
    GetAuthorityAddressGetMethod,
    GetRevokedTimeGetMethod,
)
from tonutils.contracts.nft.tlb import (
    NFTItemEditableData,
    NFTItemSoulboundData,
    NFTItemStandardData,
    OffchainItemContent,
)
from tonutils.contracts.versions import ContractVersion

_D = t.TypeVar(
    "_D",
    bound=t.Union[
        NFTItemEditableData,
        NFTItemSoulboundData,
        NFTItemStandardData,
    ],
)
_C = t.TypeVar("_C", bound=OffchainItemContent)

_DStandard = t.TypeVar("_DStandard", bound=NFTItemStandardData)
_DEditable = t.TypeVar("_DEditable", bound=NFTItemEditableData)
_DSoulbound = t.TypeVar("_DSoulbound", bound=NFTItemSoulboundData)


class BaseNFTItem(
    BaseContract[_D],
    GetNFTDataGetMethod,
    t.Generic[_D, _C],
):
    _data_model: t.Type[_D]

    @property
    def state_data(self) -> _D:
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
    def content(self) -> _C:
        return self.state_data.content


class NFTItemStandard(BaseNFTItem[_DStandard, _C]):
    _data_model = NFTItemStandardData
    VERSION = ContractVersion.NFTItemStandard


class NFTItemEditable(
    BaseNFTItem[_DEditable, _C],
    GetEditorGetMethod,
):
    _data_model = NFTItemEditableData
    VERSION = ContractVersion.NFTItemEditable

    @property
    def editor_address(self) -> Address:
        return self.state_data.editor_address


class NFTItemSoulbound(
    BaseNFTItem[_DSoulbound, _C],
    GetAuthorityAddressGetMethod,
    GetRevokedTimeGetMethod,
):
    _data_model = NFTItemSoulboundData
    VERSION = ContractVersion.NFTItemSoulbound

    @property
    def authority_address(self) -> t.Optional[Address]:
        return self.state_data.authority_address

    @property
    def revoked_at(self) -> int:
        return self.state_data.revoked_at
