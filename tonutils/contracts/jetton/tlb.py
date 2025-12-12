from __future__ import annotations

import typing as t

from pytoniq_core import Cell, Slice, TlbScheme, begin_cell

from tonutils.contracts.nft.tlb import OnchainContent, OffchainContent
from tonutils.contracts.opcodes import OpCode
from tonutils.types import AddressLike, MetadataPrefix


class JettonMasterStandardData(TlbScheme):
    """On-chain data for standard jetton minter contracts (TEP-74)."""

    def __init__(
        self,
        admin_address: AddressLike,
        content: t.Union[OnchainContent, OffchainContent],
        jetton_wallet_code: Cell,
        total_supply: int = 0,
    ) -> None:
        """
        Initialize standard jetton minter data.

        :param admin_address: Admin address with minting/management rights
        :param content: Jetton metadata (on-chain or off-chain)
        :param jetton_wallet_code: Code cell for jetton wallet contracts
        :param total_supply: Total minted supply in base units (default: 0)
        """
        self.total_supply = total_supply
        self.admin_address = admin_address
        self.content = content
        self.jetton_wallet_code = jetton_wallet_code

    def serialize(self) -> Cell:
        """
        Serialize minter data to Cell.

        Layout: total_supply:coins admin:address content:^Cell jetton_wallet_code:^Cell

        :return: Serialized data cell
        """
        cell = begin_cell()
        cell.store_coins(self.total_supply)
        cell.store_address(self.admin_address)
        cell.store_ref(self.content.serialize(True))
        cell.store_ref(self.jetton_wallet_code)
        return cell.end_cell()

    @classmethod
    def deserialize(cls, cs: Slice) -> JettonMasterStandardData:
        """
        Deserialize minter data from Cell slice.

        :param cs: Cell slice to deserialize from
        :return: Deserialized JettonMasterStandardData instance
        """
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
    """On-chain data for stablecoin jetton minter contracts."""

    def __init__(
        self,
        admin_address: AddressLike,
        jetton_wallet_code: Cell,
        content: OffchainContent,
        next_admin_address: t.Optional[AddressLike] = None,
        total_supply: int = 0,
    ) -> None:
        """
        Initialize stablecoin jetton minter data.

        :param admin_address: Current admin address
        :param jetton_wallet_code: Code cell for jetton wallet contracts
        :param content: Off-chain jetton metadata
        :param next_admin_address: Pending admin address for transition (default: None)
        :param total_supply: Total minted supply in base units (default: 0)
        """
        self.total_supply = total_supply
        self.admin_address = admin_address
        self.next_admin_address = next_admin_address
        self.jetton_wallet_code = jetton_wallet_code
        self.content = content

    def serialize(self) -> Cell:
        """
        Serialize minter data to Cell.

        Layout: total_supply:coins admin:address next_admin:address
                jetton_wallet_code:^Cell content:^Cell

        :return: Serialized data cell
        """
        cell = begin_cell()
        cell.store_coins(self.total_supply)
        cell.store_address(self.admin_address)
        cell.store_address(self.next_admin_address)
        cell.store_ref(self.jetton_wallet_code)
        cell.store_ref(self.content.serialize(False))
        return cell.end_cell()

    @classmethod
    def deserialize(cls, cs: Slice) -> JettonMasterStablecoinData:
        """
        Deserialize minter data from Cell slice.

        :param cs: Cell slice to deserialize from
        :return: Deserialized JettonMasterStablecoinData instance
        """
        return cls(
            total_supply=cs.load_coins(),
            admin_address=cs.load_address(),
            next_admin_address=cs.load_address(),
            jetton_wallet_code=cs.load_ref(),
            content=OffchainContent.deserialize(cs.load_ref().begin_parse(), False),
        )


class JettonWalletStandardData(TlbScheme):
    """On-chain data for standard jetton wallet contracts (TEP-74)."""

    def __init__(
        self,
        owner_address: AddressLike,
        jetton_master_address: AddressLike,
        jetton_wallet_code: Cell,
        balance: int = 0,
    ) -> None:
        """
        Initialize standard jetton wallet data.

        :param owner_address: Wallet owner address
        :param jetton_master_address: Jetton minter contract address
        :param jetton_wallet_code: Code cell for jetton wallet contracts
        :param balance: Current jetton balance in base units (default: 0)
        """
        self.balance = balance
        self.owner_address = owner_address
        self.jetton_master_address = jetton_master_address
        self.jetton_wallet_code = jetton_wallet_code

    def serialize(self) -> Cell:
        """
        Serialize wallet data to Cell.

        Layout: balance:coins owner:address jetton_master:address jetton_wallet_code:^Cell

        :return: Serialized data cell
        """
        cell = begin_cell()
        cell.store_coins(self.balance)
        cell.store_address(self.owner_address)
        cell.store_address(self.jetton_master_address)
        cell.store_ref(self.jetton_wallet_code)
        return cell.end_cell()

    @classmethod
    def deserialize(cls, cs: Slice) -> JettonWalletStandardData:
        """
        Deserialize wallet data from Cell slice.

        :param cs: Cell slice to deserialize from
        :return: Deserialized JettonWalletStandardData instance
        """
        return cls(
            balance=cs.load_coins(),
            owner_address=cs.load_address(),
            jetton_master_address=cs.load_address(),
            jetton_wallet_code=cs.load_ref(),
        )


class JettonWalletStablecoinData(TlbScheme):
    """On-chain data for stablecoin jetton wallet contracts."""

    def __init__(
        self,
        owner_address: AddressLike,
        jetton_master_address: AddressLike,
        status: int,
        balance: int = 0,
    ) -> None:
        """
        Initialize stablecoin jetton wallet data.

        :param owner_address: Wallet owner address
        :param jetton_master_address: Jetton minter contract address
        :param status: Wallet status flags (4 bits)
        :param balance: Current jetton balance in base units (default: 0)
        """
        self.status = status
        self.balance = balance
        self.owner_address = owner_address
        self.jetton_master_address = jetton_master_address

    def serialize(self) -> Cell:
        """
        Serialize wallet data to Cell.

        Layout: status:uint4 balance:coins owner:address jetton_master:address

        :return: Serialized data cell
        """
        cell = begin_cell()
        cell.store_uint(self.status, 4)
        cell.store_coins(self.balance)
        cell.store_address(self.owner_address)
        cell.store_address(self.jetton_master_address)
        return cell.end_cell()

    @classmethod
    def deserialize(cls, cs: Slice) -> JettonWalletStablecoinData:
        """
        Deserialize wallet data from Cell slice.

        :param cs: Cell slice to deserialize from
        :return: Deserialized JettonWalletStablecoinData instance
        """
        return cls(
            status=cs.load_uint(4),
            balance=cs.load_coins(),
            owner_address=cs.load_address(),
            jetton_master_address=cs.load_address(),
        )


class JettonWalletStablecoinV2Data(TlbScheme):
    """On-chain data for stablecoin jetton wallet contracts v2."""

    def __init__(
        self,
        owner_address: AddressLike,
        jetton_master_address: AddressLike,
        balance: int = 0,
    ) -> None:
        """
        Initialize stablecoin v2 jetton wallet data.

        :param owner_address: Wallet owner address
        :param jetton_master_address: Jetton minter contract address
        :param balance: Current jetton balance in base units (default: 0)
        """
        self.balance = balance
        self.owner_address = owner_address
        self.jetton_master_address = jetton_master_address

    def serialize(self) -> Cell:
        """
        Serialize wallet data to Cell.

        Layout: balance:coins owner:address jetton_master:address

        :return: Serialized data cell
        """
        cell = begin_cell()
        cell.store_coins(self.balance)
        cell.store_address(self.owner_address)
        cell.store_address(self.jetton_master_address)
        return cell.end_cell()

    @classmethod
    def deserialize(cls, cs: Slice) -> JettonWalletStablecoinV2Data:
        """
        Deserialize wallet data from Cell slice.

        :param cs: Cell slice to deserialize from
        :return: Deserialized JettonWalletStablecoinV2Data instance
        """
        return cls(
            balance=cs.load_coins(),
            owner_address=cs.load_address(),
            jetton_master_address=cs.load_address(),
        )


class JettonTopUpBody(TlbScheme):
    """Message body for topping up jetton wallet balance."""

    def __init__(self, query_id: int = 0) -> None:
        """
        Initialize top-up message body.

        :param query_id: Query identifier (default: 0)
        """
        self.query_id = query_id

    def serialize(self) -> Cell:
        """
        Serialize top-up body to Cell.

        Layout: op_code:uint32 query_id:uint64

        :return: Serialized message body cell
        """
        cell = begin_cell()
        cell.store_uint(OpCode.TOP_UP, 32)
        cell.store_uint(self.query_id, 64)
        return cell.end_cell()

    @classmethod
    def deserialize(cls, cs: Slice) -> JettonTopUpBody:
        """
        Deserialize top-up body from Cell slice.

        :param cs: Cell slice to deserialize from
        :return: Deserialized JettonTopUpBody instance
        """
        raise NotImplementedError


class JettonInternalTransferBody(TlbScheme):
    """Message body for internal jetton transfers between wallets."""

    def __init__(
        self,
        jetton_amount: int,
        forward_amount: int,
        from_address: t.Optional[AddressLike] = None,
        response_address: t.Optional[AddressLike] = None,
        forward_payload: t.Optional[Cell] = None,
        query_id: int = 0,
    ) -> None:
        """
        Initialize internal transfer message body.

        :param jetton_amount: Amount of jettons to transfer in base units
        :param forward_amount: Amount to forward in nanotons
        :param from_address: Original sender address (default: None)
        :param response_address: Address for excess funds (default: None)
        :param forward_payload: Optional payload to forward (default: None)
        :param query_id: Query identifier (default: 0)
        """
        self.query_id = query_id
        self.jetton_amount = jetton_amount
        self.from_address = from_address
        self.response_address = response_address
        self.forward_amount = forward_amount
        self.forward_payload = forward_payload

    def serialize(self) -> Cell:
        """
        Serialize internal transfer body to Cell.

        Layout: op_code:uint32 query_id:uint64 jetton_amount:coins from:address
                response:address forward_amount:coins forward_payload:^Cell

        :return: Serialized message body cell
        """
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
        """
        Deserialize internal transfer body from Cell slice.

        :param cs: Cell slice to deserialize from
        :return: Deserialized JettonInternalTransferBody instance
        """
        raise NotImplementedError


class JettonTransferBody(TlbScheme):
    """Message body for jetton transfers (TEP-74)."""

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
        """
        Initialize jetton transfer message body.

        :param destination: Recipient address
        :param jetton_amount: Amount of jettons to transfer in base units
        :param response_address: Address for excess funds (default: None)
        :param custom_payload: Optional custom payload cell (default: None)
        :param forward_payload: Optional payload to forward to recipient (default: None)
        :param forward_amount: Amount to forward in nanotons (default: 1)
        :param query_id: Query identifier (default: 0)
        """
        self.query_id = query_id
        self.jetton_amount = jetton_amount
        self.destination = destination
        self.response_address = response_address
        self.custom_payload = custom_payload
        self.forward_amount = forward_amount
        self.forward_payload = forward_payload

    def serialize(self) -> Cell:
        """
        Serialize transfer body to Cell.

        Layout: op_code:uint32 query_id:uint64 jetton_amount:coins destination:address
                response:address custom_payload:^Cell forward_amount:coins forward_payload:^Cell

        :return: Serialized message body cell
        """
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
        """
        Deserialize transfer body from Cell slice.

        :param cs: Cell slice to deserialize from
        :return: Deserialized JettonTransferBody instance
        """
        raise NotImplementedError


class JettonMintBody(TlbScheme):
    """Message body for minting jettons (stablecoin version)."""

    def __init__(
        self,
        destination: AddressLike,
        internal_transfer: JettonInternalTransferBody,
        forward_amount: int,
        query_id: int = 0,
    ) -> None:
        """
        Initialize mint message body.

        :param destination: Recipient wallet address
        :param internal_transfer: Internal transfer body with mint details
        :param forward_amount: Amount to forward in nanotons
        :param query_id: Query identifier (default: 0)
        """
        self.query_id = query_id
        self.destination = destination
        self.forward_amount = forward_amount
        self.internal_transfer = internal_transfer

    def serialize(self) -> Cell:
        """
        Serialize mint body to Cell.

        Layout: op_code:uint32 query_id:uint64 destination:address
                forward_amount:coins internal_transfer:^Cell

        :return: Serialized message body cell
        """
        cell = begin_cell()
        cell.store_uint(OpCode.JETTON_MINT, 32)
        cell.store_uint(self.query_id, 64)
        cell.store_address(self.destination)
        cell.store_coins(self.forward_amount)
        cell.store_ref(self.internal_transfer.serialize())
        return cell.end_cell()

    @classmethod
    def deserialize(cls, cs: Slice) -> JettonMintBody:
        """
        Deserialize mint body from Cell slice.

        :param cs: Cell slice to deserialize from
        :return: Deserialized JettonMintBody instance
        """
        raise NotImplementedError


class JettonStandardMintBody(TlbScheme):
    """Message body for minting jettons (standard version)."""

    def __init__(
        self,
        destination: AddressLike,
        internal_transfer: JettonInternalTransferBody,
        forward_amount: int,
        query_id: int = 0,
    ) -> None:
        """
        Initialize standard mint message body.

        :param destination: Recipient wallet address
        :param internal_transfer: Internal transfer body with mint details
        :param forward_amount: Amount to forward in nanotons
        :param query_id: Query identifier (default: 0)
        """
        self.query_id = query_id
        self.destination = destination
        self.forward_amount = forward_amount
        self.internal_transfer = internal_transfer

    def serialize(self) -> Cell:
        """
        Serialize mint body to Cell.

        Layout: op_code:uint32 query_id:uint64 destination:address
                forward_amount:coins internal_transfer:^Cell

        :return: Serialized message body cell
        """
        cell = begin_cell()
        cell.store_uint(21, 32)
        cell.store_uint(self.query_id, 64)
        cell.store_address(self.destination)
        cell.store_coins(self.forward_amount)
        cell.store_ref(self.internal_transfer.serialize())
        return cell.end_cell()

    @classmethod
    def deserialize(cls, cs: Slice) -> JettonMintBody:
        """
        Deserialize mint body from Cell slice.

        :param cs: Cell slice to deserialize from
        :return: Deserialized JettonStandardMintBody instance
        """
        raise NotImplementedError


class JettonChangeAdminBody(TlbScheme):
    """Message body for changing jetton minter admin (stablecoin version)."""

    def __init__(
        self,
        admin_address: AddressLike,
        query_id: int = 0,
    ) -> None:
        """
        Initialize change admin message body.

        :param admin_address: New admin address
        :param query_id: Query identifier (default: 0)
        """
        self.query_id = query_id
        self.admin_address = admin_address

    def serialize(self) -> Cell:
        """
        Serialize change admin body to Cell.

        Layout: op_code:uint32 query_id:uint64 admin:address

        :return: Serialized message body cell
        """
        cell = begin_cell()
        cell.store_uint(OpCode.JETTON_CHANGE_ADMIN, 32)
        cell.store_uint(self.query_id, 64)
        cell.store_address(self.admin_address)
        return cell.end_cell()

    @classmethod
    def deserialize(cls, cs: Slice) -> JettonChangeAdminBody:
        """
        Deserialize change admin body from Cell slice.

        :param cs: Cell slice to deserialize from
        :return: Deserialized JettonChangeAdminBody instance
        """
        raise NotImplementedError


class JettonStandardChangeAdminBody(TlbScheme):
    """Message body for changing jetton minter admin (standard version)."""

    def __init__(
        self,
        admin_address: AddressLike,
        query_id: int = 0,
    ) -> None:
        """
        Initialize standard change admin message body.

        :param admin_address: New admin address
        :param query_id: Query identifier (default: 0)
        """
        self.query_id = query_id
        self.admin_address = admin_address

    def serialize(self) -> Cell:
        """
        Serialize change admin body to Cell.

        Layout: op_code:uint32 query_id:uint64 admin:address

        :return: Serialized message body cell
        """
        cell = begin_cell()
        cell.store_uint(3, 32)
        cell.store_uint(self.query_id, 64)
        cell.store_address(self.admin_address)
        return cell.end_cell()

    @classmethod
    def deserialize(cls, cs: Slice) -> JettonChangeAdminBody:
        """
        Deserialize change admin body from Cell slice.

        :param cs: Cell slice to deserialize from
        :return: Deserialized JettonStandardChangeAdminBody instance
        """
        raise NotImplementedError


class JettonDiscoveryBody(TlbScheme):
    """Message body for discovering jetton wallet address."""

    def __init__(
        self,
        owner_address: AddressLike,
        include_address: bool = True,
        query_id: int = 0,
    ) -> None:
        """
        Initialize discovery message body.

        :param owner_address: Owner address to query wallet for
        :param include_address: Whether to include address in response (default: True)
        :param query_id: Query identifier (default: 0)
        """
        self.query_id = query_id
        self.owner_address = owner_address
        self.include_address = include_address

    def serialize(self) -> Cell:
        """
        Serialize discovery body to Cell.

        Layout: op_code:uint32 query_id:uint64 owner:address include_address:bool

        :return: Serialized message body cell
        """
        cell = begin_cell()
        cell.store_uint(OpCode.JETTON_PROVIDE_WALLET_ADDRESS, 32)
        cell.store_uint(self.query_id, 64)
        cell.store_address(self.owner_address)
        cell.store_bool(self.include_address)
        return cell.end_cell()

    @classmethod
    def deserialize(cls, cs: Slice) -> JettonDiscoveryBody:
        """
        Deserialize discovery body from Cell slice.

        :param cs: Cell slice to deserialize from
        :return: Deserialized JettonDiscoveryBody instance
        """
        raise NotImplementedError


class JettonClaimAdminBody(TlbScheme):
    """Message body for claiming jetton minter admin rights."""

    def __init__(self, query_id: int = 0) -> None:
        """
        Initialize claim admin message body.

        :param query_id: Query identifier (default: 0)
        """
        self.query_id = query_id

    def serialize(self) -> Cell:
        """
        Serialize claim admin body to Cell.

        Layout: op_code:uint32 query_id:uint64

        :return: Serialized message body cell
        """
        cell = begin_cell()
        cell.store_uint(OpCode.JETTON_CLAIM_ADMIN, 32)
        cell.store_uint(self.query_id, 64)
        return cell.end_cell()

    @classmethod
    def deserialize(cls, cs: Slice) -> JettonClaimAdminBody:
        """
        Deserialize claim admin body from Cell slice.

        :param cs: Cell slice to deserialize from
        :return: Deserialized JettonClaimAdminBody instance
        """
        raise NotImplementedError


class JettonDropAdminBody(TlbScheme):
    """Message body for dropping jetton minter admin rights."""

    def __init__(self, query_id: int = 0) -> None:
        """
        Initialize drop admin message body.

        :param query_id: Query identifier (default: 0)
        """
        self.query_id = query_id

    def serialize(self) -> Cell:
        """
        Serialize drop admin body to Cell.

        Layout: op_code:uint32 query_id:uint64

        :return: Serialized message body cell
        """
        cell = begin_cell()
        cell.store_uint(OpCode.JETTON_DROP_ADMIN, 32)
        cell.store_uint(self.query_id, 64)
        return cell.end_cell()

    @classmethod
    def deserialize(cls, cs: Slice) -> JettonDropAdminBody:
        """
        Deserialize drop admin body from Cell slice.

        :param cs: Cell slice to deserialize from
        :return: Deserialized JettonDropAdminBody instance
        """
        raise NotImplementedError


class JettonChangeContentBody(TlbScheme):
    """Message body for changing jetton metadata (stablecoin version)."""

    def __init__(
        self,
        content: OffchainContent,
        query_id: int = 0,
    ) -> None:
        """
        Initialize change content message body.

        :param content: New off-chain content URI
        :param query_id: Query identifier (default: 0)
        """
        self.query_id = query_id
        self.content = content

    def serialize(self) -> Cell:
        """
        Serialize change content body to Cell.

        Layout: op_code:uint32 query_id:uint64 uri:snake_string

        :return: Serialized message body cell
        """
        cell = begin_cell()
        cell.store_uint(OpCode.JETTON_CHANGE_METADATA, 32)
        cell.store_uint(self.query_id, 64)
        cell.store_snake_string(self.content.uri)
        return cell.end_cell()

    @classmethod
    def deserialize(cls, cs: Slice) -> JettonChangeContentBody:
        """
        Deserialize change content body from Cell slice.

        :param cs: Cell slice to deserialize from
        :return: Deserialized JettonChangeContentBody instance
        """
        raise NotImplementedError


class JettonStandardChangeContentBody(TlbScheme):
    """Message body for changing jetton metadata (standard version)."""

    def __init__(
        self,
        content: t.Union[OnchainContent, OffchainContent],
        query_id: int = 0,
    ) -> None:
        """
        Initialize standard change content message body.

        :param content: New content (on-chain or off-chain)
        :param query_id: Query identifier (default: 0)
        """
        self.query_id = query_id
        self.content = content

    def serialize(self) -> Cell:
        """
        Serialize change content body to Cell.

        Layout: op_code:uint32 query_id:uint64 content:^Cell

        :return: Serialized message body cell
        """
        cell = begin_cell()
        cell.store_uint(4, 32)
        cell.store_uint(self.query_id, 64)
        cell.store_ref(self.content.serialize(True))
        return cell.end_cell()

    @classmethod
    def deserialize(cls, cs: Slice) -> JettonStandardChangeContentBody:
        """
        Deserialize change content body from Cell slice.

        :param cs: Cell slice to deserialize from
        :return: Deserialized JettonStandardChangeContentBody instance
        """
        raise NotImplementedError


class JettonBurnBody(TlbScheme):
    """Message body for burning jettons (TEP-74)."""

    def __init__(
        self,
        jetton_amount: int,
        response_address: AddressLike,
        custom_payload: t.Optional[Cell] = None,
        query_id: int = 0,
    ) -> None:
        """
        Initialize burn message body.

        :param jetton_amount: Amount of jettons to burn in base units
        :param response_address: Address for excess funds
        :param custom_payload: Optional custom payload cell (default: None)
        :param query_id: Query identifier (default: 0)
        """
        self.query_id = query_id
        self.jetton_amount = jetton_amount
        self.response_address = response_address
        self.custom_payload = custom_payload

    def serialize(self) -> Cell:
        """
        Serialize burn body to Cell.

        Layout: op_code:uint32 query_id:uint64 jetton_amount:coins
                response:address custom_payload:^Cell

        :return: Serialized message body cell
        """
        cell = begin_cell()
        cell.store_uint(OpCode.JETTON_BURN, 32)
        cell.store_uint(self.query_id, 64)
        cell.store_coins(self.jetton_amount)
        cell.store_address(self.response_address)
        cell.store_maybe_ref(self.custom_payload)
        return cell.end_cell()

    @classmethod
    def deserialize(cls, cs: Slice) -> JettonBurnBody:
        """
        Deserialize burn body from Cell slice.

        :param cs: Cell slice to deserialize from
        :return: Deserialized JettonBurnBody instance
        """
        raise NotImplementedError


class JettonUpgradeBody(TlbScheme):
    """Message body for upgrading jetton contract code."""

    def __init__(
        self,
        code: Cell,
        data: Cell,
        query_id: int = 0,
    ) -> None:
        """
        Initialize upgrade message body.

        :param code: New contract code cell
        :param data: New contract data cell
        :param query_id: Query identifier (default: 0)
        """
        self.query_id = query_id
        self.data = data
        self.code = code

    def serialize(self) -> Cell:
        """
        Serialize upgrade body to Cell.

        Layout: op_code:uint32 query_id:uint64 data:^Cell code:^Cell

        :return: Serialized message body cell
        """
        cell = begin_cell()
        cell.store_uint(OpCode.JETTON_UPGRADE, 32)
        cell.store_uint(self.query_id, 64)
        cell.store_ref(self.data)
        cell.store_ref(self.code)
        return cell.end_cell()

    @classmethod
    def deserialize(cls, cs: Slice) -> JettonUpgradeBody:
        """
        Deserialize upgrade body from Cell slice.

        :param cs: Cell slice to deserialize from
        :return: Deserialized JettonUpgradeBody instance
        """
        raise NotImplementedError
