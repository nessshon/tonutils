import typing as t

from pytoniq_core.tl import BlockIdExt
from pytoniq_core.tlb.block import ExtBlkRef


class ShardTraversal:

    @staticmethod
    def shard_key(blk: BlockIdExt) -> t.Tuple[int, int]:
        return blk.workchain, blk.shard

    @staticmethod
    def simulate_overflow(x: int) -> int:
        return (x + 2**63) % 2**64 - 2**63

    @staticmethod
    def lower_bit64(num: int) -> int:
        return num & (~num + 1)

    def get_child_shard(self, shard: int, *, left: bool) -> int:
        x = self.lower_bit64(shard) >> 1
        if left:
            return self.simulate_overflow(shard - x)
        return self.simulate_overflow(shard + x)

    def get_parent_shard(self, shard: int) -> int:
        x = self.lower_bit64(shard)
        return self.simulate_overflow((shard - x) | (x << 1))

    async def walk_unseen(
        self,
        *,
        root: BlockIdExt,
        seen_seqno: t.Dict[t.Tuple[int, int], int],
        get_header: t.Callable[[BlockIdExt], t.Awaitable[t.Any]],
    ) -> t.List[BlockIdExt]:
        out: t.List[BlockIdExt] = []
        stack: t.List[BlockIdExt] = [root]
        post: t.List[BlockIdExt] = []

        while stack:
            blk = stack.pop()
            key = self.shard_key(blk)
            if seen_seqno.get(key, -1) >= blk.seqno:
                continue

            post.append(blk)
            _, header = await get_header(blk)
            prev_ref = header.info.prev_ref

            if prev_ref.type_ == "prev_blk_info":
                prev: ExtBlkRef = prev_ref.prev
                prev_shard = (
                    self.get_parent_shard(blk.shard)
                    if header.info.after_split
                    else blk.shard
                )
                stack.append(
                    BlockIdExt(
                        workchain=blk.workchain,
                        shard=prev_shard,
                        seqno=prev.seqno,
                        root_hash=prev.root_hash,
                        file_hash=prev.file_hash,
                    )
                )

            else:
                prev1, prev2 = prev_ref.prev1, prev_ref.prev2
                stack.append(
                    BlockIdExt(
                        workchain=blk.workchain,
                        shard=self.get_child_shard(blk.shard, left=True),
                        seqno=prev1.seqno,
                        root_hash=prev1.root_hash,
                        file_hash=prev1.file_hash,
                    )
                )
                stack.append(
                    BlockIdExt(
                        workchain=blk.workchain,
                        shard=self.get_child_shard(blk.shard, left=False),
                        seqno=prev2.seqno,
                        root_hash=prev2.root_hash,
                        file_hash=prev2.file_hash,
                    )
                )

        for blk in reversed(post):
            key = self.shard_key(blk)
            if seen_seqno.get(key, -1) >= blk.seqno:
                continue
            out.append(blk)

        return out
