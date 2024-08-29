def generate_wallet_id(
        subwallet_id: int,
        workchain: int = 0,
        wallet_version: int = 0,
        network_global_id: int = -239,
) -> int:
    """
    Generates a wallet ID based on global ID, workchain, wallet version, and wallet id.

    :param subwallet_id: The subwallet ID (16-bit unsigned integer).
    :param workchain: The workchain value (8-bit signed integer).
    :param wallet_version: The wallet version (8-bit unsigned integer).
    :param network_global_id: The network global ID (32-bit signed integer).
    """
    ctx = 0
    ctx |= 1 << 31
    ctx |= (workchain & 0xFF) << 23
    ctx |= (wallet_version & 0xFF) << 15
    ctx |= (subwallet_id & 0xFFFF)

    return ctx ^ (network_global_id & 0xFFFFFFFF)
