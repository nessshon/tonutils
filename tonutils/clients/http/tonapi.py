from __future__ import annotations

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
from tonutils.exceptions import ClientError, ProviderResponseError, RunGetMethodError
from tonutils.providers.http.tonapi import TonapiHttpProvider
from tonutils.providers.http.tonapi.models import BlockchainMessagePayload
from tonutils.types import (
    DEFAULT_REQUEST_TIMEOUT,
    ClientType,
    ContractInfo,
    RetryPolicy,
)

if t.TYPE_CHECKING:
    from aiohttp import ClientSession

_DEFAULT_RPS_LIMIT = 1
_DEFAULT_RPS_PERIOD = 4.0


class TonapiClient(BaseClient):
    """TON blockchain client using Tonapi REST API.

    For multi-provider balancing with automatic failover, use ``HttpBalancer``.
    """

    TYPE = ClientType.HTTP

    def __init__(
        self,
        network: NetworkGlobalID,
        *,
        api_key: str | None = None,
        base_url: str | None = None,
        timeout: float = DEFAULT_REQUEST_TIMEOUT,
        session: ClientSession | None = None,
        headers: dict[str, str] | None = None,
        cookies: dict[str, str] | None = None,
        rps_limit: int | None = None,
        rps_period: float | None = None,
        retry_policy: RetryPolicy | None = None,
    ) -> None:
        """Initialize the Tonapi client.

        :param network: Target TON network.
        :param api_key: API key, or ``None`` for keyless access with default rate limits.
            You can get an API key on the Tonconsole website: https://tonconsole.com/.
        :param base_url: Custom endpoint base URL, or ``None``.
        :param timeout: Request timeout in seconds.
        :param session: External aiohttp session, or ``None``.
        :param headers: Extra headers merged into every request.
        :param cookies: Extra cookies merged into every request.
        :param rps_limit: Requests-per-period cap, or ``None`` for automatic defaults.
        :param rps_period: Rate-limit window in seconds, or ``None`` for automatic defaults.
        :param retry_policy: Retry policy with per-status rules, or ``None``.
        """
        if not api_key and rps_limit is None:
            rps_limit = _DEFAULT_RPS_LIMIT
            rps_period = rps_period or _DEFAULT_RPS_PERIOD

        self.network: NetworkGlobalID = network
        self._provider: TonapiHttpProvider = TonapiHttpProvider(
            api_key=api_key,
            network=network,
            base_url=base_url,
            timeout=timeout,
            session=session,
            headers=headers,
            cookies=cookies,
            rps_limit=rps_limit,
            rps_period=rps_period or 1.0,
            retry_policy=retry_policy,
        )

    @property
    def connected(self) -> bool:
        """``True`` if the HTTP session is open."""
        session = self._provider.session
        return session is not None and not session.closed

    @property
    def provider(self) -> TonapiHttpProvider:
        """Underlying Tonapi HTTP provider."""
        return self._provider

    async def connect(self) -> None:
        """Open the HTTP session."""
        await self._provider.connect()

    async def close(self) -> None:
        """Close the HTTP session."""
        await self._provider.close()

    async def _send_message(self, boc: str) -> None:
        """Send a serialized BoC message via the Tonapi REST API.

        :param boc: Hex-encoded BoC string.
        """
        payload = BlockchainMessagePayload(boc=boc)
        return await self.provider.blockchain_message(payload=payload)

    async def _get_config(self) -> dict[int, t.Any]:
        """Fetch raw blockchain configuration via the Tonapi REST API.

        :return: Mapping of config parameter IDs to values.
        :raises ClientError: If the response is missing the ``raw`` field.
        """
        result = await self.provider.blockchain_config()

        if result.raw is None:
            raise ClientError("Invalid config response: missing `raw` field.")

        config_cell = Cell.one_from_boc(result.raw)[0]
        config_slice = config_cell.begin_parse()
        return parse_stack_config(config_slice)

    async def _get_info(self, address: str) -> ContractInfo:
        """Fetch contract state via the Tonapi REST API.

        :param address: Raw (non-user-friendly) address string.
        :return: ``ContractInfo`` snapshot.
        """
        try:
            result = await self.provider.blockchain_account(address)
        except ProviderResponseError as e:
            if e.code == 404:
                return ContractInfo(state=ContractState.NONEXIST)
            raise

        contract_info = ContractInfo(
            balance=result.balance,
            state=ContractState(result.status),
            last_transaction_lt=result.last_transaction_lt,
            last_transaction_hash=result.last_transaction_hash,
        )
        if result.code is not None:
            contract_info.code_raw = cell_to_hex(result.code)
        if result.data is not None:
            contract_info.data_raw = cell_to_hex(result.data)

        return contract_info

    async def _get_transactions(
        self,
        address: str,
        limit: int = 100,
        from_lt: int | None = None,
        to_lt: int | None = None,
    ) -> list[Transaction]:
        """Fetch transaction history via the Tonapi REST API.

        :param address: Raw (non-user-friendly) address string.
        :param limit: Maximum number of transactions to return.
        :param from_lt: Upper-bound logical time (inclusive), or ``None``.
        :param to_lt: Lower-bound logical time (exclusive), or ``None``.
        :return: List of deserialized ``Transaction`` objects.
        """
        before_lt = from_lt + 1 if from_lt is not None else None

        result = await self.provider.blockchain_account_transactions(
            address=address,
            limit=limit,
            after_lt=to_lt,
            before_lt=before_lt,
        )

        transactions: list[Transaction] = []
        for tx in result.transactions or []:
            if tx.raw is not None:
                tx_slice = Slice.one_from_boc(tx.raw)
                parsed = Transaction.deserialize(tx_slice)
                if isinstance(parsed, Transaction):
                    transactions.append(parsed)

        return transactions

    async def _run_get_method(
        self,
        address: str,
        method_name: str,
        stack: list[t.Any] | None = None,
    ) -> list[t.Any]:
        """Execute a contract get-method via the Tonapi REST API.

        :param address: Raw (non-user-friendly) address string.
        :param method_name: Name of the get-method.
        :param stack: TVM stack arguments, or ``None``.
        :return: Decoded TVM stack result.
        :raises RunGetMethodError: If the method exits with a non-zero code.
        """
        result = await self.provider.blockchain_account_method(
            address=address,
            method_name=method_name,
            args=self._encode_stack(stack or []),
        )
        if result.exit_code != 0:
            raise RunGetMethodError(
                address=address,
                method_name=method_name,
                exit_code=result.exit_code,
            )

        return self._decode_stack(result.stack or [])

    @staticmethod
    def _encode_stack(items: list[t.Any]) -> list[dict[str, str]]:
        """Encode Python values to typed Tonapi stack records.

        :param items: Python stack values.
        :return: List of ``{"type": ..., "value": ...}`` dicts.
        """
        out: list[dict[str, str]] = []

        for item in items:
            if item is None:
                out.append({"type": "null", "value": ""})
            elif isinstance(item, int):
                out.append({"type": "int257", "value": hex(item)})
            elif isinstance(item, Address):
                out.append({"type": "slice", "value": item.to_str(is_user_friendly=False)})
            elif isinstance(item, Cell):
                out.append({"type": "cell_boc_base64", "value": cell_to_b64(item)})
            elif isinstance(item, Slice):
                out.append({"type": "slice_boc_hex", "value": cell_to_hex(item.to_cell())})

        return out

    @staticmethod
    def _decode_stack(raw: list[t.Any]) -> list[t.Any]:
        """Decode Tonapi ``{"type": ..., <type>: <value>}`` stack dicts.

        :param raw: Raw stack items from the API.
        :return: Decoded Python values.
        """
        out: list[t.Any] = []

        for item in raw:
            if not isinstance(item, dict):
                continue

            tpe = item.get("type", "")

            if tpe in ("null", "nan"):
                out.append(None)
            elif tpe == "num":
                out.append(norm_stack_num(item.get("num")))  # type: ignore[arg-type]
            elif tpe == "cell":
                val = item.get("cell")
                out.append(norm_stack_cell(val) if isinstance(val, (Cell, Slice, str)) else None)
            elif tpe == "slice":
                val = item.get("slice")
                out.append(norm_stack_cell(val) if isinstance(val, (Cell, Slice, str)) else None)
            elif tpe in ("tuple", "list"):
                out.append(TonapiClient._decode_stack(item.get(tpe) or []))

        return out
