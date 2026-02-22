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
    """Base implementation for NFT item contracts."""

    _data_model: t.Type[_D]

    @property
    def state_data(self) -> _D:
        """Decoded on-chain NFT item state data."""
        return super().state_data

    @property
    def index(self) -> int:
        """Item index in the collection."""
        return self.state_data.index

    @property
    def owner_address(self) -> Address:
        """Current owner address."""
        return self.state_data.owner_address

    @property
    def collection_address(self) -> Address:
        """Parent collection address."""
        return self.state_data.collection_address

    @property
    def content(self) -> _C:
        """NFT item content metadata."""
        return self.state_data.content


class NFTItemStandard(BaseNFTItem[_DStandard, _C]):
    """Standard NFT item."""

    _data_model = NFTItemStandardData
    VERSION = ContractVersion.NFTItemStandard


class NFTItemEditable(
    BaseNFTItem[_DEditable, _C],
    GetEditorGetMethod,
):
    """Editable NFT item."""

    _data_model = NFTItemEditableData
    VERSION = ContractVersion.NFTItemEditable

    @property
    def editor_address(self) -> Address:
        """Address authorized to edit this NFT's content."""
        return self.state_data.editor_address


class NFTItemSoulbound(
    BaseNFTItem[_DSoulbound, _C],
    GetAuthorityAddressGetMethod,
    GetRevokedTimeGetMethod,
):
    """Soulbound NFT item (SBT)."""

    _data_model = NFTItemSoulboundData
    VERSION = ContractVersion.NFTItemSoulbound

    @property
    def authority_address(self) -> t.Optional[Address]:
        """Authority address that can revoke this SBT, or `None`."""
        return self.state_data.authority_address

    @property
    def revoked_at(self) -> int:
        """Revocation unix timestamp, or 0 if not revoked."""
        return self.state_data.revoked_at
