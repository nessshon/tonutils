import typing as t
from unittest.async_case import IsolatedAsyncioTestCase

from tonutils.clients import (
    LiteserverClient,
    TonapiClient,
    ToncenterClient,
)
from tonutils.protocols import ClientProtocol
from tonutils.types import ClientType

TONAPI_KEY = "AGKFC6FF236MSRIAAAABMC6G6N4PPOQB7Q2ZZV3P6ARMPJ3XPS3NX7E2QJLWQMYSIFPYJGY"


class AsyncTestCase(IsolatedAsyncioTestCase): ...


class ClientTestCase(AsyncTestCase):
    CLIENT_TYPE: t.ClassVar[ClientType]
    IS_TESTNET: t.ClassVar[bool]
    RPS: t.ClassVar[int]

    async def asyncSetUp(self) -> None:
        client: ClientProtocol
        match self.CLIENT_TYPE:
            case ClientType.TONAPI:
                client = TonapiClient(
                    api_key=TONAPI_KEY,
                    is_testnet=self.IS_TESTNET,
                    rps=self.RPS,
                )
            case ClientType.TONCENTER:
                client = ToncenterClient(
                    is_testnet=self.IS_TESTNET,
                    rps=self.RPS,
                )
            case ClientType.LITESERVER | _:
                client = LiteserverClient(
                    is_testnet=self.IS_TESTNET,
                )

        self.client = client
        await self.client.startup()

    async def asyncTearDown(self) -> None:
        await self.client.close()
