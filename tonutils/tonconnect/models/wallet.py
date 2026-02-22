from __future__ import annotations

import typing as t

from tonutils.tonconnect.exceptions import TonConnectError
from tonutils.tonconnect.models import TonProofPayloadDto
from tonutils.tonconnect.models._types import A, BaseModel
from tonutils.tonconnect.models.account import Account
from tonutils.tonconnect.models.device import Device
from tonutils.tonconnect.models.proof import TonProofData
from tonutils.tonconnect.models.response import (
    ConnectEventPayload,
    TonAddressItemReply,
    TonProofItemReply,
)


class Wallet(BaseModel):
    """Connected wallet state.

    Attributes:
        device: Wallet device information.
        account: Wallet account data.
        ton_proof: TON Proof data, or `None`.
    """

    device: Device
    account: Account
    ton_proof: t.Optional[TonProofData] = A("tonProof", default=None)

    @property
    def ton_proof_dto(self) -> t.Optional[TonProofPayloadDto]:
        """Build a `TonProofPayloadDto` from the stored proof, or `None`."""
        if self.ton_proof is None:
            return None
        return TonProofPayloadDto(
            address=self.account.address,
            network=self.account.network,
            public_key=self.account.public_key,
            wallet_state_init=self.account.state_init,
            proof=self.ton_proof,
        )

    @classmethod
    def from_payload(cls, payload: ConnectEventPayload) -> Wallet:
        """Create a `Wallet` from a `ConnectEventPayload`.

        :param payload: Successful connect event payload.
        :return: Wallet instance.
        :raises TonConnectError: If payload lacks a `ton_addr` item.
        """
        account: t.Optional[Account] = None
        ton_proof: t.Optional[TonProofData] = None

        for item in payload.items:
            if isinstance(item, TonAddressItemReply):
                account = Account.model_validate(item.model_dump(by_alias=True))
            elif isinstance(item, TonProofItemReply):
                ton_proof = item.proof

        if account is None:
            raise TonConnectError(
                "ConnectEventPayload does not contain required `ton_addr` item"
            )

        return cls(device=payload.device, account=account, ton_proof=ton_proof)
