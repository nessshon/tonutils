from __future__ import annotations

import hashlib
import socket
import struct
import typing as t

from nacl.signing import SigningKey, VerifyKey
from ton_core import AdnlAddressListConfig, PublicKey, TlGenerator, get_random

if t.TYPE_CHECKING:
    from ton_core.tl.generator import TlSchema

from tonutils.clients.dht.models import (
    DhtKey,
    DhtKeyDescription,
    DhtNode,
    DhtUpdateRule,
    DhtValue,
    compute_key_id,
)

__all__ = ["DhtCodec"]


class DhtCodec:
    """Encodes/decodes DHT protocol messages and verifies signatures.

    Owns the ``TlGenerator`` schema registry.  Every TL operation
    in the DHT stack goes through this class so that no other layer
    needs to import or know about TL.
    """

    def __init__(self) -> None:
        self.tl = TlGenerator.with_default_schemas().generate()

        def _s(name: str) -> TlSchema:
            schema = self.tl.get_by_name(name)
            if schema is None:
                msg = f"TL schema '{name}' not found"
                raise RuntimeError(msg)
            return schema

        self._s_find_node: TlSchema = _s("dht.findNode")
        self._s_find_value: TlSchema = _s("dht.findValue")
        self._s_store: TlSchema = _s("dht.store")
        self._s_ping: TlSchema = _s("dht.ping")
        self._s_get_sal: TlSchema = _s("dht.getSignedAddressList")
        self._s_node: TlSchema = _s("dht.node")
        self._s_key: TlSchema = _s("dht.key")
        self._s_key_desc: TlSchema = _s("dht.keyDescription")
        self._s_value: TlSchema = _s("dht.value")
        self._s_addr_list: TlSchema = _s("adnl.addressList")
        self._s_overlay_nodes: TlSchema = _s("overlay.nodes")
        self._s_pub_overlay: TlSchema = _s("pub.overlay")
        self._s_overlay_to_sign: TlSchema = _s("overlay.node.toSign")

    def serialize_find_node(self, key: bytes, k: int) -> bytes:
        """Serialize ``dht.findNode`` query."""
        return self.tl.serialize(self._s_find_node, {"key": key.hex(), "k": k})

    def serialize_find_value(self, key: bytes, k: int) -> bytes:
        """Serialize ``dht.findValue`` query."""
        return self.tl.serialize(self._s_find_value, {"key": key.hex(), "k": k})

    def serialize_store(self, value: dict[str, t.Any]) -> bytes:
        """Serialize ``dht.store`` query."""
        return self.tl.serialize(self._s_store, {"value": value})

    def serialize_ping(self) -> bytes:
        """Serialize ``dht.ping`` query with random ID."""
        random_id = int.from_bytes(get_random(8), "big", signed=True)
        return self.tl.serialize(self._s_ping, {"random_id": random_id})

    def serialize_get_signed_address_list(self) -> bytes:
        """Serialize ``dht.getSignedAddressList`` query."""
        return self.tl.serialize(self._s_get_sal, {})

    def deserialize(self, data: bytes) -> t.Any:
        """Deserialize boxed TL data."""
        return self.tl.deserialize(data, boxed=True)

    def parse_node(self, node_tl: dict[str, t.Any]) -> DhtNode | None:
        """Parse and verify ``dht.node`` TL dict into a ``DhtNode`` model.

        Signature verification is mandatory.
        Returns ``None`` on any validation failure.
        """
        try:
            node_id_data = node_tl.get("id", {})
            key = node_id_data.get("key", b"")
            if isinstance(key, str):
                pub_key = PublicKey(key).as_bytes
            elif isinstance(key, bytes):
                pub_key = key
            else:
                return None

            if not pub_key or len(pub_key) != 32:
                return None

            signature = _tl_bytes(node_tl.get("signature", b""))
            if not signature:
                return None

            node_copy = dict(node_tl)
            node_copy["signature"] = b""
            schema = self._s_node
            signed_msg = self.tl.serialize(schema, node_copy)
            VerifyKey(pub_key).verify(signed_msg, signature)

            addr_list = node_tl.get("addr_list", {})
            addrs = addr_list.get("addrs", [])
            if not addrs:
                return None
            if len(addrs) > 5:
                addrs = addrs[:5]

            first_addr = addrs[0]
            ip_int = first_addr.get("ip", 0)
            port = first_addr.get("port", 0)

            try:
                packed = struct.pack(">i", int(ip_int))
                host = socket.inet_ntoa(packed)
            except Exception:
                host = str(ip_int)

            adnl_id = compute_key_id(pub_key)
            return DhtNode(adnl_id=adnl_id, addr=f"{host}:{port}", server_key=pub_key)

        except Exception:
            return None

    def parse_value(self, data: dict[str, t.Any]) -> DhtValue | None:
        """Parse ``dht.value`` TL dict into a ``DhtValue`` model."""
        try:
            key_desc_data = data.get("key", data.get("key_description"))
            if key_desc_data is None:
                return None
            kd = self._parse_key_description(key_desc_data)

            value = data.get("value", b"")
            raw_value = b""
            if isinstance(value, str):
                value = bytes.fromhex(value)
            if isinstance(value, bytes):
                raw_value = value

            return DhtValue(
                key_description=kd,
                value=value,
                ttl=data.get("ttl", 0),
                signature=_tl_bytes(data.get("signature", b"")),
                raw_value=raw_value,
            )
        except Exception:
            return None

    @staticmethod
    def parse_nodes_from_response(resp: dict[str, t.Any]) -> list[dict[str, t.Any]]:
        """Extract raw ``dht.node`` dicts from a response.

        Handles both ``dht.valueNotFound`` and ``dht.findNode`` responses.
        """
        nodes_data = resp.get("nodes", [])
        if isinstance(nodes_data, dict):
            nodes_data = nodes_data.get("nodes", [])
        if isinstance(nodes_data, list):
            return nodes_data
        return []

    def verify_value(self, dht_value: DhtValue, requested_key: bytes) -> bool:
        """Verify DHT value integrity (Go ``checkValue`` parity).

        4-layer validation:
        1. Key name length (1..127), index (0..15).
        2. ``SHA256(TL(key)) == requested_key``.
        3. ``SHA256(TL(pub_key)) == key.id`` (descriptor consistency).
        4. Signature verification per update rule.
        """
        try:
            kd = dht_value.key_description
            k = kd.key

            if not (1 <= len(k.name) <= 127):
                return False
            if not (0 <= k.idx <= 15):
                return False

            tl_key_schema = self._s_key
            tl_key = self.tl.serialize(
                tl_key_schema,
                {"id": k.id.hex(), "name": k.name, "idx": k.idx},
            )
            if hashlib.sha256(tl_key).digest() != requested_key:
                return False

            if kd.update_rule == DhtUpdateRule.OVERLAY_NODES:
                # Skip id_public_key == key.id check: KeyDescription.ID is
                # pub.overlay, but compute_key_id uses pub.ed25519 TL prefix.
                # Go's tl.Hash is polymorphic; Python's is not.
                self._verify_overlay_nodes(dht_value)
            else:
                if not kd.id_public_key:
                    return False
                owner_id = compute_key_id(kd.id_public_key)
                if k.id != owner_id:
                    return False
                if kd.update_rule == DhtUpdateRule.SIGNATURE:
                    self._verify_signatures(dht_value)

            return True
        except Exception:
            return False

    def build_store_address(
        self,
        address_list: dict[str, t.Any],
        ttl: int,
        owner_key: bytes,
    ) -> tuple[dict[str, t.Any], bytes]:
        """Build a signed ``dht.value`` for storing an ADNL address.

        :return: ``(value_tl_dict, target_key_id)``.
        """
        signing_key = SigningKey(owner_key)
        pub_key = bytes(signing_key.verify_key)

        owner_id = compute_key_id(pub_key)
        dht_key = DhtKey(id=owner_id, name=b"address", idx=0)

        id_tl: dict[str, t.Any] = {"@type": "pub.ed25519", "key": pub_key.hex()}
        key_tl: dict[str, t.Any] = {
            "id": dht_key.id.hex(),
            "name": dht_key.name,
            "idx": dht_key.idx,
        }
        rule_tl: dict[str, t.Any] = {"@type": DhtUpdateRule.SIGNATURE.value}

        desc_tl: dict[str, t.Any] = {
            "key": key_tl,
            "id": id_tl,
            "update_rule": rule_tl,
            "signature": b"",
        }
        desc_schema = self._s_key_desc
        desc_data = self.tl.serialize(desc_schema, desc_tl)
        desc_tl["signature"] = signing_key.sign(desc_data).signature

        addr_schema = self._s_addr_list
        value_data = self.tl.serialize(addr_schema, address_list)

        value_tl: dict[str, t.Any] = {
            "key": desc_tl,
            "value": value_data,
            "ttl": ttl,
            "signature": b"",
        }
        value_schema = self._s_value
        value_bytes = self.tl.serialize(value_schema, value_tl)
        value_tl["signature"] = signing_key.sign(value_bytes).signature

        return value_tl, dht_key.key_id

    def build_store_overlay(
        self,
        overlay_key: bytes,
        nodes_list: dict[str, t.Any],
        ttl: int,
    ) -> tuple[dict[str, t.Any], bytes]:
        """Build a ``dht.value`` for storing overlay nodes.

        :return: ``(value_tl_dict, target_key_id)``.
        """
        key_hash = self.compute_overlay_key_hash(overlay_key)
        dht_key = DhtKey(id=key_hash, name=b"nodes", idx=0)

        id_tl: dict[str, t.Any] = {"@type": "pub.overlay", "name": overlay_key.hex()}
        key_tl: dict[str, t.Any] = {
            "id": dht_key.id.hex(),
            "name": dht_key.name,
            "idx": dht_key.idx,
        }
        rule_tl: dict[str, t.Any] = {"@type": DhtUpdateRule.OVERLAY_NODES.value}

        desc_tl: dict[str, t.Any] = {
            "key": key_tl,
            "id": id_tl,
            "update_rule": rule_tl,
            "signature": b"",
        }

        nodes_schema = self._s_overlay_nodes
        value_data = self.tl.serialize(nodes_schema, nodes_list)

        value_tl: dict[str, t.Any] = {
            "key": desc_tl,
            "value": value_data,
            "ttl": ttl,
            "signature": b"",
        }
        return value_tl, dht_key.key_id

    def compute_overlay_key_hash(self, overlay_key: bytes) -> bytes:
        """Compute ``SHA-256(TL(pub.overlay))`` for DHT overlay lookup."""
        schema = self._s_pub_overlay
        overlay_tl = self.tl.serialize(schema, {"name": overlay_key.hex()})
        return hashlib.sha256(overlay_tl).digest()

    def parse_address_list(
        self,
        value: bytes | dict[str, t.Any],
    ) -> AdnlAddressListConfig:
        """Parse ``adnl.addressList`` from DHT value data field."""
        if isinstance(value, bytes):
            parsed = self.tl.deserialize(value, boxed=True)
            if parsed:
                value = parsed[0]
        if isinstance(value, dict):
            return AdnlAddressListConfig.from_dict(value)
        raise ValueError("invalid address list data")

    def _get_value_bytes(self, dht_value: DhtValue) -> bytes:
        """Get raw bytes of value for signature verification.

        If the TL deserializer auto-parsed value into a dict,
        re-serializes it back using the ``@type`` field.
        """
        if dht_value.raw_value:
            return dht_value.raw_value
        if isinstance(dht_value.value, bytes):
            return dht_value.value
        if isinstance(dht_value.value, dict):
            at_type = dht_value.value.get("@type", "")
            if at_type:
                schema = self.tl.get_by_name(at_type)
                if schema:
                    return self.tl.serialize(schema, dht_value.value, boxed=True)
        return b""

    def _verify_signatures(self, dht_value: DhtValue) -> None:
        """Verify Ed25519 signatures on value and key description.

        Go parity: ``valueCopy.Signature = nil`` then verify value,
        then ``valueCopy.KeyDescription.Signature = nil`` then verify key desc.
        """
        kd = dht_value.key_description
        pub_key = kd.id_public_key
        if not pub_key:
            raise ValueError("no public key for signature verification")

        vk = VerifyKey(pub_key)
        id_tl: dict[str, t.Any] = {"@type": "pub.ed25519", "key": pub_key.hex()}
        key_tl: dict[str, t.Any] = {
            "id": kd.key.id.hex(),
            "name": kd.key.name,
            "idx": kd.key.idx,
        }
        rule_tl: dict[str, t.Any] = {"@type": kd.update_rule.value}

        value_bytes = self._get_value_bytes(dht_value)

        if dht_value.signature:
            value_tl: dict[str, t.Any] = {
                "key": {
                    "key": key_tl,
                    "id": id_tl,
                    "update_rule": rule_tl,
                    "signature": kd.signature,
                },
                "value": value_bytes,
                "ttl": dht_value.ttl,
                "signature": b"",
            }
            signed_data = self.tl.serialize(self._s_value, value_tl)
            vk.verify(signed_data, dht_value.signature)

        if kd.signature:
            desc_tl: dict[str, t.Any] = {
                "key": key_tl,
                "id": id_tl,
                "update_rule": rule_tl,
                "signature": b"",
            }
            signed_data = self.tl.serialize(self._s_key_desc, desc_tl)
            vk.verify(signed_data, kd.signature)

    def _verify_overlay_nodes(self, dht_value: DhtValue) -> None:
        """Verify overlay node signatures.

        TL schema: ``overlay.node.toSign id:adnl.id.short overlay:int256 version:int``
        """
        value = dht_value.value
        if isinstance(value, bytes):
            parsed = self.tl.deserialize(value, boxed=True)
            if parsed:
                value = parsed[0]

        if not isinstance(value, dict):
            raise ValueError("overlay nodes value must be a dict")

        nodes = value.get("nodes", [])
        if not isinstance(nodes, list):
            raise ValueError("overlay nodes list expected")

        schema = self._s_overlay_to_sign
        for node_data in nodes:
            overlay = node_data.get("overlay", b"")
            if isinstance(overlay, str):
                overlay = bytes.fromhex(overlay)

            id_data = node_data.get("id", {})
            pub_key_raw = id_data.get("key", b"")
            if isinstance(pub_key_raw, str):
                pub_key_raw = PublicKey(pub_key_raw).as_bytes
            if not pub_key_raw:
                raise ValueError("overlay node missing public key")

            signature = _tl_bytes(node_data.get("signature", b""))
            if not signature:
                raise ValueError("overlay node missing signature")

            node_id = compute_key_id(pub_key_raw)
            to_sign = self.tl.serialize(
                schema,
                {
                    "id": {"@type": "adnl.id.short", "id": node_id.hex()},
                    "overlay": overlay.hex(),
                    "version": node_data.get("version", 0),
                },
            )
            VerifyKey(pub_key_raw).verify(to_sign, signature)

    @staticmethod
    def _parse_key_description(data: dict[str, t.Any]) -> DhtKeyDescription:
        """Parse ``dht.keyDescription`` from TL dict."""
        key_data = data.get("key", {})
        if isinstance(key_data, dict):
            key_id = _tl_bytes(key_data.get("id", b""))
            key_name = key_data.get("name", b"")
            if isinstance(key_name, str):
                key_name = key_name.encode()
            elif not isinstance(key_name, bytes):
                key_name = b""
            key = DhtKey(id=key_id, name=key_name, idx=key_data.get("idx", 0))
        else:
            key = DhtKey(id=b"", name=b"", idx=0)

        id_data = data.get("id", {})
        pub_key = b""
        if isinstance(id_data, dict):
            raw = id_data.get("key", b"")
            if isinstance(raw, str):
                pub_key = PublicKey(raw).as_bytes
            elif isinstance(raw, bytes):
                pub_key = raw

        update_rule_data = data.get("update_rule", {})
        rule_type = update_rule_data.get("@type", "") if isinstance(update_rule_data, dict) else ""
        try:
            update_rule = DhtUpdateRule(rule_type)
        except ValueError:
            update_rule = DhtUpdateRule.SIGNATURE

        return DhtKeyDescription(
            key=key,
            id_public_key=pub_key,
            update_rule=update_rule,
            signature=_tl_bytes(data.get("signature", b"")),
        )


def _tl_bytes(v: t.Any) -> bytes:
    """Coerce TL field to bytes (handles hex str, bytes, empty)."""
    if isinstance(v, str):
        return bytes.fromhex(v)
    return v if isinstance(v, bytes) else b""
