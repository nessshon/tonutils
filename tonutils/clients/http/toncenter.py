from __future__ import annotations

import base64
import typing as t

from ton_core import (
    Address,
    Cell,
    ContractState,
    NetworkGlobalID,
    Slice,
    Transaction,
    cell_to_b64,
    cell_to_hex,
    norm_stack_cell,
    norm_stack_num,
    parse_stack_config,
)

from tonutils.clients.base import BaseClient
from tonutils.exceptions import ClientError, RunGetMethodError
from tonutils.providers.http.toncenter import ToncenterHttpProvider
from tonutils.providers.http.toncenter.models import (
    RunGetMethodPayload,
    SendBocPayload,
)
from tonutils.types import (
    ClientType,
    ContractInfo,
    RetryPolicy,
)

if t.TYPE_CHECKING:
    from aiohttp import ClientSession


class ToncenterClient(BaseClient):
    """TON blockchain client using Toncenter v2 REST API.

    For multi-provider balancing with automatic failover, use ``HttpBalancer``.
    """

    TYPE = ClientType.HTTP

    def __init__(
        self,
        network: NetworkGlobalID,
        *,
        api_key: str | None = None,
        base_url: str | None = None,
        timeout: float = 10.0,
        session: ClientSession | None = None,
        headers: dict[str, str] | None = None,
        cookies: dict[str, str] | None = None,
        rps_limit: int | None = None,
        rps_period: float = 1.0,
        retry_policy: RetryPolicy | None = None,
    ) -> None:
        """Initialize the Toncenter client.

        :param network: Target TON network.
        :param api_key: Toncenter API key, or ``None``.
            You can get an API key on the Toncenter telegram bot: https://t.me/toncenter.
        :param base_url: Custom endpoint base URL, or ``None``.
        :param timeout: Request timeout in seconds.
        :param session: External aiohttp session, or ``None``.
        :param headers: Default headers for owned session.
        :param cookies: Default cookies for owned session.
        :param rps_limit: Requests-per-period limit, or ``None``.
        :param rps_period: Rate limit period in seconds.
        :param retry_policy: Retry policy with per-error-code rules, or ``None``.
        """
        self.network: NetworkGlobalID = network
        self._provider: ToncenterHttpProvider = ToncenterHttpProvider(
            api_key=api_key,
            network=network,
            base_url=base_url,
            timeout=timeout,
            session=session,
            headers=headers,
            cookies=cookies,
            rps_limit=rps_limit,
            rps_period=rps_period,
            retry_policy=retry_policy,
        )

    @property
    def connected(self) -> bool:
        """``True`` if the HTTP session is open."""
        session = self._provider.session
        return session is not None and not session.closed

    @property
    def provider(self) -> ToncenterHttpProvider:
        """Underlying Toncenter HTTP provider."""
        return self._provider

    async def connect(self) -> None:
        """Open the HTTP session."""
        await self._provider.connect()

    async def close(self) -> None:
        """Close the HTTP session."""
        await self._provider.close()

    async def _send_message(self, boc: str) -> None:
        """Send a serialized BoC message via the Toncenter REST API.

        :param boc: Hex-encoded BoC string.
        """
        payload = SendBocPayload(boc=boc)
        return await self.provider.send_boc(payload=payload)

    async def _get_config(self) -> dict[int, t.Any]:
        """Fetch raw blockchain configuration via the Toncenter REST API.

        :return: Mapping of config parameter IDs to values.
        :raises ClientError: If the response is missing required fields.
        """
        request = await self.provider.get_config_all()

        if request.result is None:
            raise ClientError("Invalid get_config response: missing `result`.")

        if request.result.config is None:
            raise ClientError("Invalid config response: missing `config` in `result`.")

        if request.result.config.bytes is None:
            raise ClientError("Invalid config response: missing `config.bytes`.")

        config_cell = Cell.one_from_boc(request.result.config.bytes)
        config_slice = config_cell.begin_parse()
        return parse_stack_config(config_slice)

    async def _get_info(self, address: str) -> ContractInfo:
        """Fetch contract state via the Toncenter REST API.

        :param address: Raw (non-user-friendly) address string.
        :return: ``ContractInfo`` snapshot.
        """
        request = await self.provider.get_address_information(address)

        contract_info = ContractInfo(
            balance=int(request.result.balance),
            state=ContractState(request.result.state),
        )
        if request.result.code:
            contract_info.code_raw = cell_to_hex(request.result.code)

        if request.result.data:
            contract_info.data_raw = cell_to_hex(request.result.data)

        last_transaction_lt = last_transaction_hash = None

        tx_id = request.result.last_transaction_id
        if tx_id is not None:
            try:
                lt = int(tx_id.lt) if tx_id.lt is not None else 0
            except ValueError:
                pass
            else:
                if lt > 0:
                    last_transaction_lt = lt

            raw = tx_id.hash
            if raw is not None:
                try:
                    h = base64.b64decode(raw).hex()
                except Exception:
                    pass
                else:
                    if h != "00" * 32:
                        last_transaction_hash = h

        contract_info.last_transaction_lt = last_transaction_lt
        contract_info.last_transaction_hash = last_transaction_hash

        if (
            last_transaction_lt is None
            and last_transaction_hash is None
            and contract_info.state == ContractState.UNINIT
        ):
            contract_info.state = ContractState.NONEXIST

        return contract_info

    async def _get_transactions(
        self,
        address: str,
        limit: int = 100,
        from_lt: int | None = None,
        to_lt: int | None = None,
    ) -> list[Transaction]:
        """Fetch transaction history via the Toncenter REST API with pagination.

        :param address: Raw (non-user-friendly) address string.
        :param limit: Maximum number of transactions to return.
        :param from_lt: Upper-bound logical time (inclusive), or ``None``.
        :param to_lt: Lower-bound logical time (exclusive), or ``None``.
        :return: List of deserialized ``Transaction`` objects.
        """
        to_lt = 0 if to_lt is None else to_lt
        transactions: list[Transaction] = []

        curr_lt: int | None = None
        curr_hash: str | None = None

        while len(transactions) < limit:
            request = await self.provider.get_transactions(
                address=address,
                limit=100,
                lt=curr_lt,
                from_hash=curr_hash,
                to_lt=to_lt if to_lt > 0 else None,
            )

            batch: list[Transaction] = []
            for tx_entry in request.result or []:
                if tx_entry.data is not None:
                    tx_slice = Slice.one_from_boc(tx_entry.data)
                    parsed = Transaction.deserialize(tx_slice)
                    if isinstance(parsed, Transaction):
                        batch.append(parsed)

            if not batch:
                break

            for tx in batch:
                if from_lt is not None and tx.lt > from_lt:
                    continue

                if to_lt > 0 and tx.lt <= to_lt:
                    return transactions[:limit]

                transactions.append(tx)

                if len(transactions) >= limit:
                    return transactions

            last_tx = batch[-1]
            if last_tx.prev_trans_lt == 0:
                break

            curr_lt = last_tx.prev_trans_lt
            curr_hash = last_tx.prev_trans_hash.hex()

        return transactions

    async def _run_get_method(
        self,
        address: str,
        method_name: str,
        stack: list[t.Any] | None = None,
    ) -> list[t.Any]:
        """Execute a contract get-method via the Toncenter REST API.

        :param address: Raw (non-user-friendly) address string.
        :param method_name: Name of the get-method.
        :param stack: TVM stack arguments, or ``None``.
        :return: Decoded TVM stack result.
        :raises RunGetMethodError: If the method exits with a non-zero code.
        """
        payload = RunGetMethodPayload(
            address=address,
            method=method_name,
            stack=self._encode_stack(stack or []),
        )
        request = await self.provider.run_get_method(payload=payload)
        if request.result is None:
            return []

        if request.result.exit_code != 0:
            raise RunGetMethodError(
                address=address,
                method_name=method_name,
                exit_code=request.result.exit_code,
            )

        return self._decode_stack(request.result.stack or [])

    @staticmethod
    def _encode_stack(items: list[t.Any]) -> list[t.Any]:
        """Encode Python values to Toncenter stack format.

        :param items: Python stack values.
        :return: Encoded ``[tag, payload]`` pairs.
        """
        out: list[t.Any] = []

        for item in items:
            if isinstance(item, int):
                out.append(["num", str(item)])
            elif isinstance(item, Address):
                out.append(["tvm.Slice", cell_to_b64(item.to_cell())])
            elif isinstance(item, Cell):
                out.append(["tvm.Cell", cell_to_b64(item)])
            elif isinstance(item, Slice):
                out.append(["tvm.Slice", cell_to_b64(item.to_cell())])
            elif isinstance(item, list):
                out.append(["tuple", {"elements": ToncenterClient._encode_stack(item)}])

        return out

    @staticmethod
    def _decode_stack(raw: list[t.Any]) -> list[t.Any]:
        """Decode Toncenter ``[tag, payload]`` stack pairs.

        :param raw: Raw stack items from the API.
        :return: Decoded Python values.
        """
        out: list[t.Any] = []

        for item in raw:
            if not (isinstance(item, list) and len(item) == 2):
                continue

            tag, payload = item[0], item[1]

            if tag == "null":
                out.append(None)
            elif tag == "num":
                out.append(norm_stack_num(payload))
            elif tag in ("cell", "tvm.Cell", "slice", "tvm.Slice"):
                val = (payload or {}).get("bytes")
                out.append(norm_stack_cell(val) if isinstance(val, (Cell, Slice, str)) else None)
            elif tag in ("tuple", "list"):
                elements = (payload or {}).get("elements") or []
                out.append([ToncenterClient._decode_entry(el) for el in elements])

        return out

    @staticmethod
    def _decode_entry(entry: dict[str, t.Any]) -> t.Any:
        """Decode a single ``@type``-based nested entry.

        :param entry: Raw dict with ``@type`` key.
        :return: Decoded Python value.
        """
        atype = entry.get("@type", "")

        if atype == "tvm.stackEntryNumber":
            return norm_stack_num((entry.get("number") or {}).get("number"))  # type: ignore[arg-type]

        if atype in ("tvm.stackEntryCell", "tvm.stackEntryBuilder"):
            key = "cell" if atype == "tvm.stackEntryCell" else "builder"
            val = (entry.get(key) or {}).get("bytes")
            return norm_stack_cell(val) if isinstance(val, (Cell, Slice, str)) else None

        if atype == "tvm.stackEntrySlice":
            val = (entry.get("slice") or {}).get("bytes")
            return norm_stack_cell(val) if isinstance(val, (Cell, Slice, str)) else None

        if atype in ("tvm.stackEntryTuple", "tvm.stackEntryList"):
            key = "tuple" if atype == "tvm.stackEntryTuple" else "list"
            elements = (entry.get(key) or {}).get("elements") or []
            return [ToncenterClient._decode_entry(el) for el in elements]

        return None
