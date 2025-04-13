from typing import Optional, Union, Any

from pytoniq_core import (
    Address,
    Cell,
    StateInit,
    CurrencyCollection,
    ExternalMsgInfo,
    InternalMsgInfo,
    MessageAny,
    begin_cell,
)

from .account import RawAccount
from .client import (
    Client,
)
from .utils import to_amount


class Contract:
    """
    Base class representing a smart contract in the TON blockchain.
    """
    CODE_HEX: Optional[str] = None

    _code: Cell
    _data: Cell

    @property
    def code(self) -> Cell:
        """
        Retrieve the code of the contract.
        """
        return self.state_init.code

    @property
    def data(self) -> Cell:
        """
        Retrieve the data of the contract.
        """
        return self.state_init.data

    @property
    def address(self) -> Address:
        """
        Retrieve the address of the contract.
        """
        return Address((0, self.state_init.serialize().hash))

    @property
    def state_init(self) -> StateInit:
        """
        Retrieve the state init of the contract.
        """
        return StateInit.deserialize(
            begin_cell()
            .store_uint(0, 2)
            .store_dict(self._code)
            .store_dict(self._data)
            .store_uint(0, 1)
            .end_cell()
            .to_slice()
        )

    @classmethod
    async def get_raw_account(
            cls,
            client: Client,
            address: Union[Address, str],
    ) -> RawAccount:
        """
        Fetch the raw account data from the blockchain for the given address.
        """
        if isinstance(address, Address):
            address = address.to_str()

        raw_account = await client.get_raw_account(address)
        return raw_account

    @classmethod
    def create_data(cls, *args, **kwargs) -> Any:
        """
        Create contract data.

        :param kwargs: Additional arguments.
        :return: Contract data instance.
        """
        raise NotImplementedError

    @classmethod
    def create_external_msg(
            cls,
            src: Optional[Address] = None,
            dest: Optional[Address] = None,
            import_fee: int = 0,
            body: Optional[Cell] = None,
            state_init: Optional[StateInit] = None,
    ) -> MessageAny:
        """
        Create an external message for the contract.

        :param src: The source address of the message.
        :param dest: The destination address of the message.
        :param import_fee: The import fee for the message.
        :param body: The body of the message.
        :param state_init: The state init data.
        :return: The external message.
        """
        info = ExternalMsgInfo(src=src, dest=dest, import_fee=import_fee)

        return MessageAny(info, state_init, body)

    @classmethod
    def create_internal_msg(
            cls,
            ihr_disabled: Optional[bool] = True,
            bounce: Optional[bool] = None,
            bounced: Optional[bool] = False,
            src: Optional[Address] = None,
            dest: Optional[Address] = None,
            value: Union[CurrencyCollection, int] = 0,
            ihr_fee: int = 0,
            fwd_fee: int = 0,
            created_lt: int = 0,
            created_at: int = 0,
            body: Optional[Cell] = None,
            state_init: Optional[StateInit] = None,
    ) -> MessageAny:
        """
        Create an internal message for the contract.

        :param ihr_disabled: Flag to disable Intra-shard routing.
        :param bounce: Flag to indicate if the message should bounce.
        :param bounced: Flag to indicate if the message has already bounced.
        :param src: The source address of the message.
        :param dest: The destination address of the message.
        :param value: The value of the message.
        :param ihr_fee: The Intra-shard routing fee.
        :param fwd_fee: The forwarding fee.
        :param created_lt: The logical time the message was created.
        :param created_at: The time the message was created.
        :param body: The body of the message.
        :param state_init: The state init data.
        :return: The internal message.
        """
        if isinstance(value, int):
            value = CurrencyCollection(value)

        if bounce is None:
            bounce = dest.is_bounceable if dest is not None else False

        info = InternalMsgInfo(
            ihr_disabled=ihr_disabled,
            bounce=bounce,
            bounced=bounced,
            src=src,
            dest=dest,
            value=value,
            ihr_fee=ihr_fee,
            fwd_fee=fwd_fee,
            created_lt=created_lt,
            created_at=created_at,
        )

        if body is None:
            body = Cell.empty()

        return MessageAny(info, state_init, body)

    @classmethod
    async def get_balance(cls, client: Client, address: Union[Address, str]) -> float:
        """
        Retrieve the current balance of the contract in TON.
        """
        if isinstance(address, str):
            address = Address(address)

        balance = await client.get_account_balance(address.to_str())
        return to_amount(balance, precision=9)
