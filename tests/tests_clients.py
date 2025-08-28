from pytoniq_core import (
    Address,
    Cell,
    StateInit,
    Transaction,
)

from tests.helpers import ClientTestCase
from tonutils.types import (
    ClientType,
    ContractStateInfo,
    ContractState,
    PublicKey,
)

WALLET_ADDRESS = Address(
    "0:83ae019a23a8162beaa5cb0ebdc56668b2eac6c6ba51808812915b206a152dc5"
)
WALLET_PUBLIC_KEY = PublicKey(
    55076642238194142798835029799378000396651553013470455265600214024586038843895
)

TX_LIMIT = 2
TX_TO_LT = 60837801000002
TX_PREV_HASH_HEX = "f86526829c6532063ec13d97231bf3579e9d1321124397766fb27eb76374a4ff"


class TestTonapiClient(ClientTestCase):
    CLIENT_TYPE = ClientType.LITESERVER
    IS_TESTNET = False
    RPS = 1

    async def test_send_boc(self) -> None:
        pass

    async def test_get_blockchain_config(self) -> None:
        result = await self.client.get_blockchain_config()
        self.assertIsInstance(result, dict)

    async def test_get_contract_info(self) -> None:
        result = await self.client.get_contract_info(WALLET_ADDRESS)

        self.assertIsNotNone(result.code_raw)
        self.assertIsNotNone(result.data_raw)
        self.assertGreater(result.balance, 0)
        self.assertIsInstance(result, ContractStateInfo)
        self.assertIs(result.state, ContractState.ACTIVE)
        self.assertIsNotNone(result.last_transaction_lt)
        self.assertIsNotNone(result.last_transaction_hash)

        self.assertIsInstance(result.code, Cell)
        self.assertIsInstance(result.data, Cell)
        self.assertIsInstance(result.state_init, StateInit)

    async def test_get_contract_transactions(self) -> None:
        result = await self.client.get_contract_transactions(
            address=WALLET_ADDRESS,
            limit=TX_LIMIT,
            to_lt=TX_TO_LT,
        )
        tx = result[0]
        prev_tx_hash_hex = tx.prev_trans_hash.hex()

        self.assertEqual(len(result), TX_LIMIT)
        self.assertIsInstance(tx, Transaction)
        self.assertEqual(prev_tx_hash_hex, TX_PREV_HASH_HEX)

    async def test_run_get_method(self) -> None:
        result = await self.client.run_get_method(
            address=WALLET_ADDRESS,
            method_name="seqno",
        )
        stack_item = result[0]

        self.assertIsInstance(stack_item, int)
        self.assertGreater(stack_item, 0)

        result = await self.client.run_get_method(
            address=WALLET_ADDRESS,
            method_name="get_public_key",
        )
        stack_item = result[0]
        public_key = PublicKey(stack_item)

        self.assertIsInstance(stack_item, int)
        self.assertEqual(public_key, WALLET_PUBLIC_KEY)


class TestToncenterClient(TestTonapiClient):
    CLIENT_TYPE = ClientType.TONCENTER


class TestLiteserverClient(TestTonapiClient):
    CLIENT_TYPE = ClientType.LITESERVER
