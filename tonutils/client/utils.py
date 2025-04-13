from contextlib import suppress
from typing import Any, List, Optional, Union

from pytoniq_core import Address, Cell, Slice, begin_cell

from ._base import Client
from ..utils import boc_to_base64_string


class RunGetMethodResult:
    """
    Supports parsing items from various sources such as Toncenter, TonAPI, and Lite.
    """

    def __init__(self, client: Client, stack: Optional[List[Any]] = None) -> None:
        """
        Initializes the result handler with a client and an optional stack of items.

        :param client: The client instance.
        :param stack: A list of stack items to be processed. Defaults to an empty list if not provided.
        """
        self.client = client
        self.stack = stack or []

    @classmethod
    def _process_item(cls, value: Union[Cell, Slice]) -> Union[Address, Cell, Slice, None]:
        """
        Attempts to parse an Address from a Cell or Slice. Returns the original value if parsing fails.

        :param value: The value (Cell or Slice) to process.
        :return: The processed value, potentially an Address or the original value if parsing fails.
        """
        with suppress(Exception):
            copied_cell = value.copy() if isinstance(value, Cell) else value.to_cell()
            parsed = copied_cell.begin_parse()
            tag = parsed.load_uint(2)

            if tag == 0 and not parsed.bits:
                return None
            if tag == 2 and len(parsed.bits) == 265:
                return copied_cell.begin_parse().load_address()

        return value

    @classmethod
    def _parse_item(cls, item: Union[dict, list], source: str) -> Any:
        """
        Parses a single item from the stack based on its type and the source format (toncenter/tonapi).

        :param item: The item to be parsed.
        :param source: The source format ('toncenter', 'tonapi', etc.).
        :return: The parsed value, which could be a processed Cell, Slice, or other data type.
        """
        if isinstance(item, list):
            item = {"type": item[0], "value": item[1]}

        source_key_map = {
            "toncenter": {"num": "value", "cell": "value", "slice": "value"},
            "tonapi": {"num": "num", "cell": "cell", "slice": "slice"}
        }

        parsers = {
            "num": lambda v: int(v, 16),
            "cell": Cell.one_from_boc,
            "slice": Slice.one_from_boc
        }

        type_ = item.get("type")
        if type_ not in parsers or source not in source_key_map:
            raise ValueError(f"Unknown type or source: type={type_}, source={source}")

        raw_value = item.get(source_key_map[source][type_])
        parsed = parsers[type_](raw_value)

        return cls._process_item(parsed) if isinstance(parsed, (Cell, Slice)) else parsed

    def parse_from_toncenter(self) -> List[Any]:
        """
        Parses stack items from the Toncenter source.

        :return: A list of parsed items from Toncenter.
        """
        return [self._parse_item(item, "toncenter") for item in self.stack]

    def parse_from_tonapi(self) -> List[Any]:
        """
        Parses stack items from the TonAPI source.

        :return: A list of parsed items from TonAPI.
        """
        return [self._parse_item(item, "tonapi") for item in self.stack]

    def parse_from_lite(self) -> List[Any]:
        """
        Parses stack items for the Lite format (no transformation other than for Cells and Slices).

        :return: A list of stack items, potentially processed if they are Cell or Slice.
        """
        return [self._process_item(item) if isinstance(item, (Cell, Slice)) else item for item in self.stack]


class RunGetMethodStack:
    """
    Converts items into the appropriate format for each target.
    """

    def __init__(self, client: Client, stack: Optional[List[Any]] = None) -> None:
        """
        Initializes the stack handler with a client and an optional stack of items.

        :param client: The client instance.
        :param stack: A list of stack items to be processed. Defaults to an empty list if not provided.
        """
        self.client = client
        self.stack = stack or []

    def pack_to_toncenter(self) -> List[Any]:
        """
        Packs stack items into the format expected by Toncenter.

        :return: A list of packed items for Toncenter.
        """
        return [self._pack_item("toncenter", item) for item in self.stack]

    def pack_to_tonapi(self) -> List[Any]:
        """
        Packs stack items into the format expected by TonAPI.

        :return: A list of packed items for TonAPI.
        """
        return [self._pack_item("tonapi", item) for item in self.stack]

    def pack_to_lite(self) -> List[Any]:
        """
        Packs stack items into the format expected by LiteServer.

        :return: A list of packed items for LiteServer.
        """
        return [self._pack_item("lite", item) for item in self.stack]

    @classmethod
    def _pack_item(cls, target: str, item: Any) -> Any:
        """
        Packs a single item based on the target format (Toncenter, TonAPI, Lite).

        :param target: The target format ('toncenter', 'tonapi', 'lite').
        :param item: The item to be packed.
        :return: The packed item in the appropriate format for the target.
        """
        packers = {
            "toncenter": {
                int: lambda x: x,
                Cell: lambda x: boc_to_base64_string(x.to_boc()),
                Slice: lambda x: boc_to_base64_string(x.to_cell().to_boc()),
                Address: lambda x: boc_to_base64_string(begin_cell().store_address(x).end_cell().to_boc())
            },
            "tonapi": {
                int: lambda x: x,
                Cell: lambda x: x.to_boc().hex(),
                Slice: lambda x: x.to_cell().to_boc().hex(),
                Address: lambda x: x.to_str()
            },
            "lite": {
                Cell: lambda x: x.begin_parse(),
                Address: lambda x: x.to_cell().to_slice(),
                Any: lambda x: x
            }
        }

        pack_fn = packers.get(target, {}).get(type(item), None)
        if not pack_fn:
            if target == "lite":
                return item
            raise ValueError(f"Unsupported item type '{type(item)}' for target '{target}'")

        return pack_fn(item)
