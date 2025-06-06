import base64
import hashlib
import hmac
import json
import os
from decimal import Decimal
from typing import Any, Dict, Union

from Cryptodome.Cipher import AES
from nacl.bindings import crypto_scalarmult
from nacl.signing import SigningKey
from pytoniq_core import Address, Cell, MessageAny, begin_cell, HashMap, Slice


def normalize_hash(message: Union[MessageAny, str]) -> bytes:
    """
    Computes the normalized hash of an external message.
    If the message is not external, returns the regular hash.

    :param message: The message object or its BoC string.
    :return: Hash as raw bytes.
    """
    if isinstance(message, str):
        message = MessageAny.deserialize(Slice.one_from_boc(message))

    if not message.is_external:
        return message.serialize().hash

    cell = (
        begin_cell()
        .store_uint(2, 2)
        .store_address(None)
        .store_address(message.info.dest)
        .store_coins(0)
        .store_bool(False)
        .store_bool(True)
        .store_ref(message.body)
        .end_cell()
    )
    return cell.hash


def boc_to_base64_string(boc: Union[str, bytes]) -> str:
    """
    Convert a BoC string or bytes to base64.

    :param boc: The BoC string or bytes to be converted.
    :return: The base64-encoded string.
    """
    if isinstance(boc, str):
        boc = bytes.fromhex(boc)
    if not isinstance(boc, bytes):
        raise TypeError("Expected boc to be bytes, but got something else.")

    return base64.b64encode(boc).decode()


def create_encrypted_comment_cell(
        text: str,
        sender_address: Address,
        our_private_key: bytes,
        their_public_key: int,
) -> Cell:
    """
    Create an encrypted comment cell.

    This function encrypts a text comment using a shared key derived from the provided private and public keys.
    The encrypted comment is then stored in a cell which can be transmitted or stored as required.

    :param text: The text comment to be encrypted.
    :param sender_address: The address of the sender.
    :param our_private_key: The private key of the sender.
    :param their_public_key: The public key of the receiver.
    :return: A cell containing the encrypted comment.
    """
    root = begin_cell().store_uint(0x2167da4b, 32)

    our_private_key_bytes = our_private_key[:32]
    their_public_key_bytes = their_public_key.to_bytes(32, byteorder='big')

    # Convert keys to Curve25519
    _our_private_key = SigningKey(our_private_key_bytes).to_curve25519_private_key().encode()
    _their_public_key = SigningKey(their_public_key_bytes).verify_key.to_curve25519_public_key().encode()

    # Compute shared key
    shared_key = crypto_scalarmult(_our_private_key, _their_public_key)

    data = text.encode("utf-8")

    # Calculate prefix size and generate random prefix
    pfx_sz = 16
    if len(data) % 16 != 0:
        pfx_sz += 16 - (len(data) % 16)

    pfx = bytearray(os.urandom(pfx_sz - 1))
    pfx.insert(0, pfx_sz)
    data = bytes(pfx) + data

    # Generate message key using HMAC with sender address
    h = hmac.new(sender_address.to_str().encode("utf-8"), data, hashlib.sha512)
    msg_key = h.digest()[:16]

    # Generate encryption key using HMAC with shared key
    h = hmac.new(shared_key, msg_key, hashlib.sha512)
    x = h.digest()

    # Encrypt data using AES in CBC mode
    c = AES.new(x[:32], AES.MODE_CBC, x[32:48])
    encrypted_data = c.encrypt(data)

    # XOR public keys
    xor_key = bytearray(SigningKey(our_private_key_bytes).verify_key.encode())
    for i in range(32):
        xor_key[i] ^= SigningKey(their_public_key_bytes).verify_key.encode()[i]

    # Store data
    root.store_bytes(xor_key)
    root.store_bytes(msg_key)
    root.store_snake_bytes(encrypted_data)

    return root.end_cell()


def to_amount(value: int, decimals: int = 9, precision: int = 2) -> Union[float, int]:
    """
    Converts a value from nanoton to TON and rounds it to the specified precision.

    :param value: The value to convert, in nanoton. This should be a positive integer.
    :param decimals: The number of decimal places in the converted value. Defaults to 9.
    :param precision: The number of decimal places to round the converted value to. Defaults to 2.
    :return: The converted value in TON, rounded to the specified precision.
    """
    if not isinstance(value, int) or value < 0:
        raise ValueError("Value must be a positive integer.")

    if not isinstance(precision, int) or precision < 0:
        raise ValueError("Precision must be a non-negative integer.")

    ton_value = value / (10 ** decimals)
    rounded_ton_value = round(ton_value, precision)

    return rounded_ton_value if rounded_ton_value % 1 != 0 else int(rounded_ton_value)


def to_nano(value: Union[int, float, Decimal], decimals: int = 9) -> int:
    """
    Converts TON value to nanoton.

    :param value: TON value to be converted. Can be a float or an integer.
    :param decimals: The number of decimal places in the input value. Defaults to 9.
    :return: The value of the input in nanoton.
    """
    if not isinstance(value, (int, float, Decimal)):
        raise ValueError("Value must be a positive integer or float.")

    return round(value * (10 ** decimals))


def serialize_onchain_dict(data: Dict[str, Any]) -> Cell:
    """
    Serializes a dictionary into a cell.

    :param data: The dictionary to serialize.
    :return: A cell containing the serialized dictionary.
    """
    dict_cell = HashMap(256, value_serializer=lambda src, dest: dest.store_ref(src))

    for key, val in data.items():
        if val is None:
            continue
        cell = begin_cell().store_uint(0x00, 8)
        if isinstance(val, bytes):
            cell.store_snake_bytes(val)
        elif isinstance(val, (int, str)):
            cell.store_snake_string(str(val))
        elif isinstance(val, list):
            cell.store_snake_string(json.dumps(val))
        dict_cell.set(key, cell.end_cell(), hash_key=True)

    return dict_cell.serialize()


def cell_hash(c: Cell) -> int:
    """
    Calculates the representation hash of the given cell c and returns it as a 256-bit unsigned integer x.
    This function is handy for signing and verifying signatures of arbitrary entities structured as a tree of cells.
    """
    return int.from_bytes(c.hash, "big")


def slice_hash(s: Slice) -> int:
    """
    Computes the hash of the given slice s and returns it as a 256-bit unsigned integer x.
    The result is equivalent to creating a standard cell containing only the data and references from s and then computing its hash using cell_hash.
    """
    return int.from_bytes(s.to_cell().hash, "big")


def string_hash(s: str) -> int:
    """
    Calculates the SHA-256 hash of the data bits in the given slice s.
    A cell underflow exception is thrown if the bit length of s is not a multiple of eight.
    The hash is returned as a 256-bit unsigned integer x.
    """
    data = begin_cell().store_snake_string(s).end_cell().get_data_bytes()
    return int.from_bytes(hashlib.sha256(data).digest(), "big")
