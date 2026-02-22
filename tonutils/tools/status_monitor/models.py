import typing as t

from pydantic import BaseModel


class LiteServer(BaseModel):
    """Liteserver identity for status display.

    Attributes:
        index: Positional index in the config.
        host: IP address string.
        port: TCP port number.
    """

    index: int
    host: str
    port: int


class BlockInfo(BaseModel):
    """Block summary for status display.

    Attributes:
        seqno: Block sequence number.
        txs_count: Number of transactions in the block.
    """

    seqno: int
    txs_count: int


class LiteServerStatus(BaseModel):
    """Snapshot of a single liteserver's health.

    Attributes:
        server: Liteserver identity.
        version: Server software version, or `None`.
        time: Server unix timestamp, or `None`.
        ping_ms: Last ping latency in ms, or `None`.
        connect_ms: Connection RTT in ms, or `None`.
        request_ms: Request RTT in ms, or `None`.
        last_mc_block: Latest masterchain block info, or `None`.
        last_bc_block: Latest basechain block info, or `None`.
        archive_from: Earliest archive unix timestamp, or `None`.
        last_error: Most recent error message, or `None`.
    """

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
