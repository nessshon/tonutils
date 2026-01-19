import typing as t

from pydantic import BaseModel


class LiteServer(BaseModel):
    index: int
    host: str
    port: int


class BlockInfo(BaseModel):
    seqno: int
    txs_count: int


class LiteServerStatus(BaseModel):
    server: LiteServer
    version: t.Optional[int] = None
    time: t.Optional[int] = None
    ping_ms: t.Optional[int] = None
    connect_ms: t.Optional[int] = None
    request_ms: t.Optional[int] = None
    last_mc_block: t.Optional[BlockInfo] = None
    last_bc_block: t.Optional[BlockInfo] = None
    archive_from: t.Optional[int] = None
    last_error: t.Optional[str] = None
