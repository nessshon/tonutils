import time
from secrets import token_bytes
from typing import Optional

from .logger import logger
from ..models import WalletInfo


def generate_proof_payload(ttl: Optional[int] = None) -> str:
    """
    Generates a proof payload by combining random bytes and an expiration timestamp.

    :param ttl: Time-to-live in seconds for the proof. If None, uses Connector.DISCONNECT_TIMEOUT.
    :return: The payload as a hex-encoded string.
    """
    # Local import to avoid circular dependency if needed.
    if ttl is None:
        from ..connector import Connector
        ttl = Connector.DISCONNECT_TIMEOUT

    random_bytes = token_bytes(8)
    expire_time = int(time.time()) + ttl

    # Create a bytearray combining random bytes and the expiration time.
    payload = bytearray(random_bytes)
    payload.extend(expire_time.to_bytes(8, "big"))

    return payload.hex()


def verify_proof_payload(proof_hex: str, wallet_info: WalletInfo) -> bool:
    """
    Verifies that a proof payload (provided as hex) is valid and unexpired.

    :param proof_hex: The proof payload as a hex-encoded string.
    :param wallet_info: A WalletInfo instance providing the verify_proof() method.
    :return: True if the proof is valid and not expired, False otherwise.
    """
    # The proof must be at least 16 bytes (32 hex chars) to contain random bytes + expiry.
    if len(proof_hex) < 32:
        return False

    # Check the cryptographic proof via the wallet.
    if not wallet_info.verify_proof(proof_hex):
        return False

    # Extract the expiration time from the latter 8 bytes of the hex string.
    try:
        expire_time = int(proof_hex[16:32], 16)
    except ValueError:
        logger.debug("Invalid proof format: unable to parse timestamp.")
        return False

    # Check whether the current time has exceeded the expiration time.
    if time.time() > expire_time:
        logger.debug("Proof has expired.")
        return False

    return True
