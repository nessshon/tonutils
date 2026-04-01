import typing as t

from ton_core import Address, AddressLike, Cell

from tonutils.clients.protocol import ClientProtocol
from tonutils.contracts.protocol import ContractProtocol


async def get_collection_data_get_method(
    client: ClientProtocol,
    address: AddressLike,
) -> list[t.Any]:
    """Call ``get_collection_data`` on an NFT collection contract.

    :param client: TON client.
    :param address: NFT collection address.
    :return: List of [next_item_index, collection_content, owner_address].
    """
    return await client.run_get_method(
        address=address,
        method_name="get_collection_data",
    )


class GetCollectionDataGetMethod(ContractProtocol[t.Any]):
    """Mixin for the ``get_collection_data`` get-method."""

    async def get_collection_data(self) -> list[t.Any]:
        """Return collection data (next index, content, owner)."""
        return await get_collection_data_get_method(
            client=self.client,
            address=self.address,
        )


async def get_nft_address_by_index_get_method(
    client: ClientProtocol,
    address: AddressLike,
    index: int,
) -> Address:
    """Call ``get_nft_address_by_index`` on an NFT collection contract.

    :param client: TON client.
    :param address: NFT collection address.
    :param index: Item index in the collection.
    :return: NFT item contract address.
    """
    r = await client.run_get_method(
        address=address,
        method_name="get_nft_address_by_index",
        stack=[index],
    )
    return t.cast("Address", r[0])


class GetNFTAddressByIndexGetMethod(ContractProtocol[t.Any]):
    """Mixin for the ``get_nft_address_by_index`` get-method."""

    async def get_nft_address_by_index(self, index: int) -> Address:
        """Return NFT item address by index.

        :param index: Item index in the collection.
        :return: NFT item contract address.
        """
        return await get_nft_address_by_index_get_method(
            client=self.client,
            address=self.address,
            index=index,
        )


async def royalty_params_get_method(
    client: ClientProtocol,
    address: AddressLike,
) -> list[t.Any]:
    """Call ``royalty_params`` on an NFT contract.

    :param client: TON client.
    :param address: NFT contract address.
    :return: List of [numerator, denominator, destination].
    """
    return await client.run_get_method(
        address=address,
        method_name="royalty_params",
    )


class RoyaltyParamsGetMethod(ContractProtocol[t.Any]):
    """Mixin for the ``royalty_params`` get-method."""

    async def royalty_params(self) -> list[t.Any]:
        """Return royalty parameters (numerator, denominator, destination)."""
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
    """Call ``get_nft_content`` on an NFT collection contract.

    :param client: TON client.
    :param address: NFT collection address.
    :param index: Item index in the collection.
    :param individual_nft_content: Individual item content ``Cell``.
    :return: Full NFT metadata ``Cell``.
    """
    r = await client.run_get_method(
        address=address,
        method_name="get_nft_content",
        stack=[index, individual_nft_content],
    )
    return t.cast("Cell", r[0])


class GetNFTContentGetMethod(ContractProtocol[t.Any]):
    """Mixin for the ``get_nft_content`` get-method."""

    async def get_nft_content(
        self,
        index: int,
        individual_nft_content: Cell,
    ) -> Cell:
        """Return full NFT content by combining collection and individual content.

        :param index: Item index in the collection.
        :param individual_nft_content: Individual item content ``Cell``.
        :return: Full NFT metadata ``Cell``.
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
    """Call ``get_second_owner_address`` on an NFT contract.

    :param client: TON client.
    :param address: NFT contract address.
    :return: Second owner address.
    """
    r = await client.run_get_method(
        address=address,
        method_name="get_second_owner_address",
    )
    return t.cast("Address", r[0])


class GetSecondOwnerAddressGetMethod(ContractProtocol[t.Any]):
    """Mixin for the ``get_second_owner_address`` get-method."""

    async def get_second_owner_address(self) -> Address:
        """Return second owner address."""
        return await get_second_owner_address_get_method(
            client=self.client,
            address=self.address,
        )


async def get_nft_data_get_method(
    client: ClientProtocol,
    address: AddressLike,
) -> list[t.Any]:
    """Call ``get_nft_data`` on an NFT item contract.

    :param client: TON client.
    :param address: NFT item address.
    :return: List of [init, index, collection_address, owner_address, content].
    """
    return await client.run_get_method(
        address=address,
        method_name="get_nft_data",
    )


class GetNFTDataGetMethod(ContractProtocol[t.Any]):
    """Mixin for the ``get_nft_data`` get-method."""

    async def get_nft_data(self) -> list[t.Any]:
        """Return NFT item data (init, index, collection, owner, content)."""
        return await get_nft_data_get_method(
            client=self.client,
            address=self.address,
        )


async def get_editor_get_method(
    client: ClientProtocol,
    address: AddressLike,
) -> Address | None:
    """Call ``get_editor`` on an editable NFT contract.

    :param client: TON client.
    :param address: NFT contract address.
    :return: Editor address, or ``None``.
    """
    r = await client.run_get_method(
        address=address,
        method_name="get_editor",
    )
    return t.cast("Address | None", r[0])


class GetEditorGetMethod(ContractProtocol[t.Any]):
    """Mixin for the ``get_editor`` get-method."""

    async def get_editor(self) -> Address | None:
        """Return editor address, or ``None``."""
        return await get_editor_get_method(
            client=self.client,
            address=self.address,
        )


async def get_authority_address_get_method(
    client: ClientProtocol,
    address: AddressLike,
) -> Address | None:
    """Call ``get_authority_address`` on an SBT contract.

    :param client: TON client.
    :param address: SBT contract address.
    :return: Authority address, or ``None``.
    """
    r = await client.run_get_method(
        address=address,
        method_name="get_authority_address",
    )
    return t.cast("Address | None", r[0])


class GetAuthorityAddressGetMethod(ContractProtocol[t.Any]):
    """Mixin for the ``get_authority_address`` get-method."""

    async def get_authority_address(self) -> Address | None:
        """Return authority address that can revoke this SBT, or ``None``."""
        return await get_authority_address_get_method(
            client=self.client,
            address=self.address,
        )


async def get_revoked_time_get_method(
    client: ClientProtocol,
    address: AddressLike,
) -> int:
    """Call ``get_revoked_time`` on an SBT contract.

    :param client: TON client.
    :param address: SBT contract address.
    :return: Revocation unix timestamp, or 0 if not revoked.
    """
    r = await client.run_get_method(
        address=address,
        method_name="get_revoked_time",
    )
    return int(r[0])


class GetRevokedTimeGetMethod(ContractProtocol[t.Any]):
    """Mixin for the ``get_revoked_time`` get-method."""

    async def get_revoked_time(self) -> int:
        """Return revocation unix timestamp, or 0 if not revoked."""
        return await get_revoked_time_get_method(
            client=self.client,
            address=self.address,
        )
