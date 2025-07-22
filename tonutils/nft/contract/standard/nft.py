from __future__ import annotations

from typing import Optional, Union

from pytoniq_core import Cell, Address

from ..base.nft import NFT
from ...content import (
    NFTOffchainContent,
    NFTModifiedOnchainContent,
    NFTModifiedOffchainContent,
    SweetOffchainContent,
)
from ...data import NFTData


class NFTStandardBase(NFT):

    def __init__(
            self,
            index: Optional[int] = None,
            collection_address: Optional[Address] = None,
            owner_address: Optional[Address] = None,
            content: Optional[Union[NFTOffchainContent, NFTModifiedOnchainContent, NFTModifiedOffchainContent, SweetOffchainContent]] = None,
    ) -> None:
        self._data = self.create_data(index, collection_address, owner_address, content).serialize()
        self._code = Cell.one_from_boc(self.CODE_HEX)

    @classmethod
    def create_data(
            cls,
            index: Optional[int] = None,
            collection_address: Optional[Address] = None,
            owner_address: Optional[Address] = None,
            content: Optional[Union[NFTOffchainContent, NFTModifiedOnchainContent, NFTModifiedOffchainContent, SweetOffchainContent]] = None,
    ) -> NFTData:
        return NFTData(
            index=index,
            collection_address=collection_address,
            owner_address=owner_address,
            content=content,
        )


class NFTStandard(NFTStandardBase):
    CODE_HEX = "b5ee9c7241020d010001d0000114ff00f4a413f4bcf2c80b0102016203020009a11f9fe0050202ce050402012008060201200907001d00f232cfd633c58073c5b3327b552000113e910c1c2ebcb85360003b3b513434cffe900835d27080269fc07e90350c04090408f80c1c165b5b6002d70c8871c02497c0f83434c0c05c6c2497c0f83e903e900c7e800c5c75c87e800c7e800c3c00812ce3850c1b088d148cb1c17cb865407e90350c0408fc00f801b4c7f4cfe08417f30f45148c2ea3a1cc840dd78c9004f80c0d0d0d4d60840bf2c9a884aeb8c097c12103fcbc200b0a00727082108b77173505c8cbff5004cf1610248040708010c8cb055007cf165005fa0215cb6a12cb1fcb3f226eb39458cf17019132e201c901fb0001f65135c705f2e191fa4021f001fa40d20031fa00820afaf0801ba121945315a0a1de22d70b01c300209206a19136e220c2fff2e192218e3e821005138d91c85009cf16500bcf16712449145446a0708010c8cb055007cf165005fa0215cb6a12cb1fcb3f226eb39458cf17019132e201c901fb00104794102a375be20c0082028e3526f0018210d53276db103744006d71708010c8cb055007cf165005fa0215cb6a12cb1fcb3f226eb39458cf17019132e201c901fb0093303234e25502f003cc82807e"  # noqa

    def __init__(
            self,
            index: int,
            collection_address: Optional[Address] = None,
            owner_address: Optional[Address] = None,
            content: Optional[NFTOffchainContent] = None,
    ) -> None:
        super().__init__(
            index=index,
            collection_address=collection_address,
            owner_address=owner_address,
            content=content,
        )


class NFTStandardModified(NFTStandardBase):
    # https://github.com/nessshon/nft-contracts/blob/main/standard/func/nft-item.func
    CODE_HEX = "b5ee9c7241020e01000229000114ff00f4a413f4bcf2c80b0102016202030202cc04050009a11f9fe00f0201200607001dd81e4659fac678b00e78b6664f6aa403b9d1910e380492f81f068698180b8d8492f81f07d207d2018fd0018b8eb90fd0018fd001839d4da0078038259f18103698fe99fc1082fe61e8a29185d474499081baf192009ed9e70181a1a1a9ac10817e59351095d71812f824207f978408090a0201580c0d00ca306c22345232c705f2e19501fa40d45423405235f00821c701c0008e4401fa00218e3a821005138d9170c85006cf1658cf161034413073708010c8cb055007cf165005fa0215cb6a12cb1fcb3f226eb39458cf17019132e201c901fb00925f04e2925f03e201f65135c705f2e191fa4021f006fa40d20031fa00820afaf0801ba121945315a0a1de22d70b01c300209206a19136e220c2fff2e192218e3e821005138d91c85009cf16500bcf16712449145446a0708010c8cb055007cf165005fa0215cb6a12cb1fcb3f226eb39458cf17019132e201c901fb00104794102a375be20b00727082108b77173505c8cbff5004cf1610248040708010c8cb055007cf165005fa0215cb6a12cb1fcb3f226eb39458cf17019132e201c901fb000082028e3526f0068210d53276db103744006d71708010c8cb055007cf165005fa0215cb6a12cb1fcb3f226eb39458cf17019132e201c901fb0093303234e25502f00800113e910c1c2ebcb85360003b3b513434cffe900835d27080269fc07e90350c04090408f80c1c165b5b60d746cf95"  # noqa

    def __init__(
            self,
            index: int,
            collection_address: Optional[Address] = None,
            owner_address: Optional[Address] = None,
            content: Optional[Union[NFTModifiedOnchainContent, NFTModifiedOffchainContent]] = None,
    ) -> None:
        super().__init__(
            index=index,
            collection_address=collection_address,
            owner_address=owner_address,
            content=content,
        )

class SweetNFTStandard(NFTStandardBase):
    # https://github.com/sweet-io-org/miniapp-nft-contracts/blob/master/contracts/nft/standard_nft_item.fc
    CODE_HEX = "b5ee9c7241021001000299000114ff00f4a413f4bcf2c80b01020162020f0202cd030c020120040b03f743221c700925f03e0d0d3030171b0925f03e0fa40fa4031fa003171d721fa0031fa003073a9b400f00404b38eb8306c22345232c705f2e19501d42220c00097308030c8cb07c9e30ed0c801cf1602d012cf16c920d0d749830bbbf2e19601fa40304300f005e006d31fd33f82105fcc3d145230bae3023034343535805070a01fac87022820186a0a90420c2009f31a63001cb077102820186a0a908029130e222812710a90420c20022b19e31a63001cb077102812710a908029130e2228103e8a90420c20022b19e31a63001cb0771028103e8a908029130e2228064a90420c20022b19d31a63001cb0771028064a908029130e2227aa90420c20058b106002a9aa63001cb07017aa908019130e201a63001cb07c902ac3210375e3240135135c705f2e191fa4021f003fa40d20031fa0020d749c200f2e2c4820afaf0801ba121945315a0a1de22d70b01c300209206a19136e220c2fff2e1922194102a375be30d0293303234e30d5502f0050809007c821005138d91c85009cf16500bcf16712449145446a0708010c8cb055007cf165005fa0215cb6a12cb1fcb3f226eb39458cf17019132e201c901fb001047006a26f0038210d53276db103744006d71708010c8cb055007cf165005fa0215cb6a12cb1fcb3f226eb39458cf17019132e201c901fb00009482102fcb26a212ba8e397082108b77173505c8cbff5004cf1610248040708010c8cb055007cf165005fa0215cb6a12cb1fcb3f226eb39458cf17019132e201c901fb00e05f04840ff2f000115fa443070baf2e14d80201480d0e003b3b513434cffe900835d27080269fc07e90350c04090408f80c1c165b5b60001d00f232cfd633c58073c5b3327b55200009a11f9fe009d926ab9e"  # noqa

    def __init__(
            self,
            collection_address: Optional[Address] = None,
            owner_address: Optional[Address] = None,
            content: Optional[SweetOffchainContent] = None,
    ) -> None:
        super().__init__(
            index=None,  # Index is automatically assigned by the collection contract for Sweet NFTs
            collection_address=collection_address,
            owner_address=owner_address,
            content=content,
        )