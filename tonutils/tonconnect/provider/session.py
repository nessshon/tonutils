import base64
from typing import Optional, Any, Dict, Union

from nacl.encoding import HexEncoder
from nacl.public import PublicKey, PrivateKey, Box


class SessionCrypto:
    """
    Handles cryptographic operations for a session, including key pair
    generation, encryption, and decryption of messages using NaCl.
    """

    def __init__(self, private_key: Optional[Union[str, bytes]] = None) -> None:
        """
        Initializes SessionCrypto with a generated or provided private key.

        :param private_key: A hex-encoded private key (string or bytes). If None,
                            a new PrivateKey is generated.
        """
        self.private_key = (
            PrivateKey(private_key, HexEncoder)  # type: ignore
            if private_key else
            PrivateKey.generate()
        )
        # Session ID is derived from the public key in hex form
        self.session_id = self.private_key.public_key.encode().hex()

    def encrypt(self, message: str, receiver_pub_key: Union[str, bytes]) -> str:
        """
        Encrypts a message for a given receiver, identified by their public key.

        :param message: The plain text message to encrypt.
        :param receiver_pub_key: The receiver's public key (hex-encoded) as str or bytes.
        :return: The encrypted message as a base64-encoded string.
        """
        receiver_pub_key_obj = PublicKey(receiver_pub_key, encoder=HexEncoder)  # type: ignore
        box = Box(self.private_key, receiver_pub_key_obj)  # type: ignore

        message_bytes = message.encode()
        encrypted = box.encrypt(message_bytes)
        return base64.b64encode(encrypted).decode()

    def decrypt(self, message: str, sender_pub_key: Union[str, bytes]) -> str:
        """
        Decrypts a message using the sender's public key.

        :param message: The encrypted message as a base64-encoded string.
        :param sender_pub_key: The sender's public key (hex-encoded) as str or bytes.
        :return: The decrypted plain text message.
        """
        encrypted_message = base64.b64decode(message)
        sender_pub_key_obj = PublicKey(sender_pub_key, encoder=HexEncoder)  # type: ignore
        box = Box(self.private_key, sender_pub_key_obj)  # type: ignore

        decrypted = box.decrypt(encrypted_message)
        return decrypted.decode()


class BridgeSession:
    """
    Stores session data for TonConnect, including cryptographic keys
    and bridge URL information. Facilitates loading/storing session
    details from/to a dictionary representation.
    """

    def __init__(self, stored: Optional[Dict[str, Any]] = None) -> None:
        """
        Initializes the BridgeSession with optional stored data.

        :param stored: A dictionary containing previously stored session fields:
                       {
                           "session_private_key": <hex-encoded private key>,
                           "wallet_public_key": <hex-encoded wallet public key>,
                           "bridge_url": <URL string>
                       }
        """
        stored = stored or {}
        self.session_crypto = SessionCrypto(private_key=stored.get("session_private_key"))
        self.wallet_public_key = stored.get("wallet_public_key")
        self.bridge_url = stored.get("bridge_url")

    def get_dict(self) -> Dict[str, Any]:
        """
        Returns a dictionary representation of the session, suitable for storage.

        :return: A dictionary containing the private key, wallet public key,
                 and bridge URL in a serializable format:
                 {
                     "session_private_key": <hex-encoded private key>,
                     "wallet_public_key": <hex-encoded wallet public key>,
                     "bridge_url": <URL string>
                 }
        """
        session_private_key = (
            self.session_crypto.private_key.encode().hex()
            if self.session_crypto.private_key
            else None
        )
        return {
            "session_private_key": session_private_key,
            "wallet_public_key": self.wallet_public_key,
            "bridge_url": self.bridge_url
        }
