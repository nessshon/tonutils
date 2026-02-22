import base64
import socket
import struct
import typing as t
from contextlib import suppress

from pydantic import BaseModel
from pytoniq_core import BlockIdExt

from tonutils.types import PublicKey, BinaryLike


class LiteServerID(BaseModel):
    """Liteserver public key identifier."""

    key: str


class LiteServer(BaseModel):
    """TON liteserver connection configuration.

    Attributes:
        port: TCP port number for ADNL connection.
        ip: IP address as string or signed 32-bit integer.
        id: Server public key as `LiteServerID` or raw binary.
    """

    port: int
    ip: t.Union[str, int]
    id: t.Union[LiteServerID, BinaryLike]

    @property
    def pub_key(self) -> bytes:
        """Server Ed25519 public key as bytes."""
        if isinstance(self.id, LiteServerID):
            raw: BinaryLike = self.id.key
        else:
            raw = self.id
        return PublicKey(raw).as_bytes

    @property
    def host(self) -> str:
        """IP address in dotted-decimal notation."""
        with suppress(Exception):
            packed_id = struct.pack(">i", int(self.ip))
            return socket.inet_ntoa(packed_id)
        return str(self.ip)

    @property
    def endpoint(self) -> str:
        """Host and port as `host:port` string."""
        return f"{self.host}:{self.port}"


class Block(BaseModel):
    """TON blockchain block identifier.

    Attributes:
        file_hash: Base64-encoded file hash.
        root_hash: Base64-encoded root cell hash.
        shard: Shard identifier, or `None` for masterchain.
        seqno: Block sequence number, or `None`.
        workchain: Workchain ID (-1 masterchain, 0 basechain).
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
        """Root hash as hexadecimal string."""
        return self._hash_to_hex(self.root_hash)

    @property
    def file_hash_hex(self) -> str:
        """File hash as hexadecimal string."""
        return self._hash_to_hex(self.file_hash)


class MasterchainInfo(BaseModel):
    """TON masterchain state information.

    Attributes:
        last: Latest masterchain block.
        init: Genesis / initialization block.
        state_root_hash: Base64-encoded root hash of current state.
    """

    last: Block
    init: Block
    state_root_hash: str

    @staticmethod
    def _parse_raw_block(b: Block) -> BlockIdExt:
        """Convert `Block` model to `BlockIdExt`."""
        return BlockIdExt.from_dict(b.model_dump())

    def last_block(self) -> BlockIdExt:
        """Return the latest masterchain block as `BlockIdExt`."""
        return self._parse_raw_block(self.last)

    def init_block(self) -> BlockIdExt:
        """Return the genesis block as `BlockIdExt`."""
        return self._parse_raw_block(self.init)


class GlobalConfig(BaseModel):
    """TON global network configuration.

    Attributes:
        liteservers: Available liteserver endpoints.
    """

    liteservers: t.List[LiteServer]
