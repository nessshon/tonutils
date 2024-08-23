from __future__ import annotations

from pytoniq_core import Cell, Address

from ..base.nft import NFT
from ...data import NFTData


class NFTStandard(NFT):
    CODE_HEX = "b5ee9c7241020d010001d0000114ff00f4a413f4bcf2c80b0102016203020009a11f9fe0050202ce050402012008060201200907001d00f232cfd633c58073c5b3327b552000113e910c1c2ebcb85360003b3b513434cffe900835d27080269fc07e90350c04090408f80c1c165b5b6002d70c8871c02497c0f83434c0c05c6c2497c0f83e903e900c7e800c5c75c87e800c7e800c3c00812ce3850c1b088d148cb1c17cb865407e90350c0408fc00f801b4c7f4cfe08417f30f45148c2ea3a1cc840dd78c9004f80c0d0d0d4d60840bf2c9a884aeb8c097c12103fcbc200b0a00727082108b77173505c8cbff5004cf1610248040708010c8cb055007cf165005fa0215cb6a12cb1fcb3f226eb39458cf17019132e201c901fb0001f65135c705f2e191fa4021f001fa40d20031fa00820afaf0801ba121945315a0a1de22d70b01c300209206a19136e220c2fff2e192218e3e821005138d91c85009cf16500bcf16712449145446a0708010c8cb055007cf165005fa0215cb6a12cb1fcb3f226eb39458cf17019132e201c901fb00104794102a375be20c0082028e3526f0018210d53276db103744006d71708010c8cb055007cf165005fa0215cb6a12cb1fcb3f226eb39458cf17019132e201c901fb0093303234e25502f003cc82807e"  # noqa

    def __init__(
            self,
            index: int,
            collection_address: Address,
    ) -> None:
        self._data = self.create_data(index, collection_address).serialize()
        self._code = Cell.one_from_boc(self.CODE_HEX)

    @classmethod
    def create_data(
            cls,
            index: int,
            collection_address: Address,
    ) -> NFTData:
        return NFTData(
            index=index,
            collection_address=collection_address,
        )
