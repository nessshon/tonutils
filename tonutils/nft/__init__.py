from .contract.base import Collection, NFT
from .contract.editable import CollectionEditable, NFTEditable
from .contract.soulbound import CollectionSoulbound, NFTSoulbound
from .contract.standard import CollectionStandard, NFTStandard

__all__ = [
    "Collection",
    "NFT",

    "CollectionEditable",
    "NFTEditable",
    "CollectionSoulbound",
    "NFTSoulbound",
    "CollectionStandard",
    "NFTStandard",
]
