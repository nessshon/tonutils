from __future__ import annotations

import base64

from ton_core import Address, Cell, Slice

from tests.constants import ZERO_ADDRESS
from tonutils.clients import TonapiClient, ToncenterClient
from tonutils.clients.lite.mixin import LiteMixin


class TestTonapiEncode:
    def test_int(self):
        result = TonapiClient._encode_stack([42])
        assert result == [{"type": "int257", "value": "0x2a"}]

    def test_null(self):
        result = TonapiClient._encode_stack([None])
        assert result == [{"type": "null", "value": ""}]

    def test_address(self):
        result = TonapiClient._encode_stack([Address(ZERO_ADDRESS)])
        assert len(result) == 1
        assert result[0]["type"] == "slice"
        assert result[0]["value"] == ZERO_ADDRESS

    def test_cell(self):
        result = TonapiClient._encode_stack([Cell.empty()])
        assert len(result) == 1
        assert result[0]["type"] == "cell_boc_base64"
        assert isinstance(result[0]["value"], str)

    def test_slice(self):
        result = TonapiClient._encode_stack([Cell.empty().to_slice()])
        assert len(result) == 1
        assert result[0]["type"] == "slice_boc_hex"
        assert isinstance(result[0]["value"], str)

    def test_mixed(self):
        result = TonapiClient._encode_stack([42, None, Address(ZERO_ADDRESS), Cell.empty(), Cell.empty().to_slice()])
        assert len(result) == 5
        assert result[0]["type"] == "int257"
        assert result[1]["type"] == "null"
        assert result[2]["type"] == "slice"
        assert result[3]["type"] == "cell_boc_base64"
        assert result[4]["type"] == "slice_boc_hex"


class TestTonapiDecode:
    def test_int(self):
        assert TonapiClient._decode_stack([{"type": "num", "num": "0x2a"}]) == [42]

    def test_null(self):
        assert TonapiClient._decode_stack([{"type": "null"}]) == [None]

    def test_nan(self):
        assert TonapiClient._decode_stack([{"type": "nan"}]) == [None]

    def test_cell(self):
        boc = Cell.empty().to_boc().hex()
        result = TonapiClient._decode_stack([{"type": "cell", "cell": boc}])
        assert len(result) == 1

    def test_slice(self):
        boc = Cell.empty().to_boc().hex()
        result = TonapiClient._decode_stack([{"type": "slice", "slice": boc}])
        assert len(result) == 1

    def test_address_from_slice(self):
        addr_boc = Address(ZERO_ADDRESS).to_cell().to_boc().hex()
        result = TonapiClient._decode_stack([{"type": "slice", "slice": addr_boc}])
        assert len(result) == 1
        assert isinstance(result[0], Address)

    def test_nested(self):
        result = TonapiClient._decode_stack(
            [{"type": "tuple", "tuple": [{"type": "num", "num": "0x1"}, {"type": "num", "num": "0x2"}]}]
        )
        assert result == [[1, 2]]

    def test_mixed(self):
        boc = Cell.empty().to_boc().hex()
        result = TonapiClient._decode_stack(
            [
                {"type": "num", "num": "0x1"},
                {"type": "null"},
                {"type": "cell", "cell": boc},
                {"type": "slice", "slice": boc},
            ]
        )
        assert len(result) == 4
        assert result[0] == 1
        assert result[1] is None


class TestToncenterEncode:
    def test_int(self):
        assert ToncenterClient._encode_stack([42]) == [["num", "42"]]

    def test_address(self):
        result = ToncenterClient._encode_stack([Address(ZERO_ADDRESS)])
        assert len(result) == 1
        assert result[0][0] == "tvm.Slice"

    def test_cell(self):
        result = ToncenterClient._encode_stack([Cell.empty()])
        assert result[0][0] == "tvm.Cell"

    def test_slice(self):
        result = ToncenterClient._encode_stack([Cell.empty().to_slice()])
        assert result[0][0] == "tvm.Slice"

    def test_nested_list(self):
        result = ToncenterClient._encode_stack([[1, 2]])
        assert result[0][0] == "tuple"
        assert len(result[0][1]["elements"]) == 2

    def test_mixed(self):
        result = ToncenterClient._encode_stack([42, Address(ZERO_ADDRESS), Cell.empty(), Cell.empty().to_slice()])
        assert len(result) == 4


class TestToncenterDecode:
    def test_int(self):
        assert ToncenterClient._decode_stack([["num", "0x2a"]]) == [42]

    def test_null(self):
        assert ToncenterClient._decode_stack([["null", None]]) == [None]

    def test_cell(self):
        boc_b64 = base64.b64encode(Cell.empty().to_boc()).decode()
        result = ToncenterClient._decode_stack([["tvm.Cell", {"bytes": boc_b64}]])
        assert len(result) == 1

    def test_slice(self):
        boc_b64 = base64.b64encode(Cell.empty().to_boc()).decode()
        result = ToncenterClient._decode_stack([["tvm.Slice", {"bytes": boc_b64}]])
        assert len(result) == 1

    def test_address_from_slice(self):
        addr_boc_b64 = base64.b64encode(Address(ZERO_ADDRESS).to_cell().to_boc()).decode()
        result = ToncenterClient._decode_stack([["tvm.Slice", {"bytes": addr_boc_b64}]])
        assert len(result) == 1
        assert isinstance(result[0], Address)

    def test_nested(self):
        result = ToncenterClient._decode_stack(
            [["tuple", {"elements": [{"@type": "tvm.stackEntryNumber", "number": {"number": "0x1"}}]}]]
        )
        assert result == [[1]]

    def test_mixed(self):
        boc_b64 = base64.b64encode(Cell.empty().to_boc()).decode()
        result = ToncenterClient._decode_stack(
            [
                ["num", "0x1"],
                ["null", None],
                ["tvm.Cell", {"bytes": boc_b64}],
                ["tvm.Slice", {"bytes": boc_b64}],
            ]
        )
        assert len(result) == 4
        assert result[0] == 1
        assert result[1] is None


class TestLiteEncode:
    def test_int(self):
        assert LiteMixin._encode_stack([42]) == [42]

    def test_address(self):
        result = LiteMixin._encode_stack([Address(ZERO_ADDRESS)])
        assert len(result) == 1
        assert isinstance(result[0], Slice)

    def test_cell(self):
        cell = Cell.empty()
        result = LiteMixin._encode_stack([cell])
        assert result[0] is cell

    def test_slice(self):
        sl = Cell.empty().to_slice()
        result = LiteMixin._encode_stack([sl])
        assert result[0] is sl

    def test_nested_list(self):
        result = LiteMixin._encode_stack([[1, 2]])
        assert isinstance(result[0], list)
        assert result[0] == [1, 2]

    def test_mixed(self):
        result = LiteMixin._encode_stack([42, Address(ZERO_ADDRESS), Cell.empty(), Cell.empty().to_slice()])
        assert len(result) == 4


class TestLiteDecode:
    def test_int(self):
        assert LiteMixin._decode_stack([42]) == [42]

    def test_null(self):
        assert LiteMixin._decode_stack([None]) == [None]

    def test_cell(self):
        result = LiteMixin._decode_stack([Cell.empty()])
        assert len(result) == 1

    def test_slice(self):
        result = LiteMixin._decode_stack([Cell.empty().to_slice()])
        assert len(result) == 1

    def test_address(self):
        addr = Address(ZERO_ADDRESS)
        result = LiteMixin._decode_stack([addr])
        assert len(result) == 1
        assert isinstance(result[0], Cell)

    def test_nested(self):
        result = LiteMixin._decode_stack([[1, 2]])
        assert result == [[1, 2]]

    def test_mixed(self):
        result = LiteMixin._decode_stack([42, None, Cell.empty(), Cell.empty().to_slice(), Address(ZERO_ADDRESS)])
        assert len(result) == 5
        assert result[0] == 42
        assert result[1] is None
        assert isinstance(result[4], Cell)
