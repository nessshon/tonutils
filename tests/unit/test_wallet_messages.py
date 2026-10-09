from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from ton_core import Address, DNSRecordWallet, JettonTransferBody, PrivateKey, TextCipher, begin_cell

from tests.constants import ZERO_ADDRESS
from tonutils.contracts.wallet import JettonTransferBuilder, TONTransferBuilder, WalletV4R2
from tonutils.exceptions import ContractError, RunGetMethodError

SENDER_KEY = PrivateKey(bytes([1]) * 32)
RECIPIENT_KEY = PrivateKey(bytes([2]) * 32)


def _make_wallet(client: MagicMock | None = None) -> WalletV4R2:
    return WalletV4R2.from_private_key(client or MagicMock(), SENDER_KEY)


class TestEncryptedComment:
    async def test_recipient_decrypts(self):
        wallet = _make_wallet()
        builder = TONTransferBuilder(
            ZERO_ADDRESS, 1, "secret", encrypt=True, recipient_public_key=RECIPIENT_KEY.public_key
        )
        message = (await builder.build(wallet)).message
        assert TextCipher.decrypt(message.body, wallet.address, RECIPIENT_KEY) == "secret"

    async def test_fetches_recipient_key(self):
        client = MagicMock()
        client.run_get_method = AsyncMock(return_value=[int.from_bytes(RECIPIENT_KEY.public_key.as_bytes, "big")])
        wallet = _make_wallet(client)
        message = (await TONTransferBuilder(ZERO_ADDRESS, 1, "secret", encrypt=True).build(wallet)).message
        assert TextCipher.decrypt(message.body, wallet.address, RECIPIENT_KEY) == "secret"

    async def test_jetton_forward_payload(self):
        wallet = _make_wallet()
        builder = JettonTransferBuilder(
            ZERO_ADDRESS,
            1,
            jetton_wallet_address=ZERO_ADDRESS,
            forward_payload="secret",
            encrypt=True,
            recipient_public_key=RECIPIENT_KEY.public_key,
        )
        message = (await builder.build(wallet)).message
        payload = JettonTransferBody.deserialize(message.body.begin_parse()).forward_payload
        assert TextCipher.decrypt(payload, wallet.address, RECIPIENT_KEY) == "secret"

    async def test_unknown_recipient_key(self):
        client = MagicMock()
        error = RunGetMethodError(address=ZERO_ADDRESS, exit_code=-13, method_name="get_public_key")
        client.run_get_method = AsyncMock(side_effect=error)
        with pytest.raises(ContractError):
            await TONTransferBuilder(ZERO_ADDRESS, 1, "secret", encrypt=True).build(_make_wallet(client))

    async def test_requires_text_body(self):
        builder = TONTransferBuilder(ZERO_ADDRESS, 1, begin_cell().end_cell(), encrypt=True)
        with pytest.raises(ValueError):
            await builder.build(_make_wallet())


class TestDomainDestination:
    async def test_resolves_wallet_record_non_bounceable(self):
        record_address = Address(ZERO_ADDRESS)
        record_address.is_bounceable = True
        client = MagicMock()
        client.dnsresolve = AsyncMock(return_value=DNSRecordWallet(record_address))
        wallet = _make_wallet(client)
        message = (await TONTransferBuilder("alice.ton", 1).build(wallet)).message
        assert message.info.dest == Address(ZERO_ADDRESS)
        assert message.info.bounce is False

    async def test_keeps_address_destination(self):
        destination = Address(ZERO_ADDRESS)
        destination.is_bounceable = True
        message = (await TONTransferBuilder(destination, 1).build(_make_wallet())).message
        assert message.info.bounce is True

    async def test_rejects_domain_without_wallet_record(self):
        client = MagicMock()
        client.dnsresolve = AsyncMock(return_value=None)
        builder = JettonTransferBuilder("alice.ton", 1, jetton_wallet_address=ZERO_ADDRESS)
        with pytest.raises(ContractError):
            await builder.build(_make_wallet(client))
