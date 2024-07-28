import hashlib
import hmac
import os
from typing import Tuple

from Cryptodome.Cipher import AES
# noinspection PyPackageRequirements
from nacl.bindings import crypto_scalarmult
# noinspection PyPackageRequirements
from nacl.signing import SigningKey
from pytoniq_core import Address, Cell, MessageAny, begin_cell


def message_to_boc_hex(message: MessageAny) -> Tuple[str, str]:
    """
    Serialize a message to its Bag of Cells (BoC) representation and return its hexadecimal strings.

    :param message: The message to be serialized.
    :return: A tuple containing the BoC hexadecimal string and the hash hexadecimal string of the message.
    """
    message_cell = message.serialize()
    message_boc = message_cell.to_boc()

    return message_boc.hex(), message_cell.hash.hex()


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
    their_public_key, our_private_key = their_public_key.to_bytes(32, byteorder='big'), our_private_key[:32]

    # Convert keys to Curve25519
    _our_private_key = SigningKey(our_private_key).to_curve25519_private_key().encode()
    _their_public_key = SigningKey(their_public_key).verify_key.to_curve25519_public_key().encode()

    # Compute shared key
    shared_key = crypto_scalarmult(_our_private_key, _their_public_key)

    data = text.encode('utf-8')

    # Calculate prefix size and generate random prefix
    pfx_sz = 16
    if len(data) % 16 != 0:
        pfx_sz += 16 - (len(data) % 16)

    pfx = bytearray(os.urandom(pfx_sz - 1))
    pfx.insert(0, pfx_sz)
    data = bytes(pfx) + data

    # Generate message key using HMAC with sender address
    h = hmac.new(sender_address.to_str().encode('utf-8'), data, hashlib.sha512)
    msg_key = h.digest()[:16]

    # Generate encryption key using HMAC with shared key
    h = hmac.new(shared_key, msg_key, hashlib.sha512)
    x = h.digest()

    # Encrypt data using AES in CBC mode
    c = AES.new(x[:32], AES.MODE_CBC, x[32:48])
    encrypted_data = c.encrypt(data)

    # XOR public keys
    xor_key = bytearray(SigningKey(our_private_key).verify_key.encode())
    for i in range(32):
        xor_key[i] ^= SigningKey(their_public_key).verify_key.encode()[i]

    # Store data
    root.store_bytes(xor_key)
    root.store_bytes(msg_key)
    root.store_snake_bytes(encrypted_data)

    return root.end_cell()
