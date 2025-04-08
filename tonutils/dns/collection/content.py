from tonutils.nft.content import BaseOnchainContent


class DNSCollectionContent(BaseOnchainContent):

    def __init__(
            self,
            name: str,
            image: str,
            description: str,
            prefix_uri: str,
    ) -> None:
        super().__init__(
            name=name,
            image=image,
            description=description,
            prefix_uri=prefix_uri,
        )
