import hashlib
import time
from secrets import token_bytes
from typing import Tuple


def generate_proof_payload(ttl: int = 15 * 60) -> Tuple[str, str]:
    """
    Generates a hex-encoded payload for TON Proof and its SHA256 hash.

    :param ttl: Time-to-live in seconds (default: 15 minutes).
    :return: Tuple (payload_token, payload_token_hash)
    """
    random_bytes = token_bytes(8)
    expire_time = int(time.time()) + ttl
    expire_bytes = expire_time.to_bytes(8, "big")

    payload = random_bytes + expire_bytes

    payload_token = payload.hex()
    payload_token_hash = hashlib.sha256(payload_token.encode()).hexdigest()

    return payload_token, payload_token_hash
