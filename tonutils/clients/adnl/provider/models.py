import base64
import socket
import struct
import typing as t
from contextlib import suppress

from pydantic import BaseModel
from pytoniq_core import BlockIdExt

from tonutils.types import PublicKey, BinaryLike


class LiteServerID(BaseModel):
    key: str


class LiteServer(BaseModel):
    port: int
    ip: t.Union[str, int]
    id: t.Union[LiteServerID, BinaryLike]

    @property
    def pub_key(self) -> bytes:
        if isinstance(self.id, LiteServerID):
            raw: BinaryLike = self.id.key
        else:
            raw = self.id
        return PublicKey(raw).as_bytes

    @property
    def host(self) -> str:
        with suppress(Exception):
            packed_id = struct.pack(">i", int(self.ip))
            return socket.inet_ntoa(packed_id)
        return str(self.ip)


class Block(BaseModel):
    file_hash: str
    root_hash: str
    shard: t.Optional[int] = None
    seqno: t.Optional[int] = None
    workchain: int

    @staticmethod
    def _hash_to_hex(v: str) -> str:
        return base64.b64decode(v).hex()

    @property
    def root_hash_hex(self) -> str:
        return self._hash_to_hex(self.root_hash)

    @property
    def file_hash_hex(self) -> str:
        return self._hash_to_hex(self.file_hash)


class MasterchainInfo(BaseModel):
    last: Block
    init: Block
    state_root_hash: str

    @staticmethod
    def _parse_raw_block(b: Block) -> BlockIdExt:
        return BlockIdExt.from_dict(b.model_dump())

    def last_block(self) -> BlockIdExt:
        return self._parse_raw_block(self.last)

    def init_block(self) -> BlockIdExt:
        return self._parse_raw_block(self.init)


class GlobalConfig(BaseModel):
    liteservers: t.List[LiteServer]
