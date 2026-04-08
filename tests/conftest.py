from __future__ import annotations

import typing as t

import pytest
import pytest_asyncio
from environs import Env

from tests.constants import LITE_INDEX, NETWORK
from tonutils.clients import HttpBalancer, LiteBalancer, LiteClient, TonapiClient, ToncenterClient
from tonutils.types import DEFAULT_ADNL_RETRY_POLICY, DEFAULT_HTTP_RETRY_POLICY

if t.TYPE_CHECKING:
    from collections.abc import AsyncIterator

    from tonutils.clients.base import BaseClient

env = Env()
env.read_env()

RPS_LIMIT = 10


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def tonapi_client() -> AsyncIterator[BaseClient]:
    async with TonapiClient(
        NETWORK,
        api_key=env.str("TONAPI_KEY"),
        rps_limit=RPS_LIMIT,
        retry_policy=DEFAULT_HTTP_RETRY_POLICY,
    ) as client:
        yield client


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def toncenter_client() -> AsyncIterator[BaseClient]:
    async with ToncenterClient(
        NETWORK,
        api_key=env.str("TONCENTER_KEY"),
        rps_limit=RPS_LIMIT,
        retry_policy=DEFAULT_HTTP_RETRY_POLICY,
    ) as client:
        yield client


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def lite_client() -> AsyncIterator[BaseClient]:
    async with LiteClient.from_network_config(
        NETWORK,
        index=LITE_INDEX,
        rps_limit=RPS_LIMIT,
        retry_policy=DEFAULT_ADNL_RETRY_POLICY,
    ) as client:
        yield client


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def http_balancer(tonapi_client: BaseClient, toncenter_client: BaseClient) -> AsyncIterator[BaseClient]:
    async with HttpBalancer(NETWORK, clients=[tonapi_client, toncenter_client]) as balancer:
        yield balancer


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def lite_balancer() -> AsyncIterator[BaseClient]:
    async with LiteBalancer.from_network_config(
        NETWORK,
        rps_limit=RPS_LIMIT,
        retry_policy=DEFAULT_ADNL_RETRY_POLICY,
    ) as client:
        yield client


@pytest.fixture(
    scope="session",
    params=["tonapi", "toncenter", "lite", "http_balancer", "lite_balancer"],
)
def client(
    request: pytest.FixtureRequest,
    tonapi_client: BaseClient,
    toncenter_client: BaseClient,
    lite_client: BaseClient,
    http_balancer: BaseClient,
    lite_balancer: BaseClient,
) -> BaseClient:
    return {
        "tonapi": tonapi_client,
        "toncenter": toncenter_client,
        "lite": lite_client,
        "http_balancer": http_balancer,
        "lite_balancer": lite_balancer,
    }[request.param]
