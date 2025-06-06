import time
from secrets import token_bytes
from typing import Optional


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
