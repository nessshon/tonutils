from unittest import TestCase

from pytoniq_core import Address

from tests.helpers import ClientTestCase
from tonutils.contracts import (
    NFTCollectionEditable,
    NFTCollectionStandard,
    NFTItemStandard,
    NFTItemEditable,
    NFTItemSoulbound,
)
from tonutils.types import (
    ClientType,
    OffchainContent,
    OffchainItemContent,
)

NFT_COLLECTION_STANDARD_ADDRESS = Address(
    "EQAG2BH0JlmFkbMrLEnyn2bIITaOSssd4WdisE4BdFMkZbir"
)
NFT_COLLECTION_EDITABLE_ADDRESS = Address(
    "EQBibSZPEVHWHhUALDTW4y5NDNcC7HPS-BRgv9dAAsZQjh2E"
)
NFT_COLLECTION_SOULBOUND_ADDRESS = Address(
    "EQCsiaV6k0-EZvl5AyurAjNYqvT6FhGX83xYlKlU5isWt6ki"
)

NFT_ITEM_STANDARD_ADDRESS = Address("EQCoADmGFboLrgOCDSwAe-jI-lOOVoRYllA5F4WeIMokINW8")
NFT_ITEM_EDITABLE_ADDRESS = Address("EQCSAPwp9B8IioWbjYf5w9YTzNlLdk_ntvNvjVtFkp9TGyno")
NFT_ITEM_SOULBOUND_ADDRESS = Address("EQCC6S6n3qStNZYuhGUiu_iJXcdOh2xa7WsklqS7uXiaE8W3")


class TestsNFTContracts(TestCase):

    def test_calcualte_nft_item_address(self) -> None:
        pass


class TestsNFTContractsTonapi(ClientTestCase):
    CLIENT_TYPE = ClientType.TONAPI
    IS_TESTNET = False
    RPS = 1

    async def asyncSetUp(self) -> None:
        await super().asyncSetUp()

        self.nft_collection_standard = await NFTCollectionStandard.from_address(
            client=self.client,
            address=NFT_COLLECTION_STANDARD_ADDRESS,
        )
        self.nft_collection_editable = await NFTCollectionEditable.from_address(
            client=self.client,
            address=NFT_COLLECTION_EDITABLE_ADDRESS,
        )

        self.nft_item_standard: NFTItemStandard = await NFTItemStandard.from_address(
            client=self.client,
            address=NFT_ITEM_STANDARD_ADDRESS,
        )
        self.nft_item_editable: NFTItemEditable = await NFTItemEditable.from_address(
            client=self.client,
            address=NFT_ITEM_EDITABLE_ADDRESS,
        )
        self.nft_item_soulbound: NFTItemSoulbound = await NFTItemSoulbound.from_address(
            client=self.client,
            address=NFT_ITEM_SOULBOUND_ADDRESS,
        )

    async def test_nft_collection_get_collection_data(self) -> None:
        next_item_index, content, owner_address = (
            await self.nft_collection_standard.get_collection_data()
        )
        self.assertIsInstance(next_item_index, int)
        self.assertIsInstance(content, OffchainContent)
        self.assertIsInstance(owner_address, Address)

    async def test_nft_collection_get_nft_address_by_index(self) -> None:
        item_address = await self.nft_collection_standard.get_nft_address_by_index(
            index=self.nft_item_standard.index,
        )
        self.assertEqual(self.nft_item_standard.address, item_address)

    async def test_nft_collection_get_nft_content(self) -> None:
        item_full_content = await self.nft_collection_standard.get_nft_content(
            index=self.nft_item_standard.index,
            individual_nft_content=self.nft_item_standard.content.serialize(),
        )
        item_suffix_uri = self.nft_collection_standard.content.common_content.suffix_uri
        item_prefix_uri = self.nft_item_standard.content.prefix_uri
        item_full_uri = item_suffix_uri + item_prefix_uri
        self.assertEqual(item_full_uri, item_full_content.uri)

    async def test_nft_item_get_nft_data(self) -> None:
        init, index, collection_address, owner_address, content = (
            await self.nft_item_standard.get_nft_data()
        )
        self.assertIsInstance(init, bool)
        self.assertIsInstance(index, int)
        self.assertIsInstance(collection_address, Address)
        self.assertIsInstance(owner_address, Address)
        self.assertIsInstance(content, OffchainItemContent)

    async def test_nft_item_get_editor(self) -> None:
        editor_address = await self.nft_item_editable.get_editor_address()
        self.assertIsInstance(editor_address, (Address, type(None)))

    async def test_nft_item_get_authority_address(self) -> None:
        authority_address = await self.nft_item_soulbound.get_authority_address()
        self.assertIsInstance(authority_address, (Address, type(None)))

    async def test_nft_item_get_revoked_time(self) -> None:
        revoked_time = await self.nft_item_soulbound.get_revoked_time()
        self.assertIsInstance(revoked_time, int)


class TestsNFTContractsToncenter(TestsNFTContractsTonapi):
    CLIENT_TYPE = ClientType.TONCENTER


class TestsNFTContractsLiteserver(TestsNFTContractsTonapi):
    CLIENT_TYPE = ClientType.LITESERVER
