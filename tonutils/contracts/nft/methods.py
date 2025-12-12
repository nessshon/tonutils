import typing as t

from pytoniq_core import Address, Cell

from tonutils.protocols.client import ClientProtocol
from tonutils.protocols.contract import ContractProtocol
from tonutils.types import AddressLike


async def get_collection_data_get_method(
    client: ClientProtocol,
    address: AddressLike,
) -> t.List[t.Any]:
    """
    Get collection data from an NFT collection contract.

    :param client: TON client for blockchain interactions
    :param address: NFT collection contract address
    :return: List containing next_item_index, collection_content, and owner_address
    """
    return await client.run_get_method(
        address=address,
        method_name="get_collection_data",
    )


class GetCollectionDataGetMethod(ContractProtocol):
    """Mixin providing get_collection_data() get method for NFT collections."""

    async def get_collection_data(self) -> t.List[t.Any]:
        """
        Get collection data from this NFT collection.

        Returns next item index, collection content, and owner address.

        :return: List containing next_item_index, collection_content, and owner_address
        """
        return await get_collection_data_get_method(
            client=self.client,
            address=self.address,
        )


async def get_nft_address_by_index_get_method(
    client: ClientProtocol,
    address: AddressLike,
    index: int,
) -> Address:
    """
    Get NFT item address by its index in the collection.

    :param client: TON client for blockchain interactions
    :param address: NFT collection contract address
    :param index: Numerical index of the NFT item in the collection
    :return: Address of the NFT item contract
    """
    r = await client.run_get_method(
        address=address,
        method_name="get_nft_address_by_index",
        stack=[index],
    )
    return t.cast(Address, r[0])


class GetNFTAddressByIndexGetMethod(ContractProtocol):
    """Mixin providing get_nft_address_by_index() get method for NFT collections."""

    async def get_nft_address_by_index(
        self,
        index: int,
    ) -> Address:
        """
        Get NFT item address by its index in this collection.

        :param index: Numerical index of the NFT item
        :return: Address of the NFT item contract
        """
        return await get_nft_address_by_index_get_method(
            client=self.client,
            address=self.address,
            index=index,
        )


async def royalty_params_get_method(
    client: ClientProtocol,
    address: AddressLike,
) -> t.List[t.Any]:
    """
    Get royalty parameters from an NFT collection contract.

    :param client: TON client for blockchain interactions
    :param address: NFT collection contract address
    :return: List containing numerator, denominator, and destination address
    """
    return await client.run_get_method(
        address=address,
        method_name="royalty_params",
    )


class RoyaltyParamsGetMethod(ContractProtocol):
    """Mixin providing royalty_params() get method for NFT collections."""

    async def royalty_params(self) -> t.List[t.Any]:
        """
        Get royalty parameters from this NFT collection.

        Returns numerator, denominator, and destination address for royalty calculations.

        :return: List containing numerator, denominator, and destination address
        """
        return await royalty_params_get_method(
            client=self.client,
            address=self.address,
        )


async def get_nft_content_get_method(
    client: ClientProtocol,
    address: AddressLike,
    index: int,
    individual_nft_content: Cell,
) -> Cell:
    """
    Get full NFT content by combining collection and individual content.

    :param client: TON client for blockchain interactions
    :param address: NFT collection contract address
    :param index: Numerical index of the NFT item
    :param individual_nft_content: Individual NFT content cell from the item
    :return: Cell containing full NFT metadata
    """
    r = await client.run_get_method(
        address=address,
        method_name="get_nft_content",
        stack=[index, individual_nft_content],
    )
    return t.cast(Cell, r[0])


class GetNFTContentGetMethod(ContractProtocol):
    """Mixin providing get_nft_content() get method for NFT collections."""

    async def get_nft_content(
        self,
        index: int,
        individual_nft_content: Cell,
    ) -> Cell:
        """
        Get full NFT content by combining collection and individual content.

        :param index: Numerical index of the NFT item
        :param individual_nft_content: Individual NFT content cell from the item
        :return: Cell containing full NFT metadata
        """
        return await get_nft_content_get_method(
            client=self.client,
            address=self.address,
            index=index,
            individual_nft_content=individual_nft_content,
        )


async def get_second_owner_address_get_method(
    client: ClientProtocol,
    address: AddressLike,
) -> Address:
    """
    Get second owner address from an NFT contract.

    :param client: TON client for blockchain interactions
    :param address: NFT contract address
    :return: Address of the second owner
    """
    r = await client.run_get_method(
        address=address,
        method_name="get_second_owner_address",
    )
    return t.cast(Address, r[0])


class GetSecondOwnerAddressGetMethod(ContractProtocol):
    """Mixin providing get_second_owner_address() get method for NFT contracts."""

    async def get_second_owner_address(self) -> Address:
        """
        Get second owner address from this NFT contract.

        :return: Address of the second owner
        """
        return await get_second_owner_address_get_method(
            client=self.client,
            address=self.address,
        )


async def get_nft_data_get_method(
    client: ClientProtocol,
    address: AddressLike,
) -> t.List[t.Any]:
    """
    Get NFT item data from an NFT item contract.

    :param client: TON client for blockchain interactions
    :param address: NFT item contract address
    :return: List containing init flag, index, collection_address, owner_address, and individual_content
    """
    return await client.run_get_method(
        address=address,
        method_name="get_nft_data",
    )


class GetNFTDataGetMethod(ContractProtocol):
    """Mixin providing get_nft_data() get method for NFT items."""

    async def get_nft_data(self) -> t.List[t.Any]:
        """
        Get NFT item data from this NFT item.

        Returns initialization status, index, collection address, owner address, and content.

        :return: List containing init flag, index, collection_address, owner_address, and individual_content
        """
        return await get_nft_data_get_method(
            client=self.client,
            address=self.address,
        )


async def get_editor_get_method(
    client: ClientProtocol,
    address: AddressLike,
) -> t.Optional[Address]:
    """
    Get editor address from an NFT contract.

    :param client: TON client for blockchain interactions
    :param address: NFT contract address
    :return: Editor address if set, None otherwise
    """
    r = await client.run_get_method(
        address=address,
        method_name="get_editor",
    )
    return t.cast(t.Optional[Address], r[0])


class GetEditorGetMethod(ContractProtocol):
    """Mixin providing get_editor() get method for editable NFT contracts."""

    async def get_editor(self) -> t.Optional[Address]:
        """
        Get editor address from this NFT contract.

        :return: Editor address if set, None otherwise
        """
        return await get_editor_get_method(
            client=self.client,
            address=self.address,
        )


async def get_authority_address_get_method(
    client: ClientProtocol,
    address: AddressLike,
) -> t.Optional[Address]:
    """
    Get authority address from an SBT contract.

    :param client: TON client for blockchain interactions
    :param address: SBT contract address
    :return: Authority address that can revoke the SBT, None if no authority
    """
    r = await client.run_get_method(
        address=address,
        method_name="get_authority_address",
    )
    return t.cast(t.Optional[Address], r[0])


class GetAuthorityAddressGetMethod(ContractProtocol):
    """Mixin providing get_authority_address() get method for SBT contracts."""

    async def get_authority_address(self) -> t.Optional[Address]:
        """
        Get authority address from this SBT contract.

        Returns the address that can revoke this Soulbound Token.

        :return: Authority address that can revoke the SBT, None if no authority
        """
        return await get_authority_address_get_method(
            client=self.client,
            address=self.address,
        )


async def get_revoked_time_get_method(
    client: ClientProtocol,
    address: AddressLike,
) -> int:
    """
    Get revocation timestamp from an SBT contract.

    :param client: TON client for blockchain interactions
    :param address: SBT contract address
    :return: Unix timestamp when SBT was revoked, 0 if not revoked
    """
    r = await client.run_get_method(
        address=address,
        method_name="get_revoked_time",
    )
    return int(r[0])


class GetRevokedTimeGetMethod(ContractProtocol):
    """Mixin providing get_revoked_time() get method for SBT contracts."""

    async def get_revoked_time(self) -> int:
        """
        Get revocation timestamp from this SBT contract.

        Returns when this Soulbound Token was revoked.

        :return: Unix timestamp when SBT was revoked, 0 if not revoked
        """
        return await get_revoked_time_get_method(
            client=self.client,
            address=self.address,
        )
