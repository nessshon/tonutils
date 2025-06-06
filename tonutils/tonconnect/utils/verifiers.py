import base64
import hashlib
import zlib
from typing import Union

from nacl.signing import VerifyKey
from pytoniq_core import Address, begin_cell

from ..models import TonProof, SignDataResult, SignDataPayloadCell, SignDataPayloadText, SignDataPayloadBinary


def encode_dns_name(name: str) -> bytes:
    """
    Converts a human-readable domain name (e.g. "ton-connect.github.io")
    into the TON DNS internal byte representation as specified in TEP-81.

    The encoding rules are:
        - The domain name must be UTF-8 encoded and ≤ 126 bytes.
        - Characters with byte values in the range 0x00–0x20 are forbidden.
        - The domain is split by ".", labels are reversed, and each label is
          followed by a 0x00 byte (null terminator).
        - The resulting byte sequence must be ≤ 127 bytes.

    :param name: A human-readable domain name (e.g. "example.ton").
    :return: Encoded domain name as bytes, suitable for use in TON DNS records.
    """
    if not isinstance(name, str):
        raise TypeError("Domain must be a string.")

    encoded = name.encode("utf-8")

    if len(encoded) > 126:
        raise ValueError("Domain exceeds 126 bytes in UTF-8 encoding.")
    if any(b <= 0x20 for b in encoded):
        raise ValueError("Domain contains forbidden characters (bytes 0x00–0x20).")

    labels = name.split(".")
    result = bytearray()

    for label in reversed(labels):
        label_bytes = label.encode("utf-8")
        if not label_bytes:
            raise ValueError("Empty domain label detected.")
        if any(b <= 0x20 for b in label_bytes):
            raise ValueError("Label contains forbidden characters (bytes 0x00–0x20).")
        result.extend(label_bytes)
        result.append(0x00)

    if len(result) > 127:
        raise ValueError("Resulting byte array does not fit into a Cell (must be ≤127 bytes).")

    return bytes(result)


def create_cell_sign_message(
        payload: SignDataPayloadCell,
        address: Address,
        domain: str,
        timestamp: int,
) -> bytes:
    """
    Creates a SHA256 hash of a structured TON cell sign message.

    Used for signing structured payloads stored in a Cell. Includes schema hash,
    timestamp, address, domain, and payload.

    :param payload: Payload containing the schema and the cell to be signed.
    :param address: TON wallet address of the signer.
    :param domain: Domain name that requested the signature.
    :param timestamp: Timestamp when the message was created.
    :return: SHA256 hash of the assembled message cell.
    """
    schema_bytes = payload.schema.encode()
    schema_hash = zlib.crc32(schema_bytes) & 0xFFFFFFFF
    domain_cell = begin_cell().store_snake_bytes(encode_dns_name(domain)).end_cell()

    cell = (
        begin_cell()
        .store_uint(0x75569022, 32)
        .store_uint(schema_hash, 32)
        .store_uint(timestamp, 64)
        .store_address(address)
        .store_ref(domain_cell)
        .store_ref(payload.cell)
        .end_cell()
    )
    return cell.hash


def create_text_binary_sign_message(
        payload: Union[SignDataPayloadText, SignDataPayloadBinary,],
        address: Address,
        domain: str,
        timestamp: int,
) -> bytes:
    """
    Creates a SHA256 hash of a text or binary payload for signing.

    The message includes a prefix ("txt" or "bin"), domain, timestamp, address, and content.
    Used for simpler cases of signing text or base64-encoded binary data.

    :param payload: Payload containing either text or binary data.
    :param address: TON wallet address of the signer.
    :param domain: Domain name that requested the signature.
    :param timestamp: Timestamp when the message was created.
    :return: SHA256 hash of the assembled sign message.
    """
    if isinstance(payload, SignDataPayloadText):
        prefix = b"txt"
        content_bytes = payload.text.encode()
    elif isinstance(payload, SignDataPayloadBinary):
        prefix = b"bin"
        content_bytes = payload.bytes
    else:
        raise TypeError("Invalid payload type for text/binary sign message")

    domain_bytes = domain.encode()
    timestamp_bytes = timestamp.to_bytes(8, "big")
    domain_len = len(domain_bytes).to_bytes(4, "big")
    payload_len = len(content_bytes).to_bytes(4, "big")

    message = bytearray()
    message.extend(b"\xff\xff")
    message.extend(b"ton-connect/sign-data/")
    message.extend(address.wc.to_bytes(4, "little"))
    message.extend(address.hash_part)
    message.extend(domain_len)
    message.extend(domain_bytes)
    message.extend(timestamp_bytes)
    message.extend(prefix)
    message.extend(payload_len)
    message.extend(content_bytes)
    return hashlib.sha256(message).digest()


def create_proof_sign_message(
        payload: str,
        address: Address,
        domain_len: int,
        domain_val: str,
        timestamp: int,
) -> bytes:
    """
    Creates a SHA256 hash of a proof message used in TON Connect authentication.

    This includes a domain and a payload message, and is used to verify identity
    and origin through signature validation.

    :param payload: Arbitrary string payload to be signed (usually a session identifier).
    :param address: TON wallet address of the signer.
    :param domain_len: Length of the domain name in bytes.
    :param domain_val: Domain name string.
    :param timestamp: Timestamp when the proof was generated.
    :return: SHA256 hash of the proof message.
    """
    domain_val_bytes = domain_val.encode()
    domain_len_bytes = domain_len.to_bytes(4, "little")
    timestamp_bytes = timestamp.to_bytes(8, "little")

    proof = bytearray()
    proof.extend(b"ton-proof-item-v2/")
    proof.extend(address.wc.to_bytes(4, "little"))
    proof.extend(address.hash_part)
    proof.extend(domain_len_bytes)
    proof.extend(domain_val_bytes)
    proof.extend(timestamp_bytes)
    proof.extend(payload.encode())
    proof_digest = hashlib.sha256(proof).digest()

    message = bytearray()
    message.extend(b"\xff\xff")
    message.extend(b"ton-connect")
    message.extend(proof_digest)
    return hashlib.sha256(message).digest()


def verify_sign_data(
        public_key: Union[str, bytes],
        params: SignDataResult,
) -> bool:
    """
    Verifies the signature of a signed payload (cell, text, or binary).

    Depending on the payload type, constructs the appropriate message and verifies
    the signature using the provided public key.

    :param public_key: Public key used to verify the signature.
    :param params: The signed result including payload, signature, domain, and timestamp.
    :return: True if signature is valid, False otherwise.
    """
    if isinstance(public_key, str):
        public_key = bytes.fromhex(public_key)
    if isinstance(params.signature, str):
        signature = base64.b64decode(params.signature)
    else:
        signature = params.signature

    address = Address(params.address)

    if isinstance(params.payload, SignDataPayloadCell):
        sign_message = create_cell_sign_message(
            params.payload, address, params.domain, params.timestamp
        )
    elif isinstance(params.payload, (SignDataPayloadText, SignDataPayloadBinary)):
        sign_message = create_text_binary_sign_message(
            params.payload, address, params.domain, params.timestamp
        )
    else:
        raise TypeError("Unsupported payload type")

    try:
        VerifyKey(public_key).verify(sign_message, signature)
        return True
    except (Exception,):
        return False


def verify_ton_proof(
        public_key: Union[str, bytes],
        ton_proof: TonProof,
        address: Address,
        payload: str,
) -> bool:
    """
    Verifies the TON proof signature, typically used for authentication purposes.

    Uses domain, timestamp, payload, and wallet address to reconstruct the original
    message and verify it with the given public key.

    :param public_key: Public key used to verify the signature.
    :param ton_proof: The TON proof object containing domain info and signature.
    :param address: TON wallet address of the signer.
    :param payload: Arbitrary string originally signed (usually a session string).
    :return: True if the signature is valid, False otherwise.
    """
    if isinstance(public_key, str):
        public_key = bytes.fromhex(public_key)
    if isinstance(ton_proof.signature, str):
        signature = base64.b64decode(ton_proof.signature)
    else:
        signature = ton_proof.signature

    sign_message = create_proof_sign_message(
        payload,
        address,
        ton_proof.domain_len,
        ton_proof.domain_val,
        ton_proof.timestamp
    )

    try:
        VerifyKey(public_key).verify(sign_message, signature)
        return True
    except (Exception,):
        return False
