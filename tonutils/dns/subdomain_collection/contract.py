from typing import Union, Any

from pytoniq_core import Address, Cell, begin_cell

from .content import SubdomainCollectionContent
from .data import SubdomainCollectionData, FullDomain
from .op_codes import *
from ...contract import Contract
from ...nft.royalty_params import RoyaltyParams


class SubdomainCollection(Contract):
    # https://github.com/nessshon/subdomains-toolbox/blob/main/collection-contracts/admin-mint/

    CODE_HEX = "b5ee9c7241023201000512000114ff00f4a413f4bcf2c80b0102016202240202cb03230201200416020120050f020120060c020120070b02ef0831c02497c0f8007434c0c05c6c2497c0f83e900c083c004074c7fc0389b000238f8c4c8d1490b1c17cb864412084017d78402fbcb8333c030835d2483081fcb832082040fc2efcb8325e2a4230003cb832883c037cb832c83e4040d0513c04b80e0134cfc9b0006497c27809a0841ed2d0b9aeb8c089a00809007c135f036c42820afaf08070fb02708210d372158c586d8306708010c8cb055007cf165005fa0215cb6a12cb1fcb3f226eb39458cf17019132e201c901fb0001fc8210e8a0abfeba8e3a135f036c42820afaf08070fb0270841f586d8306708010c8cb055007cf165005fa0215cb6a12cb1fcb3f226eb39458cf17019132e201c901fb00e0268210693d3950ba8e2a145f043431d0128210a8cb00ad708010c8cb055005cf1624fa0214cb6a13cb1fcb3f01cf16c98040fb00e0315163c7050a0080f2e19124c0038e15323303fa40304314c85005cf1613ccccccccc9ed54e0313202c0048e1402d4d430440302c85005cf1613ccccccccc9ed54e05f04840ff2f000113e910c30003cb853600201200d0e00111c3232c1c073c5b2600009341e35c86002012010130201201112004b081be2320869548c1be073c5b24069bfa4c830bfe73214cc5be073c584b33240697a0c0c7420002d007232fffe0a33c5b25c083232c044fd003d0032c032600201201415001b3e401d3232c084b281f2fff2742000633c00fd010c20bc1e1360bb8156946503e6578a7add8d37f7ac7e04d87ff808defd19f6684ae4328060c1fd03dbe84c3c00e0020120171e020120181b020120191a008300fc01e2c4ba22c4ba09551101019bc17c013c00a2c4be22c4ba22cdc1b99e09544dd51190dbc1bc013c00978862c4be140122c4ba22d1a9cdbdba1bc1bc013c00a000231c0832140133c584f2c1c073c5b2c1f274200201201c1d00113435350c007400742000331c27c074c1c07000082ce500a98200b784b98c4830003cb432e00201201f220201202021004f3223880875d244b5c61673c58875d2883000082ce6c070007cb832c0b50c3400a44c78b98c727420007f1c0875d2638d572e882ce38b8c00b4c1c8700b48f0802c0929be14902e6c08b08bc8f04eac2c48b09800f05ec4ec04ac6cc82ce500a98200b784f7b99b04aea000154ed44d0fa40d4d4d4d4308009fa109f802b810f80301f805642802678b64e42802678b64e42c678b64e46666096664b87c12b8e4658fe59fa802e78b6638fd0109e58064bbc00c646582a801e78b387d010965b589666664c0207d8040020120252d020120262a02016227280015ae65f8073620f8057804c001c1adae98f8071a2d80f80501e8209878043689c1784151a9bff86de73f761aeb4f6e1d0c4f7378bec179a9d2a9fcd54b6585f1e74480c183fa0bc1783082eb663b57a00192f4a6ac467288df2dfeddb9da1bee28f6521c8bebd21f1e80c183fa0bc029005c82f070e5d7b6a29b392f85076fe15ca2f2053c56c2338728c4e33c9e8ddb1ee827cc018307f41770c8cb07f400c90201202b2c001fb5dafe01c28be09a1a61fa61ff480610001db4f47e01c2048be09e00ae003e00d00201202e2f0011b905bf00e5f037f02802012030310013b64a5e01cd883e014630009db46186041ae92f152118001e5c08c41ae140f800043ae938010a4216126b6f0dbc0412a03a60e6203bc43e016a245ae3061f2030401752791961e030402cf47da87b19e2d920322f122e1c42540030f5b43237"  # noqa
    ITEM_CODE_HEX = "b5ee9c7241021b010003d9000114ff00f4a413f4bcf2c80b0102016202140202cd0311020120040e020120050d04b10c8871c02497c0f83434c0c05c6c2497c0f83e90087c007e900c7e800c5c75c87e800c7e800c1cea6d0000b4c7f4cffc01016cf8c089f00078c089e08417f30f452ea3a24dd205915d44c536cf380e4e4960840bf2c9a8aea00608090b01fa5b323435355233c705f2e1916d70c8cb07f400c904fa40d420c701c0008e42fa00218e3a821005138d9170c829cf165003cf162504503373708010c8cb055007cf165005fa0215cb6a12cb1fcb3f226eb39458cf17019132e201c901fb00915be29130e2820afaf08070fb027082107b4b42e6c824cf16270450778306070054708010c8cb055007cf165005fa0215cb6a12cb1fcb3f226eb39458cf17019132e201c901fb005042f005009210245f0435355b21c705f2e191708210e8a0abfe21c805fa403015cf16103441308040708010c8cb055007cf165005fa0215cb6a12cb1fcb3f226eb39458cf17019132e201c901fb0001f65136c705f2e191fa4021f001fa40d20031fa000b820afaf080a121945315a0a1de22d70b01c300209206a19136e220c2fff2e192218e3dc85009cf16500bcf16821005138d9171245146104e50e2708010c8cb055007cf165005fa0215cb6a12cb1fcb3f226eb39458cf17019132e201c901fb0094102b385be2020a007e8e3427f00147408210d53276db016d71708010c8cb055007cf165005fa0215cb6a12cb1fcb3f226eb39458cf17019132e201c901fb0093303335e25503f00501a28e3d35365b347082108b77173504c8cbff58cf164430128040708010c8cb055007cf165005fa0215cb6a12cb1fcb3f226eb39458cf17019132e201c901fb00e0340482104eb1f0f9bae3025f07840ff2f00c00745146c705f2e191d3ff20d74ac20006d0d30701c000f2e19cf404300698d43040158307f417983050048307f45b30e270c8cb07f400c94404f00500113e910c30003cb853600201200f100019343500740075007400750c342000331c14c0321401b3c58572c1d400f3c584f2c1d633c5b2c1f274200201481213003f3b513434fffe900835d2708026dfc07e9035350c040d440d380c1c165b5b5b600021013232ffd400f3c58073c5b333327b552002012015160015bc265f8023628f8017801c0201201718001bb8fcff00431f00231c832cf16c98020120191a0015b64a5e008d8a3e004d843000c5b461843ae9240f152118001e5c08de0082abe0ba1a60e038001e5c339e8086007ae140f8001e5c33b84111c466105e033e04883dcb11fb64ddc4964ad1ba06b879240dc23572f37cc5caaab143a2fffbc4180012660f003c003060fe81edf4260f00305b5cfb6d"  # noqa

    def __init__(
            self,
            owner_address: Union[Address, str],
            content: SubdomainCollectionContent,
            royalty_params: RoyaltyParams,
            full_domain: FullDomain,
    ) -> None:
        self._data = self.create_data(
            owner_address=owner_address,
            content=content,
            royalty_params=royalty_params,
            full_domain=full_domain,
        ).serialize()
        self._code = Cell.one_from_boc(self.CODE_HEX)

    @classmethod
    def create_data(
            cls,
            owner_address: Union[Address, str],
            content: SubdomainCollectionContent,
            royalty_params: RoyaltyParams,
            full_domain: FullDomain,
    ) -> Any:
        return SubdomainCollectionData(
            owner_address=owner_address,
            content=content,
            item_code=Cell.one_from_boc(cls.ITEM_CODE_HEX),
            royalty_params=royalty_params,
            full_domain=full_domain,
        )

    @classmethod
    def build_deploy_body(cls, query_id: int = 0) -> Cell:
        return (
            begin_cell()
            .store_uint(DEPLOY_OPCODE, 32)
            .store_uint(query_id, 64)
            .end_cell()
        )

    @classmethod
    def build_change_owner_body(cls, owner_address: Address, query_id: int = 0) -> Cell:
        return (
            begin_cell()
            .store_uint(CHANGE_OWNER_OPCODE, 32)
            .store_uint(query_id, 64)
            .store_address(owner_address)
            .end_cell()
        )

    @classmethod
    def build_edit_content(
            cls,
            content: SubdomainCollectionContent,
            royalty_params: RoyaltyParams,
            query_id: int = 0,
    ) -> Cell:
        return (
            begin_cell()
            .store_uint(EDIT_CONTENT_OPCODE, 32)
            .store_uint(query_id, 64)
            .store_ref(content.serialize())
            .store_ref(royalty_params.serialize())
            .end_cell()
        )

    @classmethod
    def build_mint_subdomain_body(cls, subdomain: str) -> Cell:
        return (
            begin_cell()
            .store_uint(0, 32)
            .store_snake_string(subdomain)
            .end_cell()
        )
