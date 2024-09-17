from __future__ import annotations

from typing import Optional, Union

from pytoniq_core import Cell, Address

from ..base.nft import NFT
from ...content import NFTOnchainContent, NFTOffchainContent
from ...data import NFTData


class NFTStandard(NFT):
    # https://github.com/nessshon/nft-contracts/blob/main/standard/func/nft-item.func
    CODE_HEX = "b5ee9c7241020e01000229000114ff00f4a413f4bcf2c80b0102016202030202cc04050009a11f9fe00f0201200607001dd81e4659fac678b00e78b6664f6aa403b9d1910e380492f81f068698180b8d8492f81f07d207d2018fd0018b8eb90fd0018fd001839d4da0078038259f18103698fe99fc1082fe61e8a29185d474499081baf192009ed9e70181a1a1a9ac10817e59351095d71812f824207f978408090a0201580c0d00ca306c22345232c705f2e19501fa40d45423405235f00821c701c0008e4401fa00218e3a821005138d9170c85006cf1658cf161034413073708010c8cb055007cf165005fa0215cb6a12cb1fcb3f226eb39458cf17019132e201c901fb00925f04e2925f03e201f65135c705f2e191fa4021f006fa40d20031fa00820afaf0801ba121945315a0a1de22d70b01c300209206a19136e220c2fff2e192218e3e821005138d91c85009cf16500bcf16712449145446a0708010c8cb055007cf165005fa0215cb6a12cb1fcb3f226eb39458cf17019132e201c901fb00104794102a375be20b00727082108b77173505c8cbff5004cf1610248040708010c8cb055007cf165005fa0215cb6a12cb1fcb3f226eb39458cf17019132e201c901fb000082028e3526f0068210d53276db103744006d71708010c8cb055007cf165005fa0215cb6a12cb1fcb3f226eb39458cf17019132e201c901fb0093303234e25502f00800113e910c1c2ebcb85360003b3b513434cffe900835d27080269fc07e90350c04090408f80c1c165b5b60d746cf95"  # noqa

    def __init__(
            self,
            index: int,
            collection_address: Optional[Address] = None,
            owner_address: Optional[Address] = None,
            content: Optional[Union[NFTOnchainContent, NFTOffchainContent]] = None,
    ) -> None:
        self._data = self.create_data(index, collection_address, owner_address, content).serialize()
        self._code = Cell.one_from_boc(self.CODE_HEX)

    @classmethod
    def create_data(
            cls,
            index: int,
            collection_address: Address,
            owner_address: Optional[Address] = None,
            content: Optional[Union[NFTOnchainContent, NFTOffchainContent]] = None,
    ) -> NFTData:
        return NFTData(
            index=index,
            collection_address=collection_address,
            owner_address=owner_address,
            content=content,
        )
