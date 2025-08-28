import typing as t
from decimal import Decimal
from unittest import TestCase

from pytoniq_core import (
    Address,
    Cell,
    Slice,
    begin_cell,
)

from tonutils.types import ClientType, PrivateKey, WorkchainID, NetworkGlobalID
from tonutils.utils import (
    StackCodec,
    TextCipher,
    cell_to_b64,
    cell_to_hex,
    cell_hash,
    normalize_hash,
    slice_hash,
    string_hash,
    to_cell,
    WalletV5SubwalletID,
    to_amount,
    to_nano,
)

CELL_HEX = "b5ee9c7201010101002a0000500168747470733a2f2f6e66742e667261676d656e742e636f6d2f757365726e616d65732e6a736f6e"
CELL_B64 = "te6ccgEBAQEAKgAAUAFodHRwczovL25mdC5mcmFnbWVudC5jb20vdXNlcm5hbWVzLmpzb24="
CELL_BYTES = bytes.fromhex(CELL_HEX)
CELL_SLICE = Slice.one_from_boc(CELL_HEX)
CELL = CELL_SLICE.to_cell()

MESSAGE_HEX = "b5ee9c7201020d0100028a0003b578379ed1da34943d4d870c33d42263e3cf790affc450cdaf282a4bcc7cea49a9100003754e7847c41d99e0513ab5e320b789f43e493b10315a5f4d3c41f6974022ef4436a22889fdb0000371d09faa34168ac719d00054666febc80102030201e004050082724b09a7b09203b73b83d9293c7108e409d30009cf16f9daaf5a6ebe950cc40dd841477adbde3012580ca1d75367f579bf10907c2df711e13df7cb3ee31ce730bb02130cc08af24619313984400b0c0098880106f3da3b469287a9b0e1867a844c7c79ef215ff88a19b5e50549798f9d4935220108a3816c0055233e112c745f28b689a6a1828da440416ea18060079ce88643bf9225f5bd2468ac719a0201dd0607010120080101200900b7480106f3da3b469287a9b0e1867a844c7c79ef215ff88a19b5e50549798f9d493523001548cf844b1d17ca2da269a860a36910105ba8601801e73a2190efe4897d6f490d312d000608235a00006ea9cf08f884d158e33a1702448d4001b3480106f3da3b469287a9b0e1867a844c7c79ef215ff88a19b5e50549798f9d4935230020eb806688ea058afaa972c3af71599a2cbab1b1ae94602204a456c81a854b715409502f9000060c245c00006ea9cf08f886d158e33ac00a0062000000005468616e6b7320666f7220746f6e7574696c732066726f6d2063726f6e212028efbfa3e296bdefbfa329e3838e009d430d63138800000000000000001f4000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000020006fc9879ae04c1447940000000000040000000000051d0eb6386a84e2d8f909cc22fb5eae3909f490962ea348759614866cecd0dc6640d03954"
NORMALIZED_HASH = "ab49f1d3293243946f8e81f0169524003302688218d718fedbc99dd90163853b"

STRING_HASH_TEXT = "nessshon"
STRING_HASH = (
    45354304031421179242460489368440335494304328265643744596791119159788447170008
)

CELL_HASH_TEXT = "wallet"
CELL_HASH_CELL = begin_cell().store_snake_string(CELL_HASH_TEXT).end_cell()
CELL_HASH = (
    115698008076457823118597424358900481870087387390627058654421588318795409511780
)

DECRYPTED_PAYLOAD = "Hello from tonutils!"
SENDER_ADDRESS = Address("UQD_nC7tFgl5S_WvW6LJHRqX-smNCeDYIfYBxbD0tcHnbjxC")
SENDER_PRIVKEY = PrivateKey("9A4xl6qjn4PrbN0yIPQXAqVi634g78b2MyzJ6psmVak=")
RECIPIENT_PRIVKEY = PrivateKey("C3tEgYARTXnF+NPD7ufnn7LepZd4+kKigowVFH2kSHk=")
RECIPIENT_PUBKEY = RECIPIENT_PRIVKEY.public_key

STACK_PALOAD = [-1, CELL, Cell.one_from_boc("b5ee9c7201010101000300000120")]
STACK_RESPONSE = [-1, CELL, None]

STACK_PAYLOADS = {
    ClientType.TONAPI: [
        -1,
        "te6ccgEBAQEAKgAAUAFodHRwczovL25mdC5mcmFnbWVudC5jb20vdXNlcm5hbWVzLmpzb24=",
        "te6ccgEBAQEAAwAAASA=",
    ],
    ClientType.TONCENTER: [
        ["num", "-0x1"],
        [
            "tvm.Cell",
            "te6ccgEBAQEAKgAAUAFodHRwczovL25mdC5mcmFnbWVudC5jb20vdXNlcm5hbWVzLmpzb24=",
        ],
        ["tvm.Cell", "te6ccgEBAQEAAwAAASA="],
    ],
    ClientType.LITESERVER: STACK_PALOAD,
}
STACK_RESPONSES: t.Dict[ClientType, t.List[t.Any]] = {
    ClientType.TONAPI: [
        {"type": "num", "num": "-0x1"},
        {
            "type": "cell",
            "cell": "b5ee9c7201010101002a0000500168747470733a2f2f6e66742e667261676d656e742e636f6d2f757365726e616d65732e6a736f6e",
        },
        {"type": "cell", "cell": "b5ee9c7201010101000300000120"},
    ],
    ClientType.TONCENTER: [
        ["num", "-0x1"],
        [
            "cell",
            {
                "bytes": "te6cckEBAQEAKgAAUAFodHRwczovL25mdC5mcmFnbWVudC5jb20vdXNlcm5hbWVzLmpzb24K7MvY"
            },
        ],
        ["cell", {"bytes": "te6cckEBAQEAAwAAASCUQYZV"}],
    ],
    ClientType.LITESERVER: STACK_RESPONSE,
}


class TestUtils(TestCase):

    def tests_converters(self) -> None:
        cells = [
            to_cell(CELL),
            to_cell(CELL_HEX),
            to_cell(CELL_B64),
            to_cell(CELL_BYTES),
            to_cell(CELL_SLICE),
        ]
        self.assertTrue(all(isinstance(x, Cell) for x in cells))

        self.assertEqual(cell_to_hex(CELL), CELL_HEX)
        self.assertEqual(cell_to_hex(CELL_HEX), CELL_HEX)
        self.assertEqual(cell_to_hex(CELL_B64), CELL_HEX)
        self.assertEqual(cell_to_hex(CELL_BYTES), CELL_HEX)
        self.assertEqual(cell_to_hex(CELL_SLICE), CELL_HEX)

        self.assertEqual(cell_to_b64(to_cell(CELL)), CELL_B64)
        self.assertEqual(cell_to_b64(to_cell(CELL_HEX)), CELL_B64)
        self.assertEqual(cell_to_b64(to_cell(CELL_B64)), CELL_B64)
        self.assertEqual(cell_to_b64(to_cell(CELL_BYTES)), CELL_B64)
        self.assertEqual(cell_to_b64(to_cell(CELL_SLICE)), CELL_B64)

        self.assertEqual(cell_hash(CELL_HASH_CELL), CELL_HASH)
        self.assertEqual(string_hash(STRING_HASH_TEXT), STRING_HASH)
        self.assertEqual(slice_hash(CELL_HASH_CELL.to_slice()), CELL_HASH)

        self.assertEqual(normalize_hash(MESSAGE_HEX), NORMALIZED_HASH)

    def tests_text_cipher(self) -> None:
        encrypted = TextCipher.encrypt(
            payload=DECRYPTED_PAYLOAD,
            sender_address=SENDER_ADDRESS,
            our_private_key=SENDER_PRIVKEY,
            their_public_key=RECIPIENT_PUBKEY,
        )
        self.assertIsInstance(encrypted, Cell)

        decrypted = TextCipher.decrypt(
            payload=encrypted,
            sender_address=SENDER_ADDRESS,
            our_public_key=RECIPIENT_PUBKEY,
            our_private_key=RECIPIENT_PRIVKEY,
        )
        self.assertEqual(decrypted, DECRYPTED_PAYLOAD)

    def _tests_stack_codec(self, client_type: ClientType) -> None:
        codec = StackCodec(client_type)

        encoded_payload = codec.encode(STACK_PALOAD)
        expected_encoded_payload = STACK_PAYLOADS[client_type]
        self.assertEqual(encoded_payload, expected_encoded_payload)

        decoded_response = codec.decode(STACK_RESPONSES[client_type])
        expected_decoded_response = STACK_RESPONSE
        self.assertEqual(decoded_response, expected_decoded_response)

    def tests_stack_codec_tonapi(self) -> None:
        self._tests_stack_codec(ClientType.TONAPI)

    def tests_stack_codec_toncenter(self) -> None:
        self._tests_stack_codec(ClientType.TONCENTER)

    def tests_stack_codec_liteserver(self) -> None:
        self._tests_stack_codec(ClientType.LITESERVER)

    def tests_value_utils(self) -> None:
        decimals = 9
        self.assertEqual(to_nano("1", decimals), 1_000_000_000)
        self.assertEqual(to_nano("0.000000001", decimals), 1)
        self.assertEqual(to_nano(Decimal("1.234567891"), decimals), 1_234_567_891)

        self.assertEqual(to_nano("1.2345678919", decimals), 1_234_567_891)
        self.assertEqual(to_nano("0.9999999999", decimals), 999_999_999)

        self.assertEqual(to_nano(1.2, 1), 12)
        self.assertEqual(to_nano(7, 0), 7)
        self.assertEqual(to_nano("42", 0), 42)
        self.assertEqual(
            to_amount(1_234_567_891, decimals, precision=4),
            Decimal("1.2345"),
        )
        self.assertEqual(
            to_amount(9_999, 4, precision=2),
            Decimal("0.99"),
        )
        self.assertEqual(to_amount(0, decimals), Decimal(0))

        with self.assertRaises(ValueError):
            to_amount(-1, decimals)
        with self.assertRaises(ValueError):
            to_amount(2 ** 256, decimals)
        with self.assertRaises(ValueError):
            to_amount(1, -1)

        for s in ["1.234567891", "0.000000001", "123456789.987654321"]:
            src = Decimal(s)
            nano = to_nano(src, decimals)
            back = to_amount(nano, decimals)
            self.assertLessEqual(back, src)
            self.assertLess(src - back, Decimal(f"1e-{decimals}"))

    def tests_wallet_v5_id(self) -> None:
        subwallet_id = WalletV5SubwalletID(
            subwallet_number=0,
            workchain=WorkchainID.BASECHAIN,
            version=0,
            network_global_id=NetworkGlobalID.MAINNET,
        )
        self.assertEqual(subwallet_id.pack(), 2147483409)

        subwallet_id = WalletV5SubwalletID(
            subwallet_number=0,
            workchain=WorkchainID.MASTERCHAIN,
            version=0,
            network_global_id=NetworkGlobalID.MAINNET,
        )
        self.assertEqual(subwallet_id.pack(), 8388369)

        subwallet_id = WalletV5SubwalletID(
            subwallet_number=0,
            workchain=WorkchainID.BASECHAIN,
            version=0,
            network_global_id=NetworkGlobalID.TESTNET,
        )
        self.assertEqual(subwallet_id.pack(), 2147483645)

        subwallet_id = WalletV5SubwalletID(
            subwallet_number=0,
            workchain=WorkchainID.MASTERCHAIN,
            version=0,
            network_global_id=NetworkGlobalID.TESTNET,
        )
        self.assertEqual(subwallet_id.pack(), 8388605)
