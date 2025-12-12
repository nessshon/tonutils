import base64
import socket
import struct
import typing as t
from contextlib import suppress

from pydantic import BaseModel
from pytoniq_core import BlockIdExt

from tonutils.types import PublicKey, BinaryLike


class LiteServerID(BaseModel):
    """
    Liteserver public key identifier.

    Wraps the server's Ed25519 public key used for ADNL authentication.
    """

    key: str


class LiteServer(BaseModel):
    """
    TON liteserver connection configuration.

    Contains all information needed to connect to a TON liteserver via ADNL:
    - Network address (IP and port)
    - Server's public key for authentication

    Attributes:
        port: TCP port number for ADNL connection
        ip: IP address as string or signed 32-bit integer
        id: Server public key as LiteServerID object or raw binary
    """

    port: int
    ip: t.Union[str, int]
    id: t.Union[LiteServerID, BinaryLike]

    @property
    def pub_key(self) -> bytes:
        """
        Get the server's Ed25519 public key as bytes.

        Extracts and normalizes the public key from either LiteServerID
        or raw binary format.
        """
        if isinstance(self.id, LiteServerID):
            raw: BinaryLike = self.id.key
        else:
            raw = self.id
        return PublicKey(raw).as_bytes

    @property
    def host(self) -> str:
        """
        Get the server's IP address as a string.

        Converts integer IP representation (from global config) to
        dotted-decimal notation. Falls back to string representation
        if conversion fails.
        """
        with suppress(Exception):
            packed_id = struct.pack(">i", int(self.ip))
            return socket.inet_ntoa(packed_id)
        return str(self.ip)


class Block(BaseModel):
    """
    TON blockchain block identifier and metadata.

    Represents a block in the TON blockchain with its unique identifiers
    and shard/workchain location. Used for block queries and state tracking.

    Attributes:
        file_hash: Base64-encoded hash of the block's file representation
        root_hash: Base64-encoded hash of the block's root cell
        shard: Shard identifier (optional, None for masterchain blocks)
        seqno: Block sequence number (optional)
        workchain: Workchain ID (-1 for masterchain, 0 for basechain)
    """

    file_hash: str
    root_hash: str
    shard: t.Optional[int] = None
    seqno: t.Optional[int] = None
    workchain: int

    @staticmethod
    def _hash_to_hex(v: str) -> str:
        """Convert base64-encoded hash to hexadecimal."""
        return base64.b64decode(v).hex()

    @property
    def root_hash_hex(self) -> str:
        """Get the block's root hash as hexadecimal string."""
        return self._hash_to_hex(self.root_hash)

    @property
    def file_hash_hex(self) -> str:
        """Get the block's file hash as hexadecimal string."""
        return self._hash_to_hex(self.file_hash)


class MasterchainInfo(BaseModel):
    """
    TON masterchain state information.

    Contains references to key masterchain blocks:
    - Latest block: current blockchain state
    - Init block: genesis/initialization block
    - State root hash: merkle root of the current state

    This information is essential for synchronizing with the blockchain
    and verifying state consistency.

    Attributes:
        last: Latest masterchain block
        init: Genesis/initialization block
        state_root_hash: Base64-encoded root hash of current state
    """

    last: Block
    init: Block
    state_root_hash: str

    @staticmethod
    def _parse_raw_block(b: Block) -> BlockIdExt:
        """Convert Block model to BlockIdExt."""
        return BlockIdExt.from_dict(b.model_dump())

    def last_block(self) -> BlockIdExt:
        """Get the latest masterchain block as BlockIdExt."""
        return self._parse_raw_block(self.last)

    def init_block(self) -> BlockIdExt:
        """Get the initialization (genesis) block as BlockIdExt."""
        return self._parse_raw_block(self.init)


class GlobalConfig(BaseModel):
    """
    TON global network configuration.

    Contains the list of available liteservers for a TON network
    (mainnet or testnet). This configuration is typically loaded from
    global config JSON files published by the TON Foundation.

    Attributes:
        liteservers: List of available liteserver endpoints
    """

    liteservers: t.List[LiteServer]
