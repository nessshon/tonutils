import base64
import typing as t

from nacl.signing import SigningKey

from ..exceptions import KeyValidationError

KeyLike = t.Union[str, int, bytes]


class Key:

    def __init__(self, raw: KeyLike, size: int = 32) -> None:
        self._size = size
        self._bytes = self._parse(raw)

    @property
    def size(self) -> int:
        return self._size

    def _parse(self, value: t.Union[t.Any]) -> bytes:
        if isinstance(value, bytes):
            return value
        if isinstance(value, int):
            length = max(1, (value.bit_length() + 7) // 8)
            return value.to_bytes(length, "big")
        if isinstance(value, str):
            s = value.strip()
            if s.lower().startswith("0x"):
                return int(s, 16).to_bytes(self._size, "big")
            try:
                return base64.b64decode(s, validate=True)
            except (Exception,):
                n = int(s, 10)
                length = max(1, (n.bit_length() + 7) // 8)
                return n.to_bytes(length, "big")
        raise KeyValidationError(f"Invalid key type: {type(value).__name__}")

    @property
    def bytes(self) -> bytes:
        return self._bytes.rjust(self._size, b"\x00")

    @property
    def int(self) -> int:
        return int.from_bytes(self.bytes, byteorder="big")

    @property
    def hex(self) -> str:
        return self.bytes.hex()

    @property
    def base64(self) -> str:
        return base64.b64encode(self.bytes).decode()

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Key) and self.bytes == other.bytes

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}<{self.base64!r}>"


class PublicKey(Key):

    def __init__(self, raw: t.Union[int, str, bytes]) -> None:
        super().__init__(raw, size=32)


class PrivateKey(Key):

    def __init__(self, raw: KeyLike) -> None:
        raw_bytes = self._parse(raw)

        if len(raw_bytes) == 32:
            signing_key = SigningKey(raw_bytes)
            raw_bytes += signing_key.verify_key.encode()
        elif len(raw_bytes) == 64:
            pass
        else:
            raise KeyValidationError("Private key must be 32 or 64 bytes")

        self._public_part = raw_bytes[32:]
        super().__init__(raw_bytes[:32], size=32)

    @property
    def public_key(self) -> PublicKey:
        return PublicKey(self._public_part)

    @property
    def keypair(self) -> Key:
        raw = self.bytes + self.public_key.bytes
        return Key(raw, size=64)
