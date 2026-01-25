import typing as t

from pytoniq_core import (
    Account,
    Address,
    BlockIdExt,
    Cell,
    ConfigParam,
    ShardAccount,
    ShardStateUnsplit,
    SimpleAccount,
    begin_cell,
    check_account_proof,
    Slice,
    VmTuple,
)

from tonutils.types import ContractState, ContractInfo, StackItems, StackItem
from tonutils.utils import cell_to_hex, norm_stack_num, norm_stack_cell


def build_config_all(config_proof: Cell) -> t.Dict[int, t.Any]:
    """
    Decode full blockchain configuration from a config proof cell.

    :param config_proof: Root cell containing the config proof
    :return: Mapping of config parameter IDs to decoded values
    """
    shard = ShardStateUnsplit.deserialize(config_proof[0].begin_parse())
    result: t.Dict[int, t.Any] = {}

    for pid, cell in shard.custom.config.config.items():
        if pid in ConfigParam.params:
            result[pid] = ConfigParam.params[pid].deserialize(cell)
        else:
            result[pid] = cell
    return result


def build_shard_account(
    account_state_root: Cell,
    shard_account_descr: bytes,
    shrd_blk: BlockIdExt,
    address: Address,
) -> ShardAccount:
    """
    Construct a ShardAccount object from proof data.

    :param account_state_root: Root cell of the account state
    :param shard_account_descr: Proof bytes for the account descriptor
    :param shrd_blk: Block ID the proof applies to
    :param address: Account address being verified
    :return: Parsed ShardAccount instance
    """
    shard_descr = check_account_proof(
        proof=shard_account_descr,
        shrd_blk=shrd_blk,
        address=address,
        account_state_root=account_state_root,
        return_account_descr=True,
    )

    full_shard_builder = begin_cell()
    full_shard_builder.store_bytes(shard_descr.cell.begin_parse().load_bytes(40))
    full_shard_builder.store_ref(account_state_root)
    full_shard_cs = full_shard_builder.to_slice()

    return ShardAccount.deserialize(full_shard_cs)


def build_contract_state_info(
    address: Address,
    account: Account,
    shard_account: ShardAccount,
) -> ContractInfo:
    """
    Build a high-level ContractInfo object from raw account data.

    :param address: Contract address
    :param account: Raw Account data structure
    :param shard_account: Parsed ShardAccount entry
    :return: Filled ContractInfo instance
    """
    simple_account = SimpleAccount.from_raw(account, address)
    info = ContractInfo(balance=simple_account.balance)

    if simple_account.state is not None:
        state_init = simple_account.state.state_init
        if state_init is not None:
            if state_init.code is not None:
                info.code_raw = cell_to_hex(state_init.code)
            if state_init.data is not None:
                info.data_raw = cell_to_hex(state_init.data)

        info.state = ContractState(
            "uninit"
            if simple_account.state.type_ == "uninitialized"
            else simple_account.state.type_
        )

    if shard_account.last_trans_lt is not None:
        info.last_transaction_lt = int(shard_account.last_trans_lt)
    if shard_account.last_trans_hash is not None:
        info.last_transaction_hash = shard_account.last_trans_hash.hex()

    if (
        info.last_transaction_lt is None
        and info.last_transaction_hash is None
        and info.state == ContractState.UNINIT
    ):
        info.state = ContractState.NONEXIST

    return info


def decode_stack(items: t.List[t.Any]) -> StackItems:
    """
    Decode VM stack items into internal Python structures.

    Supports:
    - int → int
    - Cell/Slice → normalized cell
    - Address → address cell
    - VmTuple/list → recursive decode
    - None → None

    :param items: Raw VM stack items
    :return: Normalized Python stack values
    """

    out: StackItems = []
    for item in items:
        if item is None:
            out.append(None)
        elif isinstance(item, int):
            out.append(norm_stack_num(item))
        elif isinstance(item, Address):
            out.append(item.to_cell())
        elif isinstance(item, (Cell, Slice)):
            out.append(norm_stack_cell(item))
        elif isinstance(item, VmTuple):
            out.append(decode_stack(item.list))
        elif isinstance(item, list):
            out.append(decode_stack(item))
    return out


def encode_stack(items: t.List[StackItem]) -> t.List[t.Any]:
    """
    Encode Python stack values into VM-compatible format.

    Supports:
    - int → int
    - Cell/Slice → cell/slice
    - Address → cell slice
    - list/tuple → recursive encode

    :param items: Normalized Python stack items
    :return: VM-encoded stack values
    """
    out: t.List[t.Any] = []
    for item in items:
        if isinstance(item, int):
            out.append(item)
        elif isinstance(item, Address):
            out.append(item.to_cell().to_slice())
        elif isinstance(item, (Cell, Slice)):
            out.append(item)
        elif isinstance(item, (list, tuple)):
            out.append(encode_stack(list(item)))
    return out
