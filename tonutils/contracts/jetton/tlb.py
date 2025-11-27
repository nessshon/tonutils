from __future__ import annotations

import typing as t

from pytoniq_core import Cell, Slice, TlbScheme, begin_cell

from tonutils.contracts.nft.tlb import OnchainContent, OffchainContent
from tonutils.contracts.opcodes import OpCode
from tonutils.types import AddressLike, MetadataPrefix


class JettonMasterStandardData(TlbScheme):

    def __init__(
        self,
        admin_address: AddressLike,
        content: t.Union[OnchainContent, OffchainContent],
        jetton_wallet_code: Cell,
        total_supply: int = 0,
    ) -> None:
        self.total_supply = total_supply
        self.admin_address = admin_address
        self.content = content
        self.jetton_wallet_code = jetton_wallet_code

    def serialize(self) -> Cell:
        cell = begin_cell()
        cell.store_coins(self.total_supply)
        cell.store_address(self.admin_address)
        cell.store_ref(self.content.serialize(True))
        cell.store_ref(self.jetton_wallet_code)
        return cell.end_cell()

    @classmethod
    def deserialize(cls, cs: Slice) -> JettonMasterStandardData:
        total_supply = cs.load_coins()
        admin_address = cs.load_address()
        content = cs.load_ref().begin_parse()
        return cls(
            total_supply=total_supply,
            admin_address=admin_address,
            content=(
                OnchainContent.deserialize(content, False)
                if MetadataPrefix(content.load_uint(8)) == MetadataPrefix.ONCHAIN
                else OffchainContent.deserialize(content, False)
            ),
            jetton_wallet_code=cs.load_ref(),
        )


class JettonMasterStablecoinData(TlbScheme):

    def __init__(
        self,
        admin_address: AddressLike,
        jetton_wallet_code: Cell,
        content: OffchainContent,
        next_admin_address: t.Optional[AddressLike] = None,
        total_supply: int = 0,
    ) -> None:
        self.total_supply = total_supply
        self.admin_address = admin_address
        self.next_admin_address = next_admin_address
        self.jetton_wallet_code = jetton_wallet_code
        self.content = content

    def serialize(self) -> Cell:
        cell = begin_cell()
        cell.store_coins(self.total_supply)
        cell.store_address(self.admin_address)
        cell.store_address(self.next_admin_address)
        cell.store_ref(self.jetton_wallet_code)
        cell.store_ref(self.content.serialize(False))
        return cell.end_cell()

    @classmethod
    def deserialize(cls, cs: Slice) -> JettonMasterStablecoinData:
        return cls(
            total_supply=cs.load_coins(),
            admin_address=cs.load_address(),
            next_admin_address=cs.load_address(),
            jetton_wallet_code=cs.load_ref(),
            content=OffchainContent.deserialize(cs.load_ref().begin_parse(), False),
        )


class JettonWalletStandardData(TlbScheme):

    def __init__(
        self,
        owner_address: AddressLike,
        jetton_master_address: AddressLike,
        jetton_wallet_code: Cell,
        balance: int = 0,
    ) -> None:
        self.balance = balance
        self.owner_address = owner_address
        self.jetton_master_address = jetton_master_address
        self.jetton_wallet_code = jetton_wallet_code

    def serialize(self) -> Cell:
        cell = begin_cell()
        cell.store_coins(self.balance)
        cell.store_address(self.owner_address)
        cell.store_address(self.jetton_master_address)
        cell.store_ref(self.jetton_wallet_code)
        return cell.end_cell()

    @classmethod
    def deserialize(cls, cs: Slice) -> JettonWalletStandardData:
        return cls(
            balance=cs.load_coins(),
            owner_address=cs.load_address(),
            jetton_master_address=cs.load_address(),
            jetton_wallet_code=cs.load_ref(),
        )


class JettonWalletStablecoinData(TlbScheme):

    def __init__(
        self,
        owner_address: AddressLike,
        jetton_master_address: AddressLike,
        status: int,
        balance: int = 0,
    ) -> None:
        self.status = status
        self.balance = balance
        self.owner_address = owner_address
        self.jetton_master_address = jetton_master_address

    def serialize(self) -> Cell:
        cell = begin_cell()
        cell.store_uint(self.status, 4)
        cell.store_coins(self.balance)
        cell.store_address(self.owner_address)
        cell.store_address(self.jetton_master_address)
        return cell.end_cell()

    @classmethod
    def deserialize(cls, cs: Slice) -> JettonWalletStablecoinData:
        return cls(
            status=cs.load_uint(4),
            balance=cs.load_coins(),
            owner_address=cs.load_address(),
            jetton_master_address=cs.load_address(),
        )


class JettonWalletStablecoinV2Data(TlbScheme):

    def __init__(
        self,
        owner_address: AddressLike,
        jetton_master_address: AddressLike,
        balance: int = 0,
    ) -> None:
        self.balance = balance
        self.owner_address = owner_address
        self.jetton_master_address = jetton_master_address

    def serialize(self) -> Cell:
        cell = begin_cell()
        cell.store_coins(self.balance)
        cell.store_address(self.owner_address)
        cell.store_address(self.jetton_master_address)
        return cell.end_cell()

    @classmethod
    def deserialize(cls, cs: Slice) -> JettonWalletStablecoinV2Data:
        return cls(
            balance=cs.load_coins(),
            owner_address=cs.load_address(),
            jetton_master_address=cs.load_address(),
        )


class JettonTopUpBody(TlbScheme):

    def __init__(self, query_id: int = 0) -> None:
        self.query_id = query_id

    def serialize(self) -> Cell:
        cell = begin_cell()
        cell.store_uint(OpCode.TOP_UP, 32)
        cell.store_uint(self.query_id, 64)
        return cell.end_cell()

    @classmethod
    def deserialize(cls, cs: Slice) -> JettonTopUpBody:
        raise NotImplementedError()


class JettonInternalTransferBody(TlbScheme):

    def __init__(
        self,
        jetton_amount: int,
        forward_amount: int,
        from_address: t.Optional[AddressLike] = None,
        response_address: t.Optional[AddressLike] = None,
        forward_payload: t.Optional[Cell] = None,
        query_id: int = 0,
    ) -> None:
        self.query_id = query_id
        self.jetton_amount = jetton_amount
        self.from_address = from_address
        self.response_address = response_address
        self.forward_amount = forward_amount
        self.forward_payload = forward_payload

    def serialize(self) -> Cell:
        cell = begin_cell()
        cell.store_uint(OpCode.JETTON_INTERNAL_TRANSFER, 32)
        cell.store_uint(self.query_id, 64)
        cell.store_coins(self.jetton_amount)
        cell.store_address(self.from_address)
        cell.store_address(self.response_address)
        cell.store_coins(self.forward_amount)
        cell.store_maybe_ref(self.forward_payload)
        return cell.end_cell()

    @classmethod
    def deserialize(cls, cs: Slice) -> JettonInternalTransferBody:
        raise NotImplementedError()


class JettonTransferBody(TlbScheme):

    def __init__(
        self,
        destination: AddressLike,
        jetton_amount: int,
        response_address: t.Optional[AddressLike] = None,
        custom_payload: t.Optional[Cell] = None,
        forward_payload: t.Optional[Cell] = None,
        forward_amount: int = 1,
        query_id: int = 0,
    ) -> None:
        self.query_id = query_id
        self.jetton_amount = jetton_amount
        self.destination = destination
        self.response_address = response_address
        self.custom_payload = custom_payload
        self.forward_amount = forward_amount
        self.forward_payload = forward_payload

    def serialize(self) -> Cell:
        cell = begin_cell()
        cell.store_uint(OpCode.JETTON_TRANSFER, 32)
        cell.store_uint(self.query_id, 64)
        cell.store_coins(self.jetton_amount)
        cell.store_address(self.destination)
        cell.store_address(self.response_address)
        cell.store_maybe_ref(self.custom_payload)
        cell.store_coins(self.forward_amount)
        cell.store_maybe_ref(self.forward_payload)
        return cell.end_cell()

    @classmethod
    def deserialize(cls, cs: Slice) -> JettonTransferBody:
        raise NotImplementedError()


class JettonMintBody(TlbScheme):

    def __init__(
        self,
        destination: AddressLike,
        internal_transfer: JettonInternalTransferBody,
        forward_amount: int,
        query_id: int = 0,
    ) -> None:
        self.query_id = query_id
        self.destination = destination
        self.forward_amount = forward_amount
        self.internal_transfer = internal_transfer

    def serialize(self) -> Cell:
        cell = begin_cell()
        cell.store_uint(OpCode.JETTON_MINT, 32)
        cell.store_uint(self.query_id, 64)
        cell.store_address(self.destination)
        cell.store_coins(self.forward_amount)
        cell.store_ref(self.internal_transfer.serialize())
        return cell.end_cell()

    @classmethod
    def deserialize(cls, cs: Slice) -> JettonMintBody:
        raise NotImplementedError()


class JettonStandardMintBody(TlbScheme):

    def __init__(
        self,
        destination: AddressLike,
        internal_transfer: JettonInternalTransferBody,
        forward_amount: int,
        query_id: int = 0,
    ) -> None:
        self.query_id = query_id
        self.destination = destination
        self.forward_amount = forward_amount
        self.internal_transfer = internal_transfer

    def serialize(self) -> Cell:
        cell = begin_cell()
        cell.store_uint(21, 32)
        cell.store_uint(self.query_id, 64)
        cell.store_address(self.destination)
        cell.store_coins(self.forward_amount)
        cell.store_ref(self.internal_transfer.serialize())
        return cell.end_cell()

    @classmethod
    def deserialize(cls, cs: Slice) -> JettonMintBody:
        raise NotImplementedError()


class JettonChangeAdminBody(TlbScheme):

    def __init__(
        self,
        admin_address: AddressLike,
        query_id: int = 0,
    ) -> None:
        self.query_id = query_id
        self.admin_address = admin_address

    def serialize(self) -> Cell:
        cell = begin_cell()
        cell.store_uint(OpCode.JETTON_CHANGE_ADMIN, 32)
        cell.store_uint(self.query_id, 64)
        cell.store_address(self.admin_address)
        return cell.end_cell()

    @classmethod
    def deserialize(cls, cs: Slice) -> JettonChangeAdminBody:
        raise NotImplementedError()


class JettonStandardChangeAdminBody(TlbScheme):

    def __init__(
        self,
        admin_address: AddressLike,
        query_id: int = 0,
    ) -> None:
        self.query_id = query_id
        self.admin_address = admin_address

    def serialize(self) -> Cell:
        cell = begin_cell()
        cell.store_uint(3, 32)
        cell.store_uint(self.query_id, 64)
        cell.store_address(self.admin_address)
        return cell.end_cell()

    @classmethod
    def deserialize(cls, cs: Slice) -> JettonChangeAdminBody:
        raise NotImplementedError()


class JettonDiscoveryBody(TlbScheme):

    def __init__(
        self,
        owner_address: AddressLike,
        include_address: bool = True,
        query_id: int = 0,
    ) -> None:
        self.query_id = query_id
        self.owner_address = owner_address
        self.include_address = include_address

    def serialize(self) -> Cell:
        cell = begin_cell()
        cell.store_uint(OpCode.JETTON_PROVIDE_WALLET_ADDRESS, 32)
        cell.store_uint(self.query_id, 64)
        cell.store_address(self.owner_address)
        cell.store_bool(self.include_address)
        return cell.end_cell()

    @classmethod
    def deserialize(cls, cs: Slice) -> JettonDiscoveryBody:
        raise NotImplementedError()


class JettonClaimAdminBody(TlbScheme):

    def __init__(self, query_id: int = 0) -> None:
        self.query_id = query_id

    def serialize(self) -> Cell:
        cell = begin_cell()
        cell.store_uint(OpCode.JETTON_CLAIM_ADMIN, 32)
        cell.store_uint(self.query_id, 64)
        return cell.end_cell()

    @classmethod
    def deserialize(cls, cs: Slice) -> JettonClaimAdminBody:
        raise NotImplementedError()


class JettonDropAdminBody(TlbScheme):

    def __init__(self, query_id: int = 0) -> None:
        self.query_id = query_id

    def serialize(self) -> Cell:
        cell = begin_cell()
        cell.store_uint(OpCode.JETTON_DROP_ADMIN, 32)
        cell.store_uint(self.query_id, 64)
        return cell.end_cell()

    @classmethod
    def deserialize(cls, cs: Slice) -> JettonDropAdminBody:
        raise NotImplementedError()


class JettonChangeContentBody(TlbScheme):

    def __init__(
        self,
        content: OffchainContent,
        query_id: int = 0,
    ) -> None:
        self.query_id = query_id
        self.content = content

    def serialize(self) -> Cell:
        cell = begin_cell()
        cell.store_uint(OpCode.JETTON_CHANGE_METADATA, 32)
        cell.store_uint(self.query_id, 64)
        cell.store_snake_string(self.content.uri)
        return cell.end_cell()

    @classmethod
    def deserialize(cls, cs: Slice) -> JettonChangeContentBody:
        raise NotImplementedError()


class JettonStandardChangeContentBody(TlbScheme):

    def __init__(
        self,
        content: t.Union[OnchainContent, OffchainContent],
        query_id: int = 0,
    ) -> None:
        self.query_id = query_id
        self.content = content

    def serialize(self) -> Cell:
        cell = begin_cell()
        cell.store_uint(4, 32)
        cell.store_uint(self.query_id, 64)
        cell.store_ref(self.content.serialize(True))
        return cell.end_cell()

    @classmethod
    def deserialize(cls, cs: Slice) -> JettonStandardChangeContentBody:
        raise NotImplementedError()


class JettonBurnBody(TlbScheme):

    def __init__(
        self,
        jetton_amount: int,
        response_address: AddressLike,
        custom_payload: t.Optional[Cell] = None,
        query_id: int = 0,
    ) -> None:
        self.query_id = query_id
        self.jetton_amount = jetton_amount
        self.response_address = response_address
        self.custom_payload = custom_payload

    def serialize(self) -> Cell:
        cell = begin_cell()
        cell.store_uint(OpCode.JETTON_BURN, 32)
        cell.store_uint(self.query_id, 64)
        cell.store_coins(self.jetton_amount)
        cell.store_address(self.response_address)
        cell.store_maybe_ref(self.custom_payload)
        return cell.end_cell()

    @classmethod
    def deserialize(cls, cs: Slice) -> JettonBurnBody:
        raise NotImplementedError()


class JettonUpgradeBody(TlbScheme):

    def __init__(
        self,
        code: Cell,
        data: Cell,
        query_id: int = 0,
    ) -> None:
        self.query_id = query_id
        self.data = data
        self.code = code

    def serialize(self) -> Cell:
        cell = begin_cell()
        cell.store_uint(OpCode.JETTON_UPGRADE, 32)
        cell.store_uint(self.query_id, 64)
        cell.store_ref(self.data)
        cell.store_ref(self.code)
        return cell.end_cell()

    @classmethod
    def deserialize(cls, cs: Slice) -> JettonUpgradeBody:
        raise NotImplementedError()
