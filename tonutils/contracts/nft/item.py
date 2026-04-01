import typing as t

from ton_core import (
    Address,
    ContractVersion,
    NFTItemEditableData,
    NFTItemSoulboundData,
    NFTItemStandardData,
    OffchainItemContent,
)

from tonutils.contracts.base import BaseContract
from tonutils.contracts.nft.methods import (
    GetAuthorityAddressGetMethod,
    GetEditorGetMethod,
    GetNFTDataGetMethod,
    GetRevokedTimeGetMethod,
)

_D = t.TypeVar(
    "_D",
    bound=NFTItemEditableData | NFTItemSoulboundData | NFTItemStandardData,
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
    """Base NFT item contract (TEP-62)."""

    _data_model: type[_D]

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
        return t.cast("Address", self.state_data.owner_address)

    @property
    def collection_address(self) -> Address:
        """Parent collection address."""
        return t.cast("Address", self.state_data.collection_address)

    @property
    def content(self) -> _C:
        """NFT item content metadata."""
        return t.cast("_C", self.state_data.content)


class NFTItemStandard(BaseNFTItem[_DStandard, _C]):
    """Standard transferable NFT item (TEP-62)."""

    _data_model: type[_DStandard] = NFTItemStandardData  # type: ignore[assignment]
    VERSION = ContractVersion.NFTItemStandard


class NFTItemEditable(
    BaseNFTItem[_DEditable, _C],
    GetEditorGetMethod,
):
    """Editable NFT item with mutable content (TEP-62)."""

    _data_model: type[_DEditable] = NFTItemEditableData  # type: ignore[assignment]
    VERSION = ContractVersion.NFTItemEditable

    @property
    def editor_address(self) -> Address:
        """Address authorized to edit this NFT's content."""
        return t.cast("Address", self.state_data.editor_address)


class NFTItemSoulbound(
    BaseNFTItem[_DSoulbound, _C],
    GetAuthorityAddressGetMethod,
    GetRevokedTimeGetMethod,
):
    """Non-transferable Soulbound Token (TEP-85)."""

    _data_model: type[_DSoulbound] = NFTItemSoulboundData  # type: ignore[assignment]
    VERSION = ContractVersion.NFTItemSoulbound

    @property
    def authority_address(self) -> Address | None:
        """Authority address that can revoke this SBT, or ``None``."""
        return t.cast("Address | None", self.state_data.authority_address)

    @property
    def revoked_at(self) -> int:
        """Revocation unix timestamp, or 0 if not revoked."""
        return self.state_data.revoked_at
