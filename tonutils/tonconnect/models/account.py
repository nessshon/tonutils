from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

from pytoniq_core import Address

from .chain import CHAIN
from ..utils.exceptions import TonConnectError


@dataclass
class Account:
    """
    Represents an account with an address, chain/network, wallet state,
    and optional public key information.
    """
    address: Address
    chain: CHAIN
    wallet_state_init: Optional[str] = None
    public_key: Optional[str] = None

    def __repr__(self) -> str:
        return (
            f"Account(address={self.address.to_str(is_bounceable=False)}, "
            f"chain={self.chain.value}, "
            f"wallet_state_init={self.wallet_state_init}, "
            f"public_key={self.public_key})"
        )

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Account:
        """
        Creates an Account instance from a dictionary.

        :param data: A dictionary containing the account data.
        :raises TonConnectError: If 'address' is not present in the data.
        :return: An Account instance.
        """
        if "address" not in data:
            raise TonConnectError("No 'address' field found in the provided data.")

        return cls(
            address=Address(data.get("address")),
            chain=CHAIN(data.get("network")),
            wallet_state_init=data.get("walletStateInit"),
            public_key=data.get("publicKey"),
        )

    def to_dict(self) -> Dict[str, Any]:
        """
        Converts the Account instance into a dictionary.

        :return: A dictionary representation of the Account.
        """
        return {
            "address": self.address,
            "network": self.chain.value,
            "walletStateInit": self.wallet_state_init,
            "publicKey": self.public_key,
        }
