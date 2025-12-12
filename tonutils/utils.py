from __future__ import annotations

import base64
import binascii
import decimal
import hashlib
import hmac
import os
import time
import typing as t

from Cryptodome.Cipher import AES
from nacl.bindings import (
    crypto_scalarmult,
    crypto_sign_ed25519_pk_to_curve25519,
    crypto_sign_ed25519_sk_to_curve25519,
)
from pytoniq_core import (
    Address,
    ConfigParam,
    Cell,
    MessageAny,
    Slice,
    begin_cell,
    Builder,
    HashMap,
)

from tonutils.types import (
    AddressLike,
    PrivateKey,
    PublicKey,
    DNSCategory,
)

if t.TYPE_CHECKING:
    from tonutils.protocols import ClientProtocol


__all__ = [
    "TextCipher",
    "calc_valid_until",
    "cell_hash",
    "cell_to_b64",
    "cell_to_hex",
    "decode_dns_name",
    "encode_dns_name",
    "maybe_stack_addr",
    "norm_stack_cell",
    "norm_stack_num",
    "normalize_hash",
    "parse_stack_config",
    "resolve_wallet_address",
    "slice_hash",
    "string_hash",
    "to_amount",
    "to_cell",
    "to_nano",
]


def to_cell(x: t.Union[str, bytes, Cell, Slice]) -> Cell:
    """Convert various formats to a Cell object."""
    if isinstance(x, Slice):
        x = x.to_cell()
    elif isinstance(x, str):
        x = Cell.one_from_boc(x)
    elif isinstance(x, bytes):
        x = Cell.one_from_boc(x.hex())
    return x


def cell_to_hex(c: t.Union[str, bytes, Cell, Slice]) -> str:
    """Convert a cell to hexadecimal BoC representation."""
    return to_cell(c).to_boc().hex()


def cell_to_b64(c: Cell) -> str:
    """Convert a cell to base64 BoC representation."""
    return base64.b64encode(c.to_boc()).decode()


def cell_hash(c: Cell) -> int:
    """Calculate the hash of a cell as an integer."""
    return int.from_bytes(c.hash, "big")


def slice_hash(s: Slice) -> int:
    """Calculate the hash of a slice as an integer."""
    return cell_hash(s.to_cell())


def string_hash(s: str) -> int:
    """Calculate SHA-256 hash of a string as an integer."""
    return int.from_bytes(hashlib.sha256(s.encode()).digest(), "big")


def normalize_hash(msg: t.Union[MessageAny, str]) -> str:
    """
    Calculate normalized hash of a message.

    :param msg: MessageAny object or BoC string
    """
    if isinstance(msg, str):
        msg = MessageAny.deserialize(Slice.one_from_boc(msg))
    if not msg.is_external:
        return msg.serialize().hash.hex()

    cell = begin_cell()
    cell.store_uint(2, 2)
    cell.store_address(None)
    cell.store_address(msg.info.dest)
    cell.store_coins(0)
    cell.store_bool(False)
    cell.store_bool(True)
    cell.store_ref(msg.body)

    return cell.end_cell().hash.hex()


def to_nano(
    value: t.Union[int, float, str, decimal.Decimal],
    decimals: int = 9,
) -> int:
    """
    Convert token amount to the smallest units (nanotons).

    Converts human-readable token amounts to blockchain-native integer format.
    Default decimals=9 is standard for TON, but jettons may use different values
    (e.g., USDT uses 6).

    :param value: Amount in human-readable format
    :param decimals: Number of decimal places (default: 9 for TON)
    """
    if decimals < 0:
        raise ValueError("Decimals must be >= 0.")
    if isinstance(value, float):
        value = str(value)

    d = decimal.Decimal(value)
    factor = decimal.Decimal(10) ** decimals

    with decimal.localcontext() as ctx:
        ctx.prec = decimals + 30
        nano = (d * factor).quantize(decimal.Decimal(1), rounding=decimal.ROUND_DOWN)
    if nano < 0:
        raise ValueError("Value must be >= 0.")
    return int(nano)


def to_amount(
    value: int,
    decimals: int = 9,
    *,
    precision: t.Optional[int] = None,
) -> decimal.Decimal:
    """
    Convert the smallest units (nanotons) to human-readable amount.

    Converts blockchain-native integer amounts to decimal representation.
    Default decimals=9 is standard for TON, but jettons may use different values.

    :param value: Amount in the smallest units (nanotons)
    :param decimals: Number of decimal places (default: 9 for TON)
    :param precision: Optional decimal places to round to
    """
    if decimals < 0:
        raise ValueError("Decimals must be >= 0.")
    if value < 0:
        raise ValueError("Value must be >= 0.")
    if value == 0:
        return decimal.Decimal(0)

    with decimal.localcontext() as ctx:
        ctx.prec = decimals + 30
        amount = decimal.Decimal(value) / (decimal.Decimal(10) ** decimals)
    if precision is not None:
        quant = decimal.Decimal(1) / (decimal.Decimal(10) ** precision)
        amount = amount.quantize(quant, rounding=decimal.ROUND_DOWN)
    return amount


def maybe_stack_addr(
    v: t.Union[Cell, Slice],
) -> t.Optional[t.Union[Address, Cell, Slice]]:
    """
    Try to parse a TVM stack value as an Address.

    :param v: Cell or Slice from TVM stack
    """
    try:
        s = v.copy().begin_parse() if isinstance(v, Cell) else v.copy()
        tag = s.load_uint(2)
        if tag == 0 and len(s.bits) == 0:
            return None
        if tag == 2 and len(s.bits) == 265:
            s.skip_bits(1)
            wc = s.load_int(8)
            hash_part = s.load_bytes(32)
            return Address((wc, hash_part))
    except (Exception,):
        pass
    return v


def norm_stack_num(n: t.Union[str, int]) -> int:
    """
    Normalize a TVM stack number from string or int.

    :param n: Number as string or int
    """
    if isinstance(n, str):
        try:
            return int(n, 0)
        except ValueError:
            pass
    return int(n)


def norm_stack_cell(
    c: t.Union[Cell, Slice, str],
) -> t.Optional[t.Union[Address, Cell]]:
    """
    Converts various cell formats and tries to parse as an Address.

    :param c: Cell, Slice, or BoC string
    """
    cell = to_cell(c)
    return maybe_stack_addr(cell)


def parse_stack_config(config_slice: Slice) -> dict[int, t.Any]:
    """
    Parse blockchain configuration parameters from a config cell.

    :param config_slice: Slice containing config dictionary
    """

    def key_deserializer(src: t.Any) -> int:
        return Builder().store_bits(src).to_slice().load_int(32)

    def value_deserializer(src: Slice) -> Slice:
        return src.load_ref().begin_parse()

    config_map = HashMap.parse(
        dict_cell=config_slice,
        key_length=32,
        key_deserializer=key_deserializer,
        value_deserializer=value_deserializer,
    )

    params_by_id = ConfigParam.params
    out: t.Dict[int, t.Any] = {}
    for key_id, raw_value_slice in config_map.items():
        param = params_by_id.get(key_id)
        if param is not None:
            out[key_id] = param.deserialize(raw_value_slice)
        else:
            out[key_id] = raw_value_slice
    return out


def encode_dns_name(name: str) -> bytes:
    """
    Encode a DNS domain name for TON DNS.

    :param name: Domain name with dot-separated labels
    """
    labels = name.split(".")
    if any(not lbl for lbl in labels):
        raise ValueError("Empty domain label detected.")

    out = bytearray()
    for lbl in reversed(labels):
        lbl_bytes = lbl.encode()
        if any(b <= 0x20 for b in lbl_bytes):
            raise ValueError("Label contains forbidden bytes 0x00–0x20.")
        out.extend(lbl_bytes)
        out.append(0x00)

    if len(out) > 127:
        raise ValueError("Encoded domain > 127 bytes.")

    return bytes(out)


def decode_dns_name(data: bytes) -> str:
    """
    Decode TON DNS domain name from on-chain format.

    :param data: Encoded DNS name bytes
    """
    if not data:
        return ""

    parts = data.split(b"\x00")
    while parts and parts[-1] == b"":
        parts.pop()
    if not parts:
        return ""

    labels = [p.decode(errors="replace") for p in parts]
    labels.reverse()
    return ".".join(labels)


def calc_valid_until(seqno: int, ttl: int = 60) -> int:
    """Calculate message expiration timestamp for wallet transactions."""
    now = int(time.time())
    return 0xFFFFFFFF if seqno == 0 else now + ttl


async def resolve_wallet_address(
    client: ClientProtocol,
    domain: AddressLike,
) -> Address:
    """
    Resolve a TON address from domain name or address string.

    Supports:
    - Direct Address objects (returned as-is)
    - Address strings in any format (EQ..., UQ..., 0:...)
    - TON DNS domains (.ton, .t.me) - queries wallet record

    :param client: TON client for DNS resolution
    :param domain: Address object, address string, or DNS domain
    """
    from tonutils.contracts.dns.tlb import ALLOWED_DNS_ZONES

    if isinstance(domain, Address):
        return domain

    if isinstance(domain, str):
        try:
            return Address(domain)
        except (Exception,):
            if not domain.endswith(ALLOWED_DNS_ZONES):
                allowed = ", ".join(ALLOWED_DNS_ZONES)
                raise ValueError(
                    f"Invalid DNS domain: {domain}. Supported zones: {allowed}."
                )

            record = await client.dnsresolve(
                domain=domain,
                category=DNSCategory.WALLET,
            )
            if record is None:
                raise ValueError(f"DNS record not found for: {domain}.")

            return record.value

    raise TypeError(f"Invalid domain type: {type(domain)!r}. Expected Address or str.")


class TextCipher:
    """
    End-to-end encryption for TON wallet text comments.

    Implements encrypted text message protocol for TON using:
    - Ed25519 to Curve25519 key conversion for ECDH
    - AES-256-CBC encryption
    - HMAC-SHA512 for key derivation and authentication
    - Address-based salt for additional security

    This allows sending private messages as transaction comments that only
    the recipient can decrypt.
    """

    @staticmethod
    def _xor32(a: bytes, b: bytes) -> bytes:
        """XOR two 32-byte arrays."""
        return bytes(x ^ y for x, y in zip(a, b))

    @staticmethod
    def _derive(shared: bytes, msg_key: bytes) -> tuple[bytes, bytes]:
        """
        Derive AES key and IV from shared secret and message key.

        Uses HMAC-SHA512 to derive 48 bytes: 32 for AES key, 16 for IV.

        :param shared: Shared secret from ECDH
        :param msg_key: 16-byte message key
        """
        derived_bytes = hmac.new(shared, msg_key, hashlib.sha512).digest()
        return derived_bytes[:32], derived_bytes[32:48]

    @staticmethod
    def _msg_key(salt: bytes, data: bytes) -> bytes:
        """
        Calculate message key for authentication.

        :param salt: Address-based salt
        :param data: Plaintext or ciphertext data
        """
        return hmac.new(salt, data, hashlib.sha512).digest()[:16]

    @staticmethod
    def _make_plain(msg: bytes) -> bytes:
        """
        Add PKCS#7-style padding to message.

        Prepends padding length byte and random padding to align to 16-byte blocks.
        Padding size is always between 16 and 31 bytes.

        :param msg: Message bytes to pad
        """
        p = 16 if len(msg) % 16 == 0 else 16 + (16 - (len(msg) % 16))
        return bytes([p]) + os.urandom(p - 1) + msg

    @staticmethod
    def _shared_key_from_ed25519(sk64: bytes, peer_pub32: bytes) -> bytes:
        """
        Perform ECDH key exchange using Ed25519 keys.

        Converts Ed25519 keys to Curve25519 format and computes shared secret.

        :param sk64: Our 64-byte Ed25519 keypair (private + public)
        :param peer_pub32: Their 32-byte Ed25519 public key
        """
        sk_curve = crypto_sign_ed25519_sk_to_curve25519(sk64)
        pk_curve = crypto_sign_ed25519_pk_to_curve25519(peer_pub32)
        return crypto_scalarmult(sk_curve, pk_curve)

    @staticmethod
    def _parse_payload(payload: t.Union[Cell, bytes, str]) -> t.Tuple[bytes, ...]:
        """
        Parse encrypted payload into components.

        Extracts XORed public key, message key, and ciphertext from various formats.

        :param payload: Encrypted data as Cell, bytes, hex string, or base64 string
        """
        from tonutils.contracts.wallet.tlb import EncryptedTextCommentBody

        if isinstance(payload, bytes):
            return payload[:32], payload[32:48], payload[48:]
        elif isinstance(payload, str):
            try:
                payload = bytes.fromhex(payload)
            except ValueError:
                pass
            try:
                payload = base64.b64decode(payload, validate=True)
            except (binascii.Error, ValueError):
                raise ValueError("Invalid payload encoding: not hex or base64.")
            return payload[:32], payload[32:48], payload[48:]

        cell = EncryptedTextCommentBody.deserialize(payload.begin_parse())
        return cell.pub_xor, cell.msg_key, cell.ciphertext

    @staticmethod
    def _salt(address: AddressLike) -> bytes:
        """
        Generate address-based salt for key derivation.

        Uses the bounceable, user-friendly address string as salt.

        :param address: TON address
        """
        if isinstance(address, str):
            address = Address(address)
        salt = address.to_str(
            is_user_friendly=True,
            is_bounceable=True,
            is_test_only=False,
        )
        return salt.encode()

    @classmethod
    def encrypt(
        cls,
        payload: str,
        sender_address: AddressLike,
        our_private_key: PrivateKey,
        their_public_key: PublicKey,
    ) -> Cell:
        """
        Encrypt a text message for a recipient.

        Creates an encrypted comment cell that can be attached to a TON transaction.
        Only the recipient with the corresponding private key can decrypt it.

        :param payload: Plain text message to encrypt
        :param sender_address: Sender's TON address (used for salt)
        :param our_private_key: Sender's private key
        :param their_public_key: Recipient's public key
        """
        from tonutils.contracts.wallet.tlb import EncryptedTextCommentBody

        sk_ed25519_64 = our_private_key.keypair.as_bytes
        their_pubkey_32 = their_public_key.as_bytes
        our_pubkey_32 = our_private_key.public_key.as_bytes

        shared = cls._shared_key_from_ed25519(sk_ed25519_64, their_pubkey_32)
        padded_data = cls._make_plain(payload.encode("utf-8"))

        salt = cls._salt(sender_address)
        msg_key = cls._msg_key(salt, padded_data)

        key, iv = cls._derive(shared, msg_key)
        enc_data = AES.new(key, AES.MODE_CBC, iv).encrypt(padded_data)

        xor_key = cls._xor32(our_pubkey_32, their_pubkey_32)
        cell = EncryptedTextCommentBody(xor_key, msg_key, enc_data)
        return cell.serialize()

    @classmethod
    def decrypt(
        cls,
        payload: t.Union[Cell, str, bytes],
        sender_address: AddressLike,
        our_private_key: PrivateKey,
    ) -> str:
        """
        Decrypt an encrypted text message.

        Decrypts a message that was encrypted with the encrypt() method.
        Verifies message integrity using HMAC authentication.

        :param payload: Encrypted message as Cell, hex string, base64 string, or bytes
        :param sender_address: Sender's TON address (used for salt verification)
        :param our_private_key: Our private key (recipient)
        """
        sk_ed25519_64 = our_private_key.keypair.as_bytes
        our_pubkey_32 = our_private_key.public_key.as_bytes

        pub_xor, msg_key, enc_data = cls._parse_payload(payload)
        their_pubkey_ed25519 = cls._xor32(pub_xor, our_pubkey_32)
        shared = cls._shared_key_from_ed25519(sk_ed25519_64, their_pubkey_ed25519)

        key, iv = cls._derive(shared, msg_key)
        dec_data = AES.new(key, AES.MODE_CBC, iv).decrypt(enc_data)

        salt = cls._salt(sender_address)
        if cls._msg_key(salt, dec_data) != msg_key:
            raise ValueError("Message key mismatch.")

        padding_size = dec_data[0]
        if not (16 <= padding_size <= 31):
            raise ValueError(
                f"Invalid padding length: got {padding_size} byte(s), "
                f"expected between 16 and 31 bytes."
            )
        if 1 + padding_size > len(dec_data):
            raise ValueError(
                f"Padding exceeds data length: "
                f"padding={padding_size}, total={len(dec_data)}."
            )

        comment = dec_data[padding_size:]
        return comment.decode()
