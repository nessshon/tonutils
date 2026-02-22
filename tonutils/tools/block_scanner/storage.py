import typing as t


class BlockScannerStorageProtocol(t.Protocol):
    """Storage for `BlockScanner` progress (masterchain seqno)."""

    async def get_mc_seqno(self) -> t.Optional[int]:
        """Return last processed masterchain seqno, or `None`."""

    async def set_mc_seqno(self, seqno: int) -> None:
        """Persist last processed masterchain seqno.

        :param seqno: Masterchain sequence number.
        """
