from __future__ import annotations

import base64
import socket
import struct
import typing as t
from contextlib import suppress
from dataclasses import dataclass, asdict

from pytoniq_core import BlockIdExt
from tonutils.types import PublicKey, BinaryLike


@dataclass
class LiteServerID:
    """Liteserver public key identifier."""

    key: str


@dataclass
class LiteServer:
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

    @classmethod
    def from_dict(cls, data: t.Dict[str, t.Any]) -> LiteServer:
        """Create from a dictionary, resolving nested ``id``."""
        id_raw = data.get("id")
        if isinstance(id_raw, dict):
            id_val: t.Union[LiteServerID, BinaryLike] = LiteServerID(**id_raw)
        else:
            id_val = id_raw
        return cls(port=data["port"], ip=data["ip"], id=id_val)


@dataclass
class Block:
    """TON blockchain block identifier.

    Attributes:
        file_hash: Base64-encoded file hash.
        root_hash: Base64-encoded root cell hash.
        workchain: Workchain ID (-1 masterchain, 0 basechain).
        shard: Shard identifier, or `None` for masterchain.
        seqno: Block sequence number, or `None`.
    """

    file_hash: str
    root_hash: str
    workchain: int
    shard: t.Optional[int] = None
    seqno: t.Optional[int] = None

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


@dataclass
class MasterchainInfo:
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
        """Convert ``Block`` to ``BlockIdExt``."""
        return BlockIdExt.from_dict(asdict(b))

    def last_block(self) -> BlockIdExt:
        """Return the latest masterchain block as ``BlockIdExt``."""
        return self._parse_raw_block(self.last)

    def init_block(self) -> BlockIdExt:
        """Return the genesis block as ``BlockIdExt``."""
        return self._parse_raw_block(self.init)


@dataclass
class GlobalConfig:
    """TON global network configuration.

    Attributes:
        liteservers: Available liteserver endpoints.
    """

    liteservers: t.List[LiteServer]

    @classmethod
    def from_dict(cls, data: t.Dict[str, t.Any]) -> GlobalConfig:
        """Create from a dictionary, resolving nested liteservers."""
        raw_ls = data.get("liteservers")
        if not isinstance(raw_ls, list):
            raise TypeError(
                f"Expected list for 'liteservers', got {type(raw_ls).__name__}"
            )
        servers = [
            LiteServer.from_dict(item) if isinstance(item, dict) else item
            for item in raw_ls
        ]
        return cls(liteservers=servers)
