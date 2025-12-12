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
    """TlbScheme class for deserializing item state data."""

    @property
    def state_data(self) -> _D:
        """
        Decoded on-chain NFT item state data.

        :return: Typed item data
        """
        return super().state_data

    @property
    def index(self) -> int:
        """
        Numerical index of this item in the collection.

        :return: Item index
        """
        return self.state_data.index

    @property
    def owner_address(self) -> Address:
        """
        Current owner address of this NFT item.

        :return: Owner's wallet address
        """
        return self.state_data.owner_address

    @property
    def collection_address(self) -> Address:
        """
        Collection address this item belongs to.

        :return: Parent collection address
        """
        return self.state_data.collection_address

    @property
    def content(self) -> _C:
        """
        NFT item content metadata.

        :return: Item content (offchain or onchain)
        """
        return self.state_data.content


class NFTItemStandard(BaseNFTItem[_DStandard, _C]):
    """Standard NFT item contract."""

    _data_model = NFTItemStandardData
    """TlbScheme class for deserializing item state data."""

    VERSION = ContractVersion.NFTItemStandard
    """Contract version identifier."""


class NFTItemEditable(
    BaseNFTItem[_DEditable, _C],
    GetEditorGetMethod,
):
    """Editable NFT item contract."""

    _data_model = NFTItemEditableData
    """TlbScheme class for deserializing item state data."""

    VERSION = ContractVersion.NFTItemEditable
    """Contract version identifier."""

    @property
    def editor_address(self) -> Address:
        """
        Address authorized to edit this NFT's content.

        :return: Editor's wallet address
        """
        return self.state_data.editor_address


class NFTItemSoulbound(
    BaseNFTItem[_DSoulbound, _C],
    GetAuthorityAddressGetMethod,
    GetRevokedTimeGetMethod,
):
    """Soulbound NFT item contract (SBT)."""

    _data_model = NFTItemSoulboundData
    """TlbScheme class for deserializing item state data."""

    VERSION = ContractVersion.NFTItemSoulbound
    """Contract version identifier."""

    @property
    def authority_address(self) -> t.Optional[Address]:
        """
        Authority address that can revoke this SBT.

        :return: Authority address or None if no authority set
        """
        return self.state_data.authority_address

    @property
    def revoked_at(self) -> int:
        """
        Unix timestamp when this SBT was revoked.

        :return: Revocation timestamp, 0 if not revoked
        """
        return self.state_data.revoked_at
