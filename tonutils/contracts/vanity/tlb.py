from __future__ import annotations

from pytoniq_core import Cell, Slice, TlbScheme, begin_cell


class VanityDeployBody(TlbScheme):
    """Message body for deploying contracts via Vanity."""

    def __init__(self, code: Cell, data: Cell) -> None:
        """
        :param code: Contract code cell.
        :param data: Contract initial data cell.
        """
        self.code = code
        self.data = data

    def serialize(self) -> Cell:
        """Serialize to `Cell`.

        TLB: `code:^Cell data:^Cell`
        """
        cell = begin_cell()
        cell.store_ref(self.code)
        cell.store_ref(self.data)
        return cell.end_cell()

    @classmethod
    def deserialize(cls, cs: Slice) -> VanityDeployBody:
        """Deserialize from `Slice`.

        :param cs: Source slice.
        """
        raise NotImplementedError
