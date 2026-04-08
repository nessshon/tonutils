from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from ton_core import Address, PrivateKey, PublicKey

from tonutils.contracts.wallet import WalletV3R2, WalletV4R1, WalletV4R2
from tonutils.exceptions import ContractError

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
        assert w_list.address == w_str.address

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


class TestDifferentVersions:
    def test_same_mnemonic_different_versions_different_addresses(self):
        _, _, _, mnemonic = WalletV4R2.create(mock_client)
        w_v3, _, _, _ = WalletV3R2.from_mnemonic(mock_client, mnemonic)
        w_v4r1, _, _, _ = WalletV4R1.from_mnemonic(mock_client, mnemonic)
        w_v4r2, _, _, _ = WalletV4R2.from_mnemonic(mock_client, mnemonic)
        assert w_v3.address != w_v4r1.address
        assert w_v3.address != w_v4r2.address
        assert w_v4r1.address != w_v4r2.address


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
