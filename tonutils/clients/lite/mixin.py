import typing as t

from ton_core import (
    Account,
    Address,
    AddressLike,
    Block,
    BlockIdExt,
    Cell,
    ShardAccount,
    Slice,
    Transaction,
    VmTuple,
    WorkchainID,
    norm_stack_cell,
    norm_stack_num,
)

from tonutils.types import ContractInfo, MasterchainInfo


class LiteMixin:
    """High-level lite-server operations mixin for ADNL clients."""

    async def _adnl_call(
        self,
        method: str,
        /,
        *args: t.Any,
        **kwargs: t.Any,
    ) -> t.Any:
        """Execute a provider call (overridden by subclasses).

        :param method: Provider method name.
        :param args: Positional arguments.
        :param kwargs: Keyword arguments.
        :return: Provider method result.
        """
        raise NotImplementedError("LiteMixin requires `_adnl_call()` implementation.")

    @staticmethod
    def _encode_stack(items: list[t.Any]) -> list[t.Any]:
        """Encode Python values to TVM stack items.

        :param items: Python values.
        :return: Encoded stack items.
        """
        out: list[t.Any] = []
        for item in items:
            if isinstance(item, int):
                out.append(item)
            elif isinstance(item, Address):
                out.append(item.to_cell().to_slice())
            elif isinstance(item, (Cell, Slice)):
                out.append(item)
            elif isinstance(item, list):
                out.append(LiteMixin._encode_stack(item))
        return out

    @staticmethod
    def _decode_stack(raw: list[t.Any]) -> list[t.Any]:
        """Decode TVM stack items to plain Python types.

        :param raw: Raw TVM stack items.
        :return: Decoded items.
        """
        out: list[t.Any] = []
        for item in raw:
            if item is None:
                out.append(None)
            elif isinstance(item, int):
                out.append(norm_stack_num(item))
            elif isinstance(item, Address):
                out.append(item.to_cell())
            elif isinstance(item, (Cell, Slice)):
                out.append(norm_stack_cell(item))
            elif isinstance(item, VmTuple):
                out.append(LiteMixin._decode_stack(item.list))
            elif isinstance(item, list):
                out.append(LiteMixin._decode_stack(item))
        return out

    async def _send_message(self, boc: str) -> None:
        """Send a serialized BoC message via the ADNL provider.

        :param boc: Hex-encoded BoC string.
        """
        method = "send_message"
        await self._adnl_call(method, bytes.fromhex(boc))

    async def _get_config(self) -> dict[int, t.Any]:
        """Fetch raw blockchain configuration via the lite-server.

        :return: Mapping of config parameter IDs to values.
        """
        method = "get_config"
        return t.cast("dict[int, t.Any]", await self._adnl_call(method))

    async def _get_info(self, address: str) -> ContractInfo:
        """Fetch contract state via the lite-server.

        :param address: Raw (non-user-friendly) address string.
        :return: ``ContractInfo`` snapshot.
        """
        method = "get_info"
        return t.cast(
            "ContractInfo",
            await self._adnl_call(method, Address(address)),
        )

    async def _run_get_method(
        self,
        address: str,
        method_name: str,
        stack: list[t.Any] | None = None,
    ) -> list[t.Any]:
        """Execute a contract get-method via the lite-server.

        :param address: Raw (non-user-friendly) address string.
        :param method_name: Name of the get-method.
        :param stack: TVM stack arguments, or ``None``.
        :return: Decoded TVM stack result.
        """
        method = "run_get_method"
        res = await self._adnl_call(
            method,
            address=Address(address),
            method_name=method_name,
            stack=self._encode_stack(stack or []),
        )
        return self._decode_stack(res or [])

    async def _get_transactions(
        self,
        address: str,
        limit: int = 100,
        from_lt: int | None = None,
        to_lt: int | None = None,
    ) -> list[Transaction]:
        """Fetch transaction history via the lite-server with pagination.

        :param address: Raw (non-user-friendly) address string.
        :param limit: Maximum number of transactions to return.
        :param from_lt: Upper-bound logical time (inclusive), or ``None``.
        :param to_lt: Lower-bound logical time (exclusive), or ``None``.
        :return: List of ``Transaction`` objects.
        """
        method = "get_transactions"

        to_lt_i = 0 if to_lt is None else to_lt
        state = await self._get_info(address)
        account = Address(address).to_tl_account_id()

        if state.last_transaction_lt is None or state.last_transaction_hash is None:
            return []

        curr_lt = state.last_transaction_lt
        curr_hash = state.last_transaction_hash
        out: list[Transaction] = []

        while curr_lt != 0:
            fetch_lt = curr_lt
            fetch_hash = curr_hash

            txs = t.cast(
                "list[Transaction]",
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
        """Fetch current network time from the lite-server.

        :return: Current UNIX timestamp.
        """
        method = "get_time"
        return t.cast("int", await self._adnl_call(method))

    async def get_version(self) -> int:
        """Fetch lite-server protocol version.

        :return: Version number.
        """
        method = "get_version"
        return t.cast("int", await self._adnl_call(method))

    async def get_masterchain_info(self) -> MasterchainInfo:
        """Fetch basic masterchain information.

        :return: ``MasterchainInfo`` instance.
        """
        method = "get_masterchain_info"
        return t.cast("MasterchainInfo", await self._adnl_call(method))

    async def wait_masterchain_seqno(
        self,
        seqno: int,
        timeout_ms: int,
        schema_name: str,
        data: dict[str, t.Any] | None = None,
    ) -> dict[str, t.Any]:
        """Combine waitMasterchainSeqno with another lite-server query.

        :param seqno: Masterchain seqno to wait for.
        :param timeout_ms: Wait timeout in milliseconds.
        :param schema_name: Method name without ``liteServer.`` prefix.
        :param data: Additional method arguments.
        :return: Decoded response dictionary.
        """
        method = "wait_masterchain_seqno"
        return t.cast(
            "dict[str, t.Any]",
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
        seqno: int | None = None,
        lt: int | None = None,
        utime: int | None = None,
    ) -> tuple[BlockIdExt, Block]:
        """Locate a block by workchain/shard and one of seqno, lt, or utime.

        :param workchain: Workchain identifier.
        :param shard: Shard identifier.
        :param seqno: Block sequence number.
        :param lt: Logical time filter.
        :param utime: UNIX time filter.
        :return: Tuple of ``BlockIdExt`` and deserialized ``Block``.
        """
        method = "lookup_block"
        return t.cast(
            "tuple[BlockIdExt, Block]",
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
    ) -> tuple[BlockIdExt, Block]:
        """Fetch and deserialize a block header.

        :param block: Block identifier to query.
        :return: Tuple of ``BlockIdExt`` and deserialized ``Block``.
        """
        method = "get_block_header"
        return t.cast(
            "tuple[BlockIdExt, Block]",
            await self._adnl_call(method, block),
        )

    async def get_block_transactions(
        self,
        block: BlockIdExt,
        count: int = 1024,
    ) -> list[Transaction]:
        """Fetch all transactions in a block.

        :param block: Target block identifier.
        :param count: Maximum transactions per request page.
        :return: List of deserialized ``Transaction`` objects.
        """
        method = "get_block_transactions"
        return t.cast(
            "list[Transaction]",
            await self._adnl_call(method, block, count=count),
        )

    async def get_all_shards_info(
        self,
        block: BlockIdExt | None = None,
    ) -> list[BlockIdExt]:
        """Fetch shard info for all workchains at a masterchain block.

        :param block: Masterchain block ID, or ``None`` for latest.
        :return: List of shard ``BlockIdExt`` objects.
        """
        method = "get_all_shards_info"
        return t.cast(
            "list[BlockIdExt]",
            await self._adnl_call(method, block),
        )

    async def get_account_state(
        self,
        address: AddressLike,
    ) -> tuple[Account | None, ShardAccount | None]:
        """Fetch account state and shard account from the lite-server.

        :param address: Contract address.
        :return: Tuple of (``Account`` or ``None``, ``ShardAccount`` or ``None``).
        """
        if isinstance(address, str):
            address = Address(address)

        method = "get_account_state"
        return t.cast(
            "tuple[Account | None, ShardAccount | None]",
            await self._adnl_call(method, address),
        )
