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
        out: t.Optional[t.List[BlockIdExt]] = None,
    ) -> t.List[BlockIdExt]:
        """Recursively walk from root block back to seen blocks."""
        if out is None:
            out = []

        key = self.shard_key(root)
        if seen_seqno.get(key, -1) >= root.seqno:
            return out

        _, header = await get_header(root)
        prev_ref = header.info.prev_ref

        if prev_ref.type_ == "prev_blk_info":
            prev: ExtBlkRef = prev_ref.prev
            prev_shard = (
                self.get_parent_shard(root.shard)
                if header.info.after_split
                else root.shard
            )
            await self.walk_unseen(
                root=BlockIdExt(
                    workchain=root.workchain,
                    shard=prev_shard,
                    seqno=prev.seqno,
                    root_hash=prev.root_hash,
                    file_hash=prev.file_hash,
                ),
                seen_seqno=seen_seqno,
                get_header=get_header,
                out=out,
            )
        else:
            prev1, prev2 = prev_ref.prev1, prev_ref.prev2
            await self.walk_unseen(
                root=BlockIdExt(
                    workchain=root.workchain,
                    shard=self.get_child_shard(root.shard, left=True),
                    seqno=prev1.seqno,
                    root_hash=prev1.root_hash,
                    file_hash=prev1.file_hash,
                ),
                seen_seqno=seen_seqno,
                get_header=get_header,
                out=out,
            )
            await self.walk_unseen(
                root=BlockIdExt(
                    workchain=root.workchain,
                    shard=self.get_child_shard(root.shard, left=False),
                    seqno=prev2.seqno,
                    root_hash=prev2.root_hash,
                    file_hash=prev2.file_hash,
                ),
                seen_seqno=seen_seqno,
                get_header=get_header,
                out=out,
            )

        out.append(root)
        return out
