from tests.helpers import ClientTestCase
from tonutils.contracts import (
    WalletV3R2,
    WalletV4R2,
    WalletV5R1,
)
from tonutils.types import (
    ClientType,
    PublicKey,
    DEFAULT_SUBWALLET_ID,
)

WALLET_V3R2 = "UQB9IDJqXn8m3QhqCaKWNjKlFEwe2a4gecrgc-RgqcdXc0Wv"
WALLET_V4R2 = "UQC-3ilVr-W0Uc3pLrGJElwSaFxvhXXfkiQA3EwdVBHNNbbp"
WALLET_V5R1 = "UQCDrgGaI6gWK-qlyw69xWZosurGxrpRgIgSkVsgahUtxZR0"


class TestsWalletContractsTonapi(ClientTestCase):
    CLIENT_TYPE = ClientType.TONAPI
    IS_TESTNET = False
    RPS = 1

    async def asyncSetUp(self) -> None:
        await super().asyncSetUp()
        self.wallet_v3r2 = await WalletV3R2.from_address(self.client, WALLET_V3R2)
        self.wallet_v4r2 = await WalletV4R2.from_address(self.client, WALLET_V4R2)
        self.wallet_v5r1 = await WalletV5R1.from_address(self.client, WALLET_V5R1)

    async def test_get_seqno(self) -> None:
        seqno = await self.wallet_v3r2.seqno()
        self.assertIsInstance(seqno, int)

        seqno = await self.wallet_v4r2.seqno()
        self.assertIsInstance(seqno, int)

        seqno = await self.wallet_v5r1.seqno()
        self.assertIsInstance(seqno, int)

    async def test_get_public_key(self) -> None:
        public_key = await self.wallet_v3r2.get_public_key()
        self.assertIsInstance(public_key, PublicKey)

        public_key = await self.wallet_v4r2.get_public_key()
        self.assertIsInstance(public_key, PublicKey)

        public_key = await self.wallet_v5r1.get_public_key()
        self.assertIsInstance(public_key, PublicKey)

    async def test_get_subwallet_id(self) -> None:
        subwallet_id = await self.wallet_v4r2.get_subwallet_id()
        self.assertIsInstance(subwallet_id, int)
        self.assertEqual(subwallet_id, DEFAULT_SUBWALLET_ID)

        subwallet_id = await self.wallet_v5r1.get_subwallet_id()
        self.assertIsInstance(subwallet_id, int)
        self.assertEqual(subwallet_id, 2147483409)

    async def test_is_plugin_installed(self) -> None:
        pass

    async def test_get_plugin_list(self) -> None:
        pass

    async def test_is_signature_allowed(self) -> None:
        is_signature_allowed = await self.wallet_v5r1.is_signature_allowed()
        self.assertIsInstance(is_signature_allowed, bool)
        self.assertTrue(is_signature_allowed)

    async def test_get_extensions(self) -> None:
        pass
