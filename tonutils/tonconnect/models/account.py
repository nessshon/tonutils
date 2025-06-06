from __future__ import annotations

import base64
from dataclasses import dataclass
from typing import Any, Dict, Optional, Union

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
    public_key: Optional[Union[str, bytes]] = None

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
        public_key = bytes.fromhex(data["publicKey"]) if "publicKey" in data else None

        return cls(
            address=Address(data.get("address")),
            chain=CHAIN(data.get("network")),
            wallet_state_init=data.get("walletStateInit"),
            public_key=public_key,
        )

    def to_dict(self) -> Dict[str, Any]:
        """
        Converts the Account instance into a dictionary.

        :return: A dictionary representation of the Account.
        """
        if isinstance(self.public_key, bytes):
            self.public_key = base64.b64encode(self.public_key).decode()

        return {
            "address": self.address,
            "network": self.chain.value,
            "walletStateInit": self.wallet_state_init,
            "publicKey": self.public_key,
        }
