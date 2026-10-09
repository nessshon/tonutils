from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from ton_core import (
    WALLET_TG_SUBWALLET_ID,
    WALLET_TG_SUBWALLET_ID_TESTNET,
    Address,
    MnemonicType,
    NetworkGlobalID,
    PrivateKey,
    PublicKey,
    TextCipher,
    WalletTgChangePublicKeyBody,
    WalletTgConfig,
    WalletTgKeyChangedBody,
    detect_mnemonic_type,
    mnemonic_to_private_key,
    multichain_mnemonic_to_private_key,
)

from tests.constants import ZERO_ADDRESS
from tonutils.contracts.wallet import WalletTg, WalletV3R2, WalletV4R1, WalletV4R2
from tonutils.exceptions import ContractError
from tonutils.types import ContractInfo

mock_client = MagicMock()


class TestCreate:
    def test_returns_wallet_and_keys(self):
        wallet, pub, priv, mnemonic = WalletV4R2.create(mock_client)
        assert isinstance(wallet.address, Address)
        assert isinstance(pub, PublicKey)
        assert isinstance(priv, PrivateKey)
        assert isinstance(mnemonic, list)
        assert len(mnemonic) == 24

    def test_rejects_invalid_length(self):
        with pytest.raises(ContractError):
            WalletV4R2.create(mock_client, mnemonic_length=10)

    @pytest.mark.parametrize(
        ("cls", "mnemonic_length", "mnemonic_type", "expected_length", "expected_type"),
        [
            (WalletV4R2, None, None, 24, MnemonicType.TON),
            (WalletV4R2, 12, None, 12, MnemonicType.MULTICHAIN),
            (WalletV4R2, 18, None, 18, MnemonicType.TON),
            (WalletV4R2, None, MnemonicType.MULTICHAIN, 12, MnemonicType.MULTICHAIN),
            (WalletV4R2, 24, MnemonicType.MULTICHAIN, 24, MnemonicType.MULTICHAIN),
            (WalletTg, None, None, 12, MnemonicType.MULTICHAIN),
            (WalletTg, 24, None, 24, MnemonicType.TON),
        ],
    )
    def test_mnemonic_scheme(self, cls, mnemonic_length, mnemonic_type, expected_length, expected_type):
        *_, mnemonic = cls.create(mock_client, mnemonic_length, mnemonic_type=mnemonic_type)
        assert len(mnemonic) == expected_length
        assert detect_mnemonic_type(mnemonic) == expected_type


class TestFromMnemonic:
    def test_deterministic(self):
        wallet1, pub1, priv1, _ = WalletV4R2.create(mock_client)
        mnemonic = _
        wallet2, pub2, priv2, _ = WalletV4R2.from_mnemonic(mock_client, mnemonic)
        assert wallet1.address == wallet2.address
        assert pub1 == pub2
        assert priv1 == priv2

    def test_string_equals_list(self):
        _, _, _, mnemonic_list = WalletV4R2.create(mock_client)
        mnemonic_str = " ".join(mnemonic_list)
        w_list, _, _, _ = WalletV4R2.from_mnemonic(mock_client, mnemonic_list)
        w_str, _, _, _ = WalletV4R2.from_mnemonic(mock_client, mnemonic_str)
        w_upper, _, _, _ = WalletV4R2.from_mnemonic(mock_client, [w.upper() for w in mnemonic_list])
        assert w_list.address == w_str.address == w_upper.address

    def test_different_mnemonics_different_addresses(self):
        w1, _, _, _ = WalletV4R2.create(mock_client)
        w2, _, _, _ = WalletV4R2.create(mock_client)
        assert w1.address != w2.address

    def test_validates_bad_mnemonic(self):
        with pytest.raises(ValueError, match="Invalid mnemonic"):
            WalletV4R2.from_mnemonic(mock_client, "invalid words here that dont exist xyz")

    def test_validates_short_mnemonic(self):
        with pytest.raises(ValueError, match="Invalid mnemonic length"):
            WalletV4R2.from_mnemonic(mock_client, "word word word")

    def test_multichain_key(self):
        # BIP-39 reference phrase; key at m/44'/607'/0'
        mnemonic = "abandon " * 11 + "about"
        _, pub, _, _ = WalletV4R2.from_mnemonic(mock_client, mnemonic)
        assert pub.as_hex == "7952e94118f34607c75e23258dd9220d66ccac5a3ee074125c25068e8107bfbf"

    def test_without_validation_uses_wallet_scheme(self):
        mnemonic = "abandon " * 11 + "about"
        _, pub, _, _ = WalletV4R2.from_mnemonic(mock_client, mnemonic, validate=False)
        assert pub.as_bytes == mnemonic_to_private_key(mnemonic.split())[0]

    def test_multichain_rejects_bad_checksum(self):
        with pytest.raises(ValueError, match="checksum"):
            WalletV4R2.from_mnemonic(mock_client, "abandon " * 12, mnemonic_type=MnemonicType.MULTICHAIN)

    def test_ton_rejects_multichain_mnemonic(self):
        with pytest.raises(ValueError, match="MULTICHAIN"):
            WalletV4R2.from_mnemonic(mock_client, "abandon " * 11 + "about", mnemonic_type=MnemonicType.TON)

    def test_ambiguous_mnemonic_uses_wallet_scheme(self):
        # valid as both a TON and a BIP-39 mnemonic
        mnemonic = "today loyal inhale category human link conduct member heart bleak gate modify"
        _, ton_pub, _, _ = WalletV4R2.from_mnemonic(mock_client, mnemonic)
        _, tg_pub, _, _ = WalletTg.from_mnemonic(mock_client, mnemonic)
        assert ton_pub.as_bytes == mnemonic_to_private_key(mnemonic.split())[0]
        assert tg_pub.as_bytes == multichain_mnemonic_to_private_key(mnemonic.split())[0]


class TestDifferentVersions:
    def test_same_mnemonic_different_versions_different_addresses(self):
        _, _, _, mnemonic = WalletV4R2.create(mock_client)
        w_v3, _, _, _ = WalletV3R2.from_mnemonic(mock_client, mnemonic)
        w_v4r1, _, _, _ = WalletV4R1.from_mnemonic(mock_client, mnemonic)
        w_v4r2, _, _, _ = WalletV4R2.from_mnemonic(mock_client, mnemonic)
        w_tg, _, _, _ = WalletTg.from_mnemonic(mock_client, mnemonic)
        assert w_v3.address != w_v4r1.address
        assert w_v3.address != w_v4r2.address
        assert w_v4r1.address != w_v4r2.address
        assert w_tg.address != w_v4r2.address


class TestFromPrivateKey:
    def test_deterministic(self):
        _, _, priv, _ = WalletV4R2.create(mock_client)
        w1 = WalletV4R2.from_private_key(mock_client, priv)
        w2 = WalletV4R2.from_private_key(mock_client, priv)
        assert w1.address == w2.address

    def test_public_key_matches(self):
        _, pub, priv, _ = WalletV4R2.create(mock_client)
        wallet = WalletV4R2.from_private_key(mock_client, priv)
        assert wallet._private_key.public_key == pub


class TestWalletTg:
    def test_subwallet_id_defaults_to_mainnet(self):
        wallet = WalletTg.from_private_key(mock_client, PrivateKey(bytes(32)))
        assert wallet.config.subwallet_id == WALLET_TG_SUBWALLET_ID

    def test_subwallet_id_on_testnet(self):
        testnet_client = MagicMock()
        testnet_client.network = NetworkGlobalID.TESTNET
        wallet = WalletTg.from_private_key(testnet_client, PrivateKey(bytes(32)))
        assert wallet.config.subwallet_id == WALLET_TG_SUBWALLET_ID_TESTNET

    async def test_from_address_derives_undeployed_with_config(self, monkeypatch):
        key = PrivateKey(bytes([1]) * 32)
        address = WalletTg.from_private_key(mock_client, key, config=WalletTgConfig(subwallet_id=1)).address
        monkeypatch.setattr(WalletTg, "_load_info", AsyncMock(return_value=ContractInfo()))
        wallet = await WalletTg.from_address_and_private_key(
            mock_client, address, key, config=WalletTgConfig(subwallet_id=1)
        )
        assert wallet.address == address

    def test_key_changed_body_pins_encryption(self):
        # sha256(new_seed || WALLET_TG_KEY_CHANGE_SALT) XOR old_seed: part of the on-chain format.
        body = WalletTgKeyChangedBody.from_keys(PrivateKey(bytes([0x11]) * 32), PrivateKey(bytes([0x22]) * 32))
        assert (
            body.encrypted_old_private_key.hex() == "57a12a6e8d1d18cf5dfdc42a8a63b30630522d31a9530a692f9713fd14815255"
        )

    async def test_change_public_key_with_custom_salt(self):
        client = MagicMock()
        client.network = NetworkGlobalID.TESTNET
        old_key, new_key = PrivateKey(bytes([1]) * 32), PrivateKey(bytes([2]) * 32)
        wallet = WalletTg.from_private_key(client, old_key)
        wallet.refresh = AsyncMock()
        wallet._info = ContractInfo()

        msg = await wallet.build_change_public_key_message(new_key, salt=b"custom")
        cs = msg.body.begin_parse()
        cs.skip_bits(512)
        request = WalletTgChangePublicKeyBody.deserialize(cs)
        key_changed = WalletTgKeyChangedBody(request.encrypted_old_private_key)
        assert key_changed.decrypt(new_key, salt=b"custom").as_bytes == old_key.as_bytes
        assert key_changed.decrypt(new_key).as_bytes != old_key.as_bytes

    def test_decrypt_with_wrong_key_raises_value_error(self):
        sender, recipient = PrivateKey(bytes([1]) * 32), PrivateKey(bytes([2]) * 32)
        body = TextCipher.encrypt("hi", ZERO_ADDRESS, sender, recipient.public_key)
        for i in range(32):
            with pytest.raises(ValueError):
                TextCipher.decrypt(body, ZERO_ADDRESS, PrivateKey(bytes([0x80 + i]) * 32))

    async def test_change_public_key_rejects_same_key(self):
        client = MagicMock()
        client.network = NetworkGlobalID.TESTNET
        key = PrivateKey(bytes([1]) * 32)
        wallet = WalletTg.from_private_key(client, key)
        with pytest.raises(ContractError):
            await wallet.build_change_public_key_message(key)


class TestMessageCount:
    def test_error_names_wallet(self):
        with pytest.raises(ContractError, match="WalletV4R2 failed"):
            WalletV4R2._validate_message_count([MagicMock()] * 5)
