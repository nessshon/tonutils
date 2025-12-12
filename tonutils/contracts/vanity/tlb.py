from __future__ import annotations

from pytoniq_core import Cell, Slice, TlbScheme, begin_cell


class VanityDeployBody(TlbScheme):
    """Message body structure for deploying contracts via Vanity."""

    def __init__(self, code: Cell, data: Cell) -> None:
        """
        Initialize Vanity deploy message body.

        :param code: Contract code cell to deploy
        :param data: Contract initial data cell
        """
        self.code = code
        self.data = data

    def serialize(self) -> Cell:
        """
        Serialize deploy body to Cell.

        Layout: code:^Cell data:^Cell

        :return: Serialized message body cell
        """
        cell = begin_cell()
        cell.store_ref(self.code)
        cell.store_ref(self.data)
        return cell.end_cell()

    @classmethod
    def deserialize(cls, cs: Slice) -> VanityDeployBody:
        """
        Deserialize deploy body from Cell slice.

        :param cs: Cell slice to deserialize from
        :return: Deserialized VanityDeployBody instance
        """
        raise NotImplementedError
