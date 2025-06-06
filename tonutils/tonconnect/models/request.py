from __future__ import annotations

import base64
import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pytoniq_core import Address, Cell, StateInit, begin_cell, MessageAny

from .chain import CHAIN
from ...utils import (
    boc_to_base64_string,
    normalize_hash,
    to_nano,
)


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

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ConnectItem:
        """
        Creates a ConnectItem instance from a dictionary.

        :param data: A dictionary containing the item data.
        :return: An instance of ConnectItem.
        """
        return ConnectItem(name=data["name"], payload=data.get("payload"))

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

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Message:
        """
        Creates a Message instance from a dictionary.

        :param data: A dictionary containing message data.
        :return: An instance of Message.
        """
        return Message(
            address=data["address"],
            amount=data["amount"],
            payload=data.get("payload"),
            state_init=data.get("stateInit"),
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

    @classmethod
    def create_message(
            cls,
            destination: Union[Address, str],
            amount: Union[float, int],
            body: Optional[Union[Cell, str]] = None,
            state_init: Optional[StateInit] = None,
            **_: Any,
    ) -> Message:
        """
        Creates a basic transfer message compatible with the SendTransactionRequest.

        :param destination: The Address object or string representing the recipient.
        :param amount: The amount in TONs to be transferred.
        :param body: Optional message payload (Cell or string).
        :param state_init: Optional StateInit for deploying contracts.
        :param _: Any additional keyword arguments are ignored.
        :return: A Message object ready to be sent.
        """
        destination_str = destination.to_str() if isinstance(destination, Address) else destination
        state_init_b64 = boc_to_base64_string(state_init.serialize().to_boc()) if state_init else None

        if body is not None:
            if isinstance(body, str):
                # Convert string payload to a Cell.
                body_cell = (
                    begin_cell()
                    .store_uint(0, 32)
                    .store_snake_string(body)
                    .end_cell()
                )
                body = boc_to_base64_string(body_cell.to_boc())
            else:
                # Body is already a Cell; convert to base64.
                body = boc_to_base64_string(body.to_boc())

        return Message(
            address=destination_str,
            amount=str(to_nano(amount)),
            payload=body,
            state_init=state_init_b64,
        )

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Transaction:
        """
        Creates a Transaction instance from a dictionary.

        :param data: A dictionary containing transaction data.
        :return: An instance of Transaction.
        """
        return Transaction(
            from_=data.get("from"),
            network=CHAIN(data.get("network")),
            valid_until=data.get("valid_until"),
            messages=[Message.from_dict(message) for message in data.get("messages", [])],
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
    id: Optional[int] = None
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
            from ..utils.exceptions import TonConnectError
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

    @property
    def normalized_hash(self) -> str:
        """
        Computes the normalized hash of the Cell object derived from the BOC.

        :return: The hexadecimal representation of the Cell's normalized hash.
        """
        message = MessageAny.deserialize(self.cell.begin_parse())
        return normalize_hash(message).hex()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> SendTransactionResponse:
        """
        Creates a SendTransactionResponse instance from a dictionary.

        :param data: A dictionary containing the transaction response data.
        :return: An instance of SendTransactionResponse.
        """
        return cls(id=data.get("id"), _boc=data.get("result"))

    def to_dict(self) -> Dict[str, Any]:
        """
        Converts the SendTransactionResponse instance into a dictionary format.

        :return: A dictionary representation of the SendTransactionResponse.
        """
        return {"id": self.id, "boc": self._boc}


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


@dataclass
class SignDataPayloadText:
    text: str
    type: str = "text"

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> SignDataPayloadText:
        return cls(
            text=data["text"],
        )

    def to_dict(self):
        return {
            "type": self.type,
            "text": self.text
        }


@dataclass
class SignDataPayloadBinary:
    bytes: bytes
    type: str = "binary"

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> SignDataPayloadBinary:
        return cls(
            bytes=base64.b64decode(data["bytes"]),
        )

    def to_dict(self):
        return {
            "type": self.type,
            "bytes": base64.b64encode(self.bytes).decode(),
        }


@dataclass
class SignDataPayloadCell:
    schema: str
    cell: Cell
    type: str = "cell"

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> SignDataPayloadCell:
        return cls(
            schema=data["schema"],
            cell=Cell.one_from_boc(base64.b64decode(data["cell"])),
        )

    def to_dict(self):
        return {
            "type": self.type,
            "schema": self.schema,
            "cell": boc_to_base64_string(self.cell.to_boc()),
        }


SignDataPayload = Union[
    SignDataPayloadText,
    SignDataPayloadBinary,
    SignDataPayloadCell
]


@dataclass
class SignDataResult:
    signature: Union[str, bytes]
    address: str
    timestamp: int
    domain: str
    payload: SignDataPayload

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> SignDataResult:
        payload_data = data["payload"]
        payload_type = payload_data.get("type")

        payload: Union[
            SignDataPayloadText,
            SignDataPayloadBinary,
            SignDataPayloadCell
        ]
        if payload_type == "text":
            payload = SignDataPayloadText.from_dict(payload_data)
        elif payload_type == "binary":
            payload = SignDataPayloadBinary.from_dict(payload_data)
        elif payload_type == "cell":
            payload = SignDataPayloadCell.from_dict(payload_data)
        else:
            raise ValueError(f"Unknown payload type: {payload_type}")

        signature = data.get("signature")
        if signature is None:
            raise ValueError("Signature is missing")

        return cls(
            signature=base64.b64decode(signature),
            address=data["address"],
            timestamp=data["timestamp"],
            domain=data["domain"],
            payload=payload,
        )

    def to_dict(self) -> Dict[str, Any]:
        if isinstance(self.signature, bytes):
            self.signature = base64.b64encode(self.signature).decode()

        return {
            "signature": self.signature,
            "address": self.address,
            "timestamp": self.timestamp,
            "domain": self.domain,
            "payload": self.payload.to_dict(),
        }


@dataclass
class SignDataResponse:
    id: str
    result: SignDataResult

    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        return SignDataResponse(
            id=data["id"],
            result=SignDataResult.from_dict(data["result"]),
        )

    def verify_sign_data(self, public_key: Union[str, bytes]) -> bool:
        from ..utils.verifiers import verify_sign_data

        return verify_sign_data(
            public_key=public_key,
            params=self.result,
        )


@dataclass
class SignDataRequest(Request):
    """
    Represents a request to sign data using the wallet.
    """
    params: List[SignDataPayload] = field(default_factory=list)
    id: Optional[int] = None
    method: str = "signData"

    def to_dict(self) -> Dict[str, Any]:
        """
        Converts the SignDataRpcRequest instance into a dictionary format suitable for JSON serialization.

        :return: A dictionary representation of the SignDataRequest.
        """
        return {
            "id": str(self.id) if self.id is not None else None,
            "method": self.method,
            "params": [json.dumps(payload.to_dict()) for payload in self.params],
        }
