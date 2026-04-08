from __future__ import annotations

from ton_core import NetworkGlobalID

from tonutils.clients import TonapiClient, ToncenterClient
from tonutils.types import (
    DEFAULT_ADNL_RETRY_POLICY,
    DEFAULT_HTTP_RETRY_POLICY,
    LITESERVER_RATE_LIMIT_CODES,
    RetryPolicy,
    RetryRule,
)


class TestTonapiKeylessRateLimit:
    def test_applies_defaults_without_key(self):
        client = TonapiClient(NetworkGlobalID.MAINNET)
        assert client.provider.limiter is not None
        assert client.provider.limiter._max_rate >= 1
        assert client.provider.limiter._period > 0

    def test_no_limiter_with_key(self):
        client = TonapiClient(NetworkGlobalID.MAINNET, api_key="key")
        assert client.provider.limiter is None

    def test_explicit_rps_overrides_default(self):
        client = TonapiClient(NetworkGlobalID.MAINNET, rps_limit=10, rps_period=2.0)
        assert client.provider.limiter is not None
        assert client.provider.limiter._max_rate == 10
        assert client.provider.limiter._period == 2.0


class TestToncenterKeylessRateLimit:
    def test_applies_defaults_without_key(self):
        client = ToncenterClient(NetworkGlobalID.MAINNET)
        assert client.provider.limiter is not None
        assert client.provider.limiter._max_rate >= 1
        assert client.provider.limiter._period > 0

    def test_no_limiter_with_key(self):
        client = ToncenterClient(NetworkGlobalID.MAINNET, api_key="key")
        assert client.provider.limiter is None

    def test_explicit_rps_overrides_default(self):
        client = ToncenterClient(NetworkGlobalID.MAINNET, rps_limit=10, rps_period=2.0)
        assert client.provider.limiter is not None
        assert client.provider.limiter._max_rate == 10
        assert client.provider.limiter._period == 2.0


class TestRetryRuleMatching:
    def test_matches_by_code(self):
        rule = RetryRule(codes=frozenset({429}))
        assert rule.matches(429, "") is True
        assert rule.matches(500, "") is False

    def test_matches_by_marker_case_insensitive(self):
        rule = RetryRule(markers=("cloudflare",))
        assert rule.matches(0, "Blocked by CLOUDFLARE") is True
        assert rule.matches(0, "normal response") is False

    def test_requires_both_when_code_and_marker_set(self):
        rule = RetryRule(codes=frozenset({503}), markers=("cloudflare",))
        assert rule.matches(503, "cloudflare error") is True
        assert rule.matches(503, "normal error") is False
        assert rule.matches(429, "cloudflare error") is False


class TestRetryRuleDelay:
    def test_exponential_backoff(self):
        rule = RetryRule(base_delay=1.0, backoff_factor=2.0, max_delay=100.0)
        assert rule.delay_for_attempt(0) == 1.0
        assert rule.delay_for_attempt(1) == 2.0
        assert rule.delay_for_attempt(2) == 4.0

    def test_capped_at_max_delay(self):
        rule = RetryRule(base_delay=1.0, backoff_factor=2.0, max_delay=3.0)
        assert rule.delay_for_attempt(10) == 3.0


class TestDefaultRetryPolicies:
    def test_http_handles_rate_limit(self):
        assert DEFAULT_HTTP_RETRY_POLICY.rule_for(429, "") is not None

    def test_http_handles_transient(self):
        assert DEFAULT_HTTP_RETRY_POLICY.rule_for(502, "") is not None

    def test_http_handles_cdn_challenge(self):
        assert DEFAULT_HTTP_RETRY_POLICY.rule_for(0, "blocked by cloudflare") is not None

    def test_adnl_handles_liteserver_rate_limit(self):
        for code in LITESERVER_RATE_LIMIT_CODES:
            assert DEFAULT_ADNL_RETRY_POLICY.rule_for(code, "") is not None

    def test_first_match_wins(self):
        rule_a = RetryRule(codes=frozenset({429}), base_delay=1.0)
        rule_b = RetryRule(codes=frozenset({429}), base_delay=5.0, max_delay=10.0)
        policy = RetryPolicy(rules=(rule_a, rule_b))
        assert policy.rule_for(429, "") is rule_a
