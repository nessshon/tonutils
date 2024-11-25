from enum import Enum

from pytoniq_core import Cell, StateInit


class AccountStatus(str, Enum):
    active = "active"
    nonexist = "nonexist"
    frozen = "frozen"
    uninit = "uninit"


class RawAccount:

    def __init__(
            self,
            balance: int,
            code: Cell,
            data: Cell,
            status: AccountStatus,
            last_transaction_lt: int,
            last_transaction_hash: str,
    ) -> None:
        self.balance = balance
        self.code = code
        self.data = data
        self.status = status
        self.last_transaction_lt = last_transaction_lt
        self.last_transaction_hash = last_transaction_hash

        self.state_init = StateInit(code=code, data=data) if code and data else None
