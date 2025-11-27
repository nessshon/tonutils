from __future__ import annotations

from tonutils.clients.adnl.provider.workers.base import BaseWorker
from tonutils.exceptions import AdnlServerError


class ReaderWorker(BaseWorker):

    def _handle_message(self, root: dict) -> None:
        query_id = root.get("query_id")
        random_id = root.get("random_id")

        if query_id is not None:
            message_id = query_id
        elif random_id is not None:
            message_id = str(random_id)
        else:
            return

        fut = self.provider.pending.pop(message_id, None)
        if fut is None or fut.done():
            return

        payload = root.get("answer", root)

        if "code" in payload and "message" in payload:
            exception = AdnlServerError(
                code=payload["code"],
                message=payload["message"],
            )
            fut.set_exception(exception)
        else:
            fut.set_result(payload)

    async def _run(self) -> None:
        provider = self.provider

        while self.running:
            frame = await self.provider.transport.recv_adnl_packet()
            if len(frame) < 32:
                continue
            try:
                root = provider.tl_schemas.deserialize(frame[32:], boxed=True)
            except (Exception,):
                continue
            self._handle_message(root[0])
