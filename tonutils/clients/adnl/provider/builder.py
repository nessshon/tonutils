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
)

from tonutils.types import ContractState, ContractStateInfo
from tonutils.utils import cell_to_hex


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
) -> ContractStateInfo:
    """
    Build a high-level ContractStateInfo object from raw account data.

    :param address: Contract address
    :param account: Raw Account data structure
    :param shard_account: Parsed ShardAccount entry
    :return: Filled ContractStateInfo instance
    """
    simple_account = SimpleAccount.from_raw(account, address)
    info = ContractStateInfo(balance=simple_account.balance)

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
