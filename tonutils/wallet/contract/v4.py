from __future__ import annotations

from typing import List, Tuple, Union

from pytoniq_core import Cell, WalletMessage

from ._base import Wallet
from ..data import WalletV4Data
from ...client import Client


class WalletV4R1(Wallet):
    """
    A class representing Wallet V4 R1 in the TON blockchain.
    """

    CODE_HEX = "b5ee9c72410215010002f5000114ff00f4a413f4bcf2c80b010201200203020148040504f8f28308d71820d31fd31fd31f02f823bbf263ed44d0d31fd31fd3fff404d15143baf2a15151baf2a205f901541064f910f2a3f80024a4c8cb1f5240cb1f5230cbff5210f400c9ed54f80f01d30721c0009f6c519320d74a96d307d402fb00e830e021c001e30021c002e30001c0039130e30d03a4c8cb1f12cb1fcbff1112131403eed001d0d3030171b0915be021d749c120915be001d31f218210706c7567bd228210626c6e63bdb022821064737472bdb0925f03e002fa403020fa4401c8ca07cbffc9d0ed44d0810140d721f404305c810108f40a6fa131b3925f05e004d33fc8258210706c7567ba9131e30d248210626c6e63bae30004060708020120090a005001fa00f404308210706c7567831eb17080185005cb0527cf165003fa02f40012cb69cb1f5210cb3f0052f8276f228210626c6e63831eb17080185005cb0527cf1624fa0214cb6a13cb1f5230cb3f01fa02f4000092821064737472ba8e3504810108f45930ed44d0810140d720c801cf16f400c9ed54821064737472831eb17080185004cb0558cf1622fa0212cb6acb1fcb3f9410345f04e2c98040fb000201200b0c0059bd242b6f6a2684080a06b90fa0218470d4080847a4937d29910ce6903e9ff9837812801b7810148987159f31840201580d0e0011b8c97ed44d0d70b1f8003db29dfb513420405035c87d010c00b23281f2fff274006040423d029be84c600201200f100019adce76a26840206b90eb85ffc00019af1df6a26840106b90eb858fc0006ed207fa00d4d422f90005c8ca0715cbffc9d077748018c8cb05cb0222cf165005fa0214cb6b12ccccc971fb00c84014810108f451f2a702006c810108d718c8542025810108f451f2a782106e6f746570748018c8cb05cb025004cf16821005f5e100fa0213cb6a12cb1fc971fb00020072810108d718305202810108f459f2a7f82582106473747270748018c8cb05cb025005cf16821005f5e100fa0214cb6a13cb1f12cb3fc973fb00000af400c9ed5446a9f34f"  # noqa

    @classmethod
    def create(
            cls,
            client: Client,
            wallet_id: int = 698983191,
            **kwargs,
    ) -> Tuple[WalletV4R1, bytes, bytes, List[str]]:
        return super().create(client, wallet_id)

    @classmethod
    def from_mnemonic(
            cls,
            client: Client,
            mnemonic: Union[List[str], str],
            wallet_id: int = 698983191,
            **kwargs,
    ) -> Tuple[WalletV4R1, bytes, bytes, List[str]]:
        return super().from_mnemonic(client, mnemonic, wallet_id)

    @classmethod
    def create_data(cls, public_key: bytes, wallet_id: int = 698983191, seqno: int = 0) -> WalletV4Data:
        return WalletV4Data(public_key, wallet_id, seqno)

    def raw_create_transfer_msg(
            self,
            private_key: bytes,
            messages: List[WalletMessage],
            **kwargs,
    ) -> Cell:
        return super().raw_create_transfer_msg(
            private_key=private_key,
            messages=messages,
            op_code=0,
            **kwargs,
        )


class WalletV4R2(Wallet):
    """
    A class representing Wallet V4 R2 in the TON blockchain.
    """

    CODE_HEX = "b5ee9c72410214010002d4000114ff00f4a413f4bcf2c80b010201200203020148040504f8f28308d71820d31fd31fd31f02f823bbf264ed44d0d31fd31fd3fff404d15143baf2a15151baf2a205f901541064f910f2a3f80024a4c8cb1f5240cb1f5230cbff5210f400c9ed54f80f01d30721c0009f6c519320d74a96d307d402fb00e830e021c001e30021c002e30001c0039130e30d03a4c8cb1f12cb1fcbff1011121302e6d001d0d3032171b0925f04e022d749c120925f04e002d31f218210706c7567bd22821064737472bdb0925f05e003fa403020fa4401c8ca07cbffc9d0ed44d0810140d721f404305c810108f40a6fa131b3925f07e005d33fc8258210706c7567ba923830e30d03821064737472ba925f06e30d06070201200809007801fa00f40430f8276f2230500aa121bef2e0508210706c7567831eb17080185004cb0526cf1658fa0219f400cb6917cb1f5260cb3f20c98040fb0006008a5004810108f45930ed44d0810140d720c801cf16f400c9ed540172b08e23821064737472831eb17080185005cb055003cf1623fa0213cb6acb1fcb3fc98040fb00925f03e20201200a0b0059bd242b6f6a2684080a06b90fa0218470d4080847a4937d29910ce6903e9ff9837812801b7810148987159f31840201580c0d0011b8c97ed44d0d70b1f8003db29dfb513420405035c87d010c00b23281f2fff274006040423d029be84c600201200e0f0019adce76a26840206b90eb85ffc00019af1df6a26840106b90eb858fc0006ed207fa00d4d422f90005c8ca0715cbffc9d077748018c8cb05cb0222cf165005fa0214cb6b12ccccc973fb00c84014810108f451f2a7020070810108d718fa00d33fc8542047810108f451f2a782106e6f746570748018c8cb05cb025006cf165004fa0214cb6a12cb1fcb3fc973fb0002006c810108d718fa00d33f305224810108f459f2a782106473747270748018c8cb05cb025005cf165003fa0213cb6acb1f12cb3fc973fb00000af400c9ed54696225e5"  # noqa

    @classmethod
    def create(
            cls,
            client: Client,
            wallet_id: int = 698983191,
            **kwargs,
    ) -> Tuple[WalletV4R2, bytes, bytes, List[str]]:
        return super().create(client, wallet_id, **kwargs)

    @classmethod
    def from_mnemonic(
            cls,
            client: Client,
            mnemonic: Union[List[str], str],
            wallet_id: int = 698983191,
            **kwargs,
    ) -> Tuple[WalletV4R2, bytes, bytes, List[str]]:
        return super().from_mnemonic(client, mnemonic, wallet_id, **kwargs)

    @classmethod
    def create_data(
            cls,
            public_key: bytes,
            wallet_id: int = 698983191,
            seqno: int = 0,
    ) -> WalletV4Data:
        return WalletV4Data(public_key, wallet_id, seqno)

    def raw_create_transfer_msg(
            self,
            private_key: bytes,
            messages: List[WalletMessage],
            **kwargs,
    ) -> Cell:
        return super().raw_create_transfer_msg(
            private_key=private_key,
            messages=messages,
            op_code=0,
            **kwargs,
        )
