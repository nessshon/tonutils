from __future__ import annotations

import asyncio

from tonutils.exceptions import (
    BalancerError,
    ClientError,
    ContractError,
    DhtValueNotFoundError,
    NetworkNotSupportedError,
    NotConnectedError,
    ProviderError,
    ProviderResponseError,
    ProviderTimeoutError,
    RetryLimitError,
    RunGetMethodError,
    StateNotLoadedError,
    TonutilsError,
    TransportError,
)


class TestHintMechanism:
    def test_with_hint(self):
        err = TonutilsError("broke", hint="fix it")
        assert "broke" in str(err)
        assert "Hint: fix it" in str(err)

    def test_without_hint(self):
        err = TonutilsError("broke")
        assert str(err) == "broke"
        assert "Hint" not in str(err)


class TestStructuredFields:
    def test_transport_error(self):
        err = TransportError(endpoint="1.2.3.4:1234", operation="handshake", reason="timeout")
        assert err.endpoint == "1.2.3.4:1234"
        assert err.operation == "handshake"
        assert err.reason == "timeout"

    def test_provider_response_error(self):
        err = ProviderResponseError(code=429, message="rate limit", endpoint="https://api.example.com")
        assert err.code == 429
        assert err.message == "rate limit"
        assert err.endpoint == "https://api.example.com"

    def test_provider_timeout_error(self):
        err = ProviderTimeoutError(timeout=5.0, endpoint="x", operation="request")
        assert err.timeout == 5.0

    def test_retry_limit_error(self):
        cause = ProviderResponseError(code=503, message="unavailable", endpoint="x")
        err = RetryLimitError(attempts=3, max_attempts=3, last_error=cause)
        assert err.last_error is cause
        assert err.attempts == 3
        assert "3/3" in str(err)

    def test_run_get_method_error(self):
        err = RunGetMethodError(address="0:abc", exit_code=11, method_name="seqno")
        assert err.exit_code == 11
        assert err.method_name == "seqno"
        assert "Hint" in str(err)

    def test_not_connected_error(self):
        err = NotConnectedError(component="HttpTransport", endpoint="x", operation="send")
        assert err.component == "HttpTransport"
        assert "Hint" in str(err)


class TestInheritance:
    def test_transport_is_base(self):
        assert isinstance(TransportError(endpoint="x", operation="y", reason="z"), TonutilsError)

    def test_provider_timeout_is_asyncio_timeout(self):
        assert isinstance(ProviderTimeoutError(timeout=1, endpoint="x", operation="y"), asyncio.TimeoutError)

    def test_provider_timeout_is_provider_error(self):
        assert isinstance(ProviderTimeoutError(timeout=1, endpoint="x", operation="y"), ProviderError)

    def test_not_connected_is_runtime_error(self):
        assert isinstance(NotConnectedError(), RuntimeError)

    def test_network_not_supported_is_key_error(self):
        assert isinstance(NetworkNotSupportedError("x", provider="y"), KeyError)

    def test_network_not_supported_is_client_error(self):
        assert isinstance(NetworkNotSupportedError("x", provider="y"), ClientError)

    def test_state_not_loaded_chain(self):
        class Fake:
            pass

        err = StateNotLoadedError(Fake(), missing="code")
        assert isinstance(err, ContractError)
        assert isinstance(err, ClientError)
        assert isinstance(err, TonutilsError)

    def test_dht_is_client_error(self):
        assert isinstance(DhtValueNotFoundError(key=b"\x00" * 32), ClientError)

    def test_balancer_is_base(self):
        assert isinstance(BalancerError("no backends"), TonutilsError)

    def test_retry_limit_is_provider_error(self):
        cause = ProviderResponseError(code=500, message="x", endpoint="y")
        assert isinstance(RetryLimitError(attempts=1, max_attempts=1, last_error=cause), ProviderError)
