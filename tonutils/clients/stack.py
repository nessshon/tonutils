import typing as t
from abc import ABC, abstractmethod


class StackCodec(ABC):
    """Abstract base for TVM stack encoding/decoding."""

    @classmethod
    @abstractmethod
    def decode(cls, raw: t.List[t.Any]) -> t.List[t.Any]:
        """Decode raw stack data to Python values.

        :param raw: Provider-specific raw stack items.
        :return: Decoded Python values.
        """

    @classmethod
    @abstractmethod
    def encode(cls, items: t.List[t.Any]) -> t.List[t.Any]:
        """Encode Python values to provider-specific wire format.

        :param items: Python stack values.
        :return: Encoded stack items.
        """
