from __future__ import annotations

import time

from ..types.common import NetworkGlobalID, WorkchainID


def calc_valid_until(seqno: int, ttl: int = 60) -> int:
    now = int(time.time())
    return 0xFFFFFFFF if seqno == 0 else now + ttl


class WalletV5SubwalletID:

    def __init__(
        self,
        subwallet_number: int = 0,
        workchain: WorkchainID = WorkchainID.BASECHAIN,
        version: int = 0,
        network_global_id: NetworkGlobalID = NetworkGlobalID.MAINNET,
    ) -> None:
        self.subwallet_number = subwallet_number
        self.workchain = workchain
        self.version = version
        self.network_global_id = network_global_id

    def pack(self) -> int:
        ctx = 0
        ctx |= 1 << 31
        ctx |= (self.workchain & 0xFF) << 23
        ctx |= (self.version & 0xFF) << 15
        ctx |= self.subwallet_number & 0xFFFF
        return ctx ^ (self.network_global_id & 0xFFFFFFFF)

    @classmethod
    def unpack(
        cls,
        value: int,
        network_global_id: NetworkGlobalID,
    ) -> WalletV5SubwalletID:
        ctx = value ^ (network_global_id & 0xFFFFFFFF)

        subwallet_number = ctx & 0xFFFF
        version = (ctx >> 15) & 0xFF
        workchain = (ctx >> 23) & 0xFF

        return cls(
            subwallet_number=subwallet_number,
            workchain=WorkchainID(workchain),
            version=version,
            network_global_id=network_global_id,
        )

    def __repr__(self) -> str:
        return f"WalletV5SubwalletID<{self.pack()!r}>"
