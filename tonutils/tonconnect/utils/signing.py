import abc
import hashlib
import hmac
import secrets
import time
import typing as t
import zlib

from nacl.exceptions import BadSignatureError
from nacl.signing import VerifyKey
from pytoniq_core import Address, Cell, StateInit, begin_cell

from tonutils.contracts import (
    BaseWalletData,
    WalletV1Data,
    WalletV1R1,
    WalletV1R2,
    WalletV1R3,
    WalletV2Data,
    WalletV2R1,
    WalletV2R2,
    WalletV3Data,
    WalletV3R1,
    WalletV3R2,
    WalletV4Data,
    WalletV4R1,
    WalletV4R2,
    WalletV5Beta,
    WalletV5BetaData,
    WalletV5Data,
    WalletV5R1,
)
from tonutils.tonconnect.models import (
    SignDataPayloadBinary,
    SignDataPayloadCell,
    SignDataPayloadText,
    SignDataPayloadDto,
    TonProofPayloadDto,
)
from tonutils.types import PublicKey
from tonutils.utils import encode_dns_name

__all__ = [
    "VerifySignData",
    "VerifyTonProof",
    "create_ton_proof_payload",
    "verify_ton_proof_payload",
]


_WALLET_DATA_MODELS: t.Dict[Cell, t.Type[BaseWalletData]] = {
    WalletV1R1.get_default_code(): WalletV1Data,
    WalletV1R2.get_default_code(): WalletV1Data,
    WalletV1R3.get_default_code(): WalletV1Data,
    WalletV2R1.get_default_code(): WalletV2Data,
    WalletV2R2.get_default_code(): WalletV2Data,
    WalletV3R1.get_default_code(): WalletV3Data,
    WalletV3R2.get_default_code(): WalletV3Data,
    WalletV4R1.get_default_code(): WalletV4Data,
    WalletV4R2.get_default_code(): WalletV4Data,
    WalletV5R1.get_default_code(): WalletV5Data,
    WalletV5Beta.get_default_code(): WalletV5BetaData,
}

_TDTO = t.TypeVar("_TDTO", TonProofPayloadDto, SignDataPayloadDto)
_GetWalletPublicKey = t.Callable[[Address], t.Awaitable[t.Optional[PublicKey]]]


def _u32_be(value: int) -> bytes:
    """Encode unsigned 32-bit integer (big-endian)."""
    return int(value).to_bytes(4, "big")


def _u64_be(value: int) -> bytes:
    """Encode unsigned 64-bit integer (big-endian)."""
    return int(value).to_bytes(8, "big")


def _u32_le(value: int) -> bytes:
    """Encode unsigned 32-bit integer (little-endian)."""
    return int(value).to_bytes(4, "little")


def _u64_le(value: int) -> bytes:
    """Encode unsigned 64-bit integer (little-endian)."""
    return int(value).to_bytes(8, "little")


def _i32_be(value: int) -> bytes:
    """Encode signed 32-bit integer (big-endian)."""
    return int(value).to_bytes(4, "big", signed=True)


class _BaseVerify(abc.ABC, t.Generic[_TDTO]):
    """Base verifier for TON Connect signed payload DTOs."""

    TON_CONNECT_PREFIX: bytes

    def __init__(self, dto: _TDTO) -> None:
        """
        :param dto: Parsed request payload DTO.
        """
        self.dto: _TDTO = dto

    @property
    @abc.abstractmethod
    def address(self) -> Address:
        """Wallet address that must be proven."""

    @property
    @abc.abstractmethod
    def domain(self) -> str:
        """dApp domain that must match the signed domain."""

    @property
    @abc.abstractmethod
    def public_key(self) -> PublicKey:
        """Public key declared by the wallet."""

    @property
    @abc.abstractmethod
    def signature(self) -> bytes:
        """Ed25519 signature bytes."""

    @property
    @abc.abstractmethod
    def signing_message(self) -> bytes:
        """Canonical message bytes the wallet signs."""

    @property
    @abc.abstractmethod
    def timestamp(self) -> int:
        """Unix timestamp when the wallet produced the signature."""

    @property
    @abc.abstractmethod
    def wallet_state_init(self) -> StateInit:
        """Wallet `StateInit` used to derive address and public key."""

    async def verify(
        self,
        allowed_domains: t.List[str],
        valid_auth_time: int = 15 * 60,
        get_wallet_public_key: t.Optional[_GetWalletPublicKey] = None,
    ) -> bool:
        """Verify payload DTO authenticity.

        :param allowed_domains: Permitted domain strings.
        :param valid_auth_time: Max age of signature in seconds.
        :param get_wallet_public_key: Async resolver for unknown wallet codes, or `None`.
        :return: `True` if all checks pass.
        :raises BadSignatureError: If any validation step fails.
        """
        await self._resolve_public_key(
            wallet_state_init=self.wallet_state_init,
            address=self.address,
            wanted_public_key=self.public_key,
            get_wallet_public_key=get_wallet_public_key,
        )

        self._ensure_address_matches(self.address, self.wallet_state_init)
        self._ensure_timestamp_valid(self.timestamp, valid_auth_time)
        self._ensure_domain_allowed(self.domain, allowed_domains)

        verify_key = VerifyKey(self.public_key.as_bytes)
        return verify_key.verify(self.signing_message, self.signature) is not None

    @classmethod
    def _ensure_domain_allowed(cls, domain: str, allowed_domains: t.List[str]) -> None:
        """Ensure the domain is in the allow-list.

        :param domain: Domain from the signed payload.
        :param allowed_domains: Backend allow-list.
        :raises BadSignatureError: If the domain is not allowed.
        """
        if domain not in allowed_domains:
            raise BadSignatureError("Domain not allowed")

    @classmethod
    def _ensure_timestamp_valid(cls, timestamp: int, valid_auth_time: int) -> None:
        """Ensure the timestamp is within the allowed window.

        :param timestamp: Signed unix timestamp.
        :param valid_auth_time: Max age in seconds.
        :raises BadSignatureError: If timestamp is out of range.
        """
        now = int(time.time())
        if timestamp < now - valid_auth_time:
            raise BadSignatureError("Signature expired")
        if timestamp > now + 60:
            raise BadSignatureError("Invalid timestamp")

    @classmethod
    def _ensure_address_matches(cls, address: Address, state_init: StateInit) -> None:
        """Ensure address matches `StateInit`.

        :param address: Wallet address from payload.
        :param state_init: Wallet `StateInit` from payload.
        :raises BadSignatureError: If derivation fails or address mismatches.
        """
        try:
            st_cell = state_init.serialize()
            derived = Address((address.wc, st_cell.hash))
        except Exception as e:
            raise BadSignatureError("Cannot validate address against state_init") from e

        if derived != address:
            raise BadSignatureError("Address does not match wallet_state_init")

    @classmethod
    async def _resolve_public_key(
        cls,
        wallet_state_init: StateInit,
        address: Address,
        wanted_public_key: PublicKey,
        get_wallet_public_key: t.Optional[_GetWalletPublicKey],
    ) -> PublicKey:
        """Resolve and validate the wallet public key.

        :param wallet_state_init: Wallet `StateInit`.
        :param address: Wallet address (for external resolver).
        :param wanted_public_key: Public key declared by the wallet.
        :param get_wallet_public_key: Async resolver, or `None`.
        :return: Resolved public key.
        :raises BadSignatureError: If key cannot be resolved or mismatches.
        """
        public_key = cls._try_parse_public_key(wallet_state_init)
        if public_key is None and get_wallet_public_key is not None:
            public_key = await get_wallet_public_key(address)

        if public_key is None:
            raise BadSignatureError("Public key not found")
        if public_key != wanted_public_key:
            raise BadSignatureError("Public key mismatch")
        return public_key

    @classmethod
    def _try_parse_public_key(cls, state_init: StateInit) -> t.Optional[PublicKey]:
        """Try to extract a public key from `StateInit`.

        :param state_init: Wallet `StateInit`.
        :return: Extracted public key, or `None`.
        """
        code, data = state_init.code, state_init.data
        if code is None or data is None:
            return None

        data_model = _WALLET_DATA_MODELS.get(code)
        if data_model is not None:
            wallet_data = data_model.deserialize(data.begin_parse())
            return wallet_data.public_key

        return None


class VerifySignData(_BaseVerify[SignDataPayloadDto]):
    """Verifier for TON Connect `signData` payload DTOs."""

    TON_CONNECT_PREFIX = b"ton-connect/sign-data/"

    @property
    def address(self) -> Address:
        """Wallet address."""
        return self.dto.address

    @property
    def domain(self) -> str:
        """dApp domain."""
        return self.dto.domain

    @property
    def public_key(self) -> PublicKey:
        """Wallet public key."""
        return self.dto.public_key

    @property
    def signature(self) -> bytes:
        """Ed25519 signature bytes."""
        return self.dto.signature.as_bytes

    @property
    def signing_message(self) -> bytes:
        """Build the canonical signing message for `signData`.

        :raises BadSignatureError: If payload type is unsupported.
        """
        if isinstance(self.dto.payload, SignDataPayloadCell):
            schema = self.dto.payload.tlb_schema.encode()
            schema_hash = zlib.crc32(schema) & 0xFFFFFFFF
            domain = encode_dns_name(self.domain)
            domain_cell = begin_cell().store_snake_bytes(domain).end_cell()
            return self._build_cell_message(schema_hash, domain_cell)

        if isinstance(self.dto.payload, SignDataPayloadText):
            prefix = b"txt"
            content = self.dto.payload.text.encode()
            return self._build_text_binary_message(prefix, content)

        if isinstance(self.dto.payload, SignDataPayloadBinary):
            prefix = b"bin"
            content = self.dto.payload.raw_bytes
            return self._build_text_binary_message(prefix, content)

        raise BadSignatureError("Unsupported payload type")

    @property
    def timestamp(self) -> int:
        """Signature unix timestamp."""
        return self.dto.timestamp

    @property
    def wallet_state_init(self) -> StateInit:
        """Wallet `StateInit`."""
        return self.dto.wallet_state_init

    def _build_cell_message(self, schema_hash: int, domain_cell: Cell) -> bytes:
        """Build signing message for cell payload.

        :param schema_hash: CRC32 of TL-B schema string.
        :param domain_cell: `Cell` with snake-encoded DNS name.
        :return: 32-byte cell hash.
        """
        cell = begin_cell()
        cell.store_uint(0x75569022, 32)
        cell.store_uint(schema_hash, 32)
        cell.store_uint(self.timestamp, 64)
        cell.store_address(self.address)
        cell.store_ref(domain_cell)
        cell.store_ref(self.dto.payload.cell)
        return cell.end_cell().hash

    def _build_text_binary_message(self, prefix: bytes, content: bytes) -> bytes:
        """Build signing message for text or binary payload.

        :param prefix: Type tag (b"txt" or b"bin").
        :param content: Content bytes.
        :return: 32-byte SHA-256 digest.
        """
        msg = bytearray()
        msg.extend(b"\xff\xff")
        msg.extend(self.TON_CONNECT_PREFIX)
        msg.extend(_i32_be(self.address.wc))
        msg.extend(self.address.hash_part)

        domain_bytes = self.domain.encode()
        msg.extend(_u32_be(len(domain_bytes)))
        msg.extend(domain_bytes)

        msg.extend(_u64_be(self.timestamp))
        msg.extend(prefix)
        msg.extend(_u32_be(len(content)))
        msg.extend(content)
        return hashlib.sha256(bytes(msg)).digest()


class VerifyTonProof(_BaseVerify[TonProofPayloadDto]):
    """Verifier for TON Connect `ton_proof` payload DTOs."""

    TON_CONNECT_PREFIX = b"ton-connect"

    @property
    def address(self) -> Address:
        """Wallet address."""
        return self.dto.address

    @property
    def domain(self) -> str:
        """dApp domain."""
        return self.dto.proof.domain.value

    @property
    def public_key(self) -> PublicKey:
        """Wallet public key."""
        return self.dto.public_key

    @property
    def signature(self) -> bytes:
        """Ed25519 signature bytes."""
        return self.dto.proof.signature.as_bytes

    @property
    def signing_message(self) -> bytes:
        """Compute canonical signing hash for TON Proof."""
        msg = self._build_proof_message()
        full = bytearray()
        full.extend(b"\xff\xff")
        full.extend(self.TON_CONNECT_PREFIX)
        full.extend(hashlib.sha256(msg).digest())
        return hashlib.sha256(bytes(full)).digest()

    @property
    def timestamp(self) -> int:
        """Proof unix timestamp."""
        return self.dto.proof.timestamp

    @property
    def wallet_state_init(self) -> StateInit:
        """Wallet `StateInit`."""
        return self.dto.wallet_state_init

    def _build_proof_message(self) -> bytes:
        """Build raw `ton-proof-item-v2/` message bytes.

        :return: Raw message bytes (not hashed).
        """
        msg = bytearray()
        msg.extend(b"ton-proof-item-v2/")
        msg.extend(_i32_be(self.address.wc))
        msg.extend(self.address.hash_part)
        msg.extend(_u32_le(self.dto.proof.domain.length_bytes))
        msg.extend(self.domain.encode())
        msg.extend(_u64_le(self.timestamp))
        msg.extend(self.dto.proof.payload.encode())
        return bytes(msg)


def create_ton_proof_payload(secret_key: str, ttl: int = 15 * 60) -> str:
    """Create backend-generated challenge payload for TON Proof.

    :param secret_key: Backend secret key for HMAC.
    :param ttl: Validity period in seconds.
    :return: Hex-encoded payload.
    """
    exp = int(time.time()) + int(ttl)
    payload = secrets.token_bytes(32) + exp.to_bytes(8, "big")
    sig = hmac.new(secret_key.encode(), payload, hashlib.sha256).digest()
    return (payload + sig).hex()


def verify_ton_proof_payload(secret_key: str, ton_proof_payload: str) -> bool:
    """Verify backend-generated TON Proof challenge payload.

    :param secret_key: Backend secret key used in `create_ton_proof_payload`.
    :param ton_proof_payload: Hex payload from wallet proof response.
    :return: `True` if payload is valid.
    :raises BadSignatureError: If payload is malformed, signature invalid, or expired.
    """
    try:
        raw = bytes.fromhex(ton_proof_payload)
    except Exception as e:
        raise BadSignatureError("Invalid payload encoding") from e

    if len(raw) != 72:
        raise BadSignatureError("Invalid payload length")

    payload, sig = raw[:40], raw[40:]
    expected = hmac.new(secret_key.encode(), payload, hashlib.sha256).digest()
    if not hmac.compare_digest(sig, expected):
        raise BadSignatureError("Payload signature mismatch")

    exp = int.from_bytes(payload[32:40], "big")
    if int(time.time()) > exp + 60:
        raise BadSignatureError("Payload expired")
    return True
