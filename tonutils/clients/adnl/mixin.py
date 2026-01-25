import typing as t

from pytoniq_core import Address, Block, BlockIdExt, Transaction, Account, ShardAccount

from tonutils.clients.adnl.provider.models import MasterchainInfo
from tonutils.clients.adnl.utils import decode_stack, encode_stack
from tonutils.types import ContractInfo, WorkchainID, AddressLike


class LiteMixin:

    async def _adnl_call(
        self,
        method: str,
        /,
        *args: t.Any,
        **kwargs: t.Any,
    ) -> t.Any:
        """
        Execute a single lite-server provider call.

        This is an internal hook used by the mixin to unify implementations between
        LiteClient (direct call) and LiteBalancer (failover / retry call).

        :param method: Provider coroutine method name (e.g. "get_time", "lookup_block").
        :param args: Positional arguments forwarded to the provider method.
        :param kwargs: Keyword arguments forwarded to the provider method.
        :return: Provider method result.
        """
        raise NotImplementedError("LiteMixin requires `_adnl_call()` implementation.")

    async def _send_message(self, boc: str) -> None:
        method = "send_message"
        await self._adnl_call(method, bytes.fromhex(boc))

    async def _get_config(self) -> t.Dict[int, t.Any]:
        method = "get_config"
        return t.cast(t.Dict[int, t.Any], await self._adnl_call(method))

    async def _get_info(self, address: str) -> ContractInfo:
        method = "get_info"
        return t.cast(
            ContractInfo,
            await self._adnl_call(method, Address(address)),
        )

    async def _run_get_method(
        self,
        address: str,
        method_name: str,
        stack: t.Optional[t.List[t.Any]] = None,
    ) -> t.List[t.Any]:
        method = "run_get_method"
        res = await self._adnl_call(
            method,
            address=Address(address),
            method_name=method_name,
            stack=encode_stack(stack or []),
        )
        return decode_stack(res or [])

    async def _get_transactions(
        self,
        address: str,
        limit: int = 100,
        from_lt: t.Optional[int] = None,
        to_lt: t.Optional[int] = None,
    ) -> t.List[Transaction]:
        method = "get_transactions"

        to_lt_i = 0 if to_lt is None else to_lt
        state = await self._get_info(address)
        account = Address(address).to_tl_account_id()

        if state.last_transaction_lt is None or state.last_transaction_hash is None:
            return []

        curr_lt = state.last_transaction_lt
        curr_hash = state.last_transaction_hash
        out: t.List[Transaction] = []

        while curr_lt != 0:
            fetch_lt = curr_lt
            fetch_hash = curr_hash

            txs = t.cast(
                t.List[Transaction],
                await self._adnl_call(
                    method,
                    account=account,
                    count=16,
                    from_lt=fetch_lt,
                    from_hash=fetch_hash,
                ),
            )
            if not txs:
                break

            for tx in txs:
                if from_lt is not None and tx.lt > from_lt:
                    continue
                if to_lt_i > 0 and tx.lt <= to_lt_i:
                    return out[:limit]

                out.append(tx)
                if len(out) >= limit:
                    return out

            last_tx = txs[-1]
            curr_lt = last_tx.prev_trans_lt
            curr_hash = last_tx.prev_trans_hash.hex()

        return out[:limit]

    async def get_time(self) -> int:
        """
        Fetch current network time from lite-server.

        :return: Current UNIX timestamp
        """
        method = "get_time"
        return t.cast(int, await self._adnl_call(method))

    async def get_version(self) -> int:
        """
        Fetch lite-server protocol version.

        :return: Version number
        """
        method = "get_version"
        return t.cast(int, await self._adnl_call(method))

    async def get_masterchain_info(self) -> MasterchainInfo:
        """
        Fetch basic masterchain information.

        :return: MasterchainInfo instance
        """
        method = "get_masterchain_info"
        return t.cast(MasterchainInfo, await self._adnl_call(method))

    async def wait_masterchain_seqno(
        self,
        seqno: int,
        timeout_ms: int,
        schema_name: str,
        data: t.Optional[dict] = None,
    ) -> t.Dict[str, t.Any]:
        """
        Combine waitMasterchainSeqno with another lite-server query.

        :param seqno: Masterchain seqno to wait for
        :param timeout_ms: Wait timeout in milliseconds
        :param schema_name: Lite-server TL method name without prefix
        :param data: Additional method arguments
        :return: Lite-server response as dictionary
        """
        method = "wait_masterchain_seqno"
        return t.cast(
            t.Dict[str, t.Any],
            await self._adnl_call(
                method,
                seqno=seqno,
                timeout_ms=timeout_ms,
                schema_name=schema_name,
                data=data,
            ),
        )

    async def lookup_block(
        self,
        workchain: WorkchainID,
        shard: int,
        seqno: t.Optional[int] = None,
        lt: t.Optional[int] = None,
        utime: t.Optional[int] = None,
    ) -> t.Tuple[BlockIdExt, Block]:
        """
        Locate a block by workchain/shard and one of seqno/lt/utime.

        :param workchain: Workchain identifier
        :param shard: Shard identifier
        :param seqno: Block sequence number
        :param lt: Logical time filter
        :param utime: UNIX time filter
        :return: Tuple of BlockIdExt and deserialized Block
        """
        method = "lookup_block"
        return t.cast(
            t.Tuple[BlockIdExt, Block],
            await self._adnl_call(
                method,
                workchain=workchain,
                shard=shard,
                seqno=seqno,
                lt=lt,
                utime=utime,
            ),
        )

    async def get_block_header(
        self,
        block: BlockIdExt,
    ) -> t.Tuple[BlockIdExt, Block]:
        """
        Fetch and deserialize block header by BlockIdExt.

        :param block: BlockIdExt to query
        :return: Tuple of BlockIdExt and deserialized Block
        """
        method = "get_block_header"
        return t.cast(
            t.Tuple[BlockIdExt, Block],
            await self._adnl_call(method, block),
        )

    async def get_block_transactions(
        self,
        block: BlockIdExt,
        count: int = 1024,
    ) -> t.List[Transaction]:
        """
        Fetch extended block transactions list.

        :param block: Target block identifier
        :param count: Maximum number of transactions per request
        :return: List of deserialized Transaction objects
        """
        method = "get_block_transactions"
        return t.cast(
            t.List[Transaction],
            await self._adnl_call(method, block, count=count),
        )

    async def get_all_shards_info(
        self,
        block: t.Optional[BlockIdExt] = None,
    ) -> t.List[BlockIdExt]:
        """
        Fetch shard info for all workchains at a given masterchain block.

        :param block: Masterchain block ID or None to use latest
        :return: List of shard BlockIdExt objects
        """
        method = "get_all_shards_info"
        return t.cast(
            t.List[BlockIdExt],
            await self._adnl_call(method, block),
        )

    async def get_account_state(
        self,
        address: AddressLike,
    ) -> t.Tuple[t.Optional[Account], t.Optional[ShardAccount]]:
        """
        Fetch account state and shard account from lite-server.

        :param address: Contract address as Address object or string
        :return: Tuple of (Account | None, ShardAccount | None)
        """
        if isinstance(address, str):
            address = Address(address)

        method = "get_account_state"
        return t.cast(
            t.Tuple[t.Optional[Account], t.Optional[ShardAccount]],
            await self._adnl_call(method, address),
        )
