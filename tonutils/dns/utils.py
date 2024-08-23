import hashlib
from typing import Union


def hash_name(name: str) -> int:
    return int(hashlib.sha256(name.encode("utf-8")).hexdigest(), 16)


class ByteHexConverter:
    def __init__(self, data: Union[bytes, bytearray, str]) -> None:
        self.bytes = self._convert_to_bytes(data)

    @staticmethod
    def _convert_to_bytes(data):
        if isinstance(data, (bytes, bytearray)):
            if len(data) != 32:
                raise ValueError("Invalid bytes length")
            return data

        if isinstance(data, str):
            if len(data) != 64:
                raise ValueError("Invalid hex length")
            return bytes.fromhex(data)

        raise TypeError("Unsupported type")

    def to_hex(self):
        return self.bytes.hex().zfill(64)
