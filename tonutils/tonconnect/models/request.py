from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

from pytoniq_core import Cell

from .chain import CHAIN
from ..utils.exceptions import TonConnectError


class ItemName(str, Enum):
    """
    Enum representing the names of connection items used in the TonConnect protocol.
    """
    TON_ADDR = "ton_addr"
    TON_PROOF = "ton_proof"


@dataclass
class ConnectItem:
    """
    Represents an item required for establishing a connection with the wallet.
    """
    name: str
    payload: Optional[Any] = None

    def to_dict(self) -> Dict[str, Any]:
        """
        Converts the ConnectItem instance into a dictionary format.

        :return: A dictionary representation of the ConnectItem.
        """
        data = {"name": ItemName(self.name).value}
        if self.payload is not None:
            data["payload"] = self.payload
        return data


@dataclass
class Message:
    """
    Represents a single message within a transaction.
    """
    address: str
    amount: str
    payload: Optional[str] = None
    state_init: Optional[str] = None

    def __repr__(self) -> str:
        return (
            f"Message(address={self.address}, "
            f"amount={self.amount}, "
            f"payload={self.payload}, "
            f"state_init={self.state_init})"
        )

    def to_dict(self) -> Dict[str, Any]:
        """
        Converts the Message instance into a dictionary format.

        :return: A dictionary representation of the Message.
        """
        data = {
            "address": self.address,
            "amount": self.amount
        }
        if self.payload is not None:
            data["payload"] = self.payload
        if self.state_init is not None:
            data["stateInit"] = self.state_init
        return data


@dataclass
class Transaction:
    """
    Represents a transaction containing multiple messages.
    """
    from_: Optional[str] = None
    network: Optional[CHAIN] = None
    valid_until: Optional[int] = None
    messages: List[Message] = field(default_factory=list)

    def __repr__(self) -> str:
        return (
            f"Transaction(from={self.from_}, "
            f"network={self.network}, "
            f"valid_until={self.valid_until}, "
            f"messages={self.messages})"
        )

    def to_dict(self) -> Dict[str, Any]:
        """
        Converts the Transaction instance into a dictionary format.

        :return: A dictionary representation of the Transaction.
        """
        return {
            "valid_until": self.valid_until,
            "from": self.from_,
            "network": self.network.value if self.network else None,
            "messages": [message.to_dict() for message in self.messages],
        }


@dataclass
class Request:
    """
    Abstract base class representing a generic request in the TonConnect protocol.
    """
    id: Optional[int] = None
    method: Optional[str] = None
    params: Optional[List[Any]] = None

    def __repr__(self) -> str:
        return (
            f"Request(id={self.id}, "
            f"method={self.method}, "
            f"params={self.params})"
        )

    def to_dict(self) -> Dict[str, Any]:
        """
        Converts the Request instance into a dictionary format.

        :raises NotImplementedError: If not implemented in a subclass.
        """
        raise NotImplementedError("Subclasses must implement the to_dict method.")


@dataclass
class SendTransactionRequest(Request):
    """
    Represents a request to send a transaction containing one or more messages.
    """
    params: List[Transaction] = field(default_factory=list)
    id: Optional[int] = None
    method: str = "sendTransaction"

    def to_dict(self) -> Dict[str, Any]:
        """
        Converts the SendTransactionRequest instance into a dictionary format suitable for JSON serialization.

        :return: A dictionary representation of the SendTransactionRequest.
        """
        return {
            "id": str(self.id) if self.id is not None else None,
            "method": self.method,
            "params": [json.dumps(transaction.to_dict()) for transaction in self.params],
        }


@dataclass
class SendTransactionResponse:
    """
    Represents the response received after sending a transaction.
    """
    _boc: Optional[str] = None

    @property
    def boc(self) -> Optional[str]:
        """
        Retrieves the BOC string.

        :return: The BOC string if available, else None.
        """
        return self._boc

    @property
    def cell(self) -> Cell:
        """
        Parses the BOC string into a Cell object.

        :return: A Cell object created from the BOC string.
        """
        if not self.boc:
            raise TonConnectError("BOC data is missing in the transaction response.")
        return Cell.one_from_boc(self.boc)

    @property
    def hash(self) -> str:
        """
        Computes the hash of the Cell object derived from the BOC.

        :return: The hexadecimal representation of the Cell's hash.
        """
        cell = self.cell
        return cell.hash.hex()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> SendTransactionResponse:
        """
        Creates a SendTransactionResponse instance from a dictionary.

        :param data: A dictionary containing the transaction response data.
        :return: An instance of SendTransactionResponse.
        """
        return cls(_boc=data.get("result"))

    def to_dict(self) -> Dict[str, Any]:
        """
        Converts the SendTransactionResponse instance into a dictionary format.

        :return: A dictionary representation of the SendTransactionResponse.
        """
        return {"boc": self._boc}


@dataclass
class SendDisconnectRequest(Request):
    """
    Represents a request to disconnect from the wallet.
    """
    id: Optional[int] = None
    method: str = "disconnect"

    def to_dict(self) -> Dict[str, Any]:
        """
        Converts the SendDisconnectRequest instance into a dictionary format suitable for JSON serialization.

        :return: A dictionary representation of the SendDisconnectRequest.
        """
        return {
            "id": str(self.id) if self.id is not None else None,
            "method": self.method,
            "params": [],
        }


@dataclass
class SendConnectRequest:
    """
    Represents a request to establish a connection with the wallet.
    """
    manifest_url: str
    items: List[ConnectItem] = field(default_factory=list)

    @classmethod
    def create(
            cls,
            manifest_url: str,
            ton_proof: Optional[str] = None,
    ) -> SendConnectRequest:
        """
        Factory method to create a SendConnectRequest with optional TON proof.

        :param manifest_url: The URL of the DApp's manifest.
        :param ton_proof: Optional TON proof string for authentication.
        :return: An instance of SendConnectRequest.
        """
        items = [ConnectItem(name=ItemName.TON_ADDR.value)]
        if ton_proof is not None:
            items.append(
                ConnectItem(
                    name=ItemName.TON_PROOF.value,
                    payload=ton_proof,
                )
            )

        return cls(manifest_url=manifest_url, items=items)

    def to_dict(self) -> Dict[str, Any]:
        """
        Converts the SendConnectRequest instance into a dictionary format suitable for JSON serialization.

        :return: A dictionary representation of the SendConnectRequest.
        """
        return {
            "manifestUrl": self.manifest_url,
            "items": [item.to_dict() for item in self.items]
        }
