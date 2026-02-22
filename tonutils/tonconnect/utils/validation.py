import typing as t

from tonutils.tonconnect.exceptions import (
    WalletMissingRequiredFeaturesError,
    WalletNotSupportFeatureError,
    WalletWrongNetworkError,
)
from tonutils.tonconnect.models.app import AppWallet
from tonutils.tonconnect.models.feature import (
    SendTransactionFeature,
    SignDataFeature,
)
from tonutils.tonconnect.models.wallet import Wallet
from tonutils.types import NetworkGlobalID


def _find_send_transaction_feature(
    features: t.Sequence[t.Any],
) -> t.Optional[SendTransactionFeature]:
    """Return the first `SendTransactionFeature` in *features*, or `None`."""
    for feature in features:
        if isinstance(feature, SendTransactionFeature):
            return feature
    return None


def _find_sign_data_feature(
    features: t.Sequence[t.Any],
) -> t.Optional[SignDataFeature]:
    """Return the first `SignDataFeature` in *features*, or `None`."""
    for feature in features:
        if isinstance(feature, SignDataFeature):
            return feature
    return None


def verify_wallet_features(wallet: Wallet) -> None:
    """Verify that the wallet declares required features.

    :param wallet: Connected wallet to validate.
    :raises WalletMissingRequiredFeaturesError: If `SendTransaction` is not declared.
    """
    if not wallet.device.features:
        raise WalletMissingRequiredFeaturesError("Wallet did not declare any features")

    has_send_transaction = any(
        isinstance(f, SendTransactionFeature) for f in wallet.device.features
    )
    if not has_send_transaction:
        raise WalletMissingRequiredFeaturesError(
            "Wallet does not declare SendTransaction support"
        )


def verify_send_transaction_support(
    wallet: Wallet,
    num_messages: int = 0,
    app_wallet: t.Optional[AppWallet] = None,
    *,
    has_extra_currency: bool = False,
) -> SendTransactionFeature:
    """Verify `SendTransaction` support on both app and wallet layers.

    :param wallet: Connected wallet with device capabilities.
    :param num_messages: Number of outgoing messages (0 to skip check).
    :param app_wallet: Wallet application descriptor, or `None`.
    :param has_extra_currency: Whether extra-currency transfers are included.
    :return: `SendTransactionFeature` from the connected wallet.
    :raises WalletNotSupportFeatureError: If any validation step fails.
    """
    if app_wallet is not None:
        app_feature = _find_send_transaction_feature(app_wallet.features)
        if app_feature is None:
            raise WalletNotSupportFeatureError(
                f"Wallet app `{app_wallet.app_name}` does not declare SendTransaction support"
            )

        if (
            num_messages > 0
            and app_feature.max_messages is not None
            and num_messages > app_feature.max_messages
        ):
            raise WalletNotSupportFeatureError(
                f"Wallet app `{app_wallet.app_name}` supports max "
                f"{app_feature.max_messages} messages, but {num_messages} were requested"
            )

        if has_extra_currency and not app_feature.extra_currency_supported:
            raise WalletNotSupportFeatureError(
                f"Wallet app `{app_wallet.app_name}` does not support extra currencies"
            )

    wallet_feature = _find_send_transaction_feature(wallet.device.features)
    if wallet_feature is None:
        raise WalletNotSupportFeatureError("Wallet does not support SendTransaction")

    if (
        num_messages > 0
        and wallet_feature.max_messages is not None
        and num_messages > wallet_feature.max_messages
    ):
        raise WalletNotSupportFeatureError(
            f"Wallet supports max {wallet_feature.max_messages} messages, "
            f"but {num_messages} were requested"
        )

    if has_extra_currency and not wallet_feature.extra_currency_supported:
        raise WalletNotSupportFeatureError("Wallet does not support extra currencies")

    return wallet_feature


def verify_sign_data_support(
    wallet: Wallet,
    payload_type: t.Optional[str] = None,
    app_wallet: t.Optional[AppWallet] = None,
) -> SignDataFeature:
    """Verify `SignData` support on both app and wallet layers.

    :param wallet: Connected wallet with device capabilities.
    :param payload_type: Payload type to validate (e.g. `"text"`), or `None`.
    :param app_wallet: Wallet application descriptor, or `None`.
    :return: `SignDataFeature` from the connected wallet.
    :raises WalletNotSupportFeatureError: If any validation step fails.
    """
    if app_wallet is not None:
        app_feature = _find_sign_data_feature(app_wallet.features)
        if app_feature is None:
            raise WalletNotSupportFeatureError(
                f"Wallet app `{app_wallet.app_name}` does not declare SignData support"
            )

        if payload_type is not None and payload_type not in app_feature.types:
            raise WalletNotSupportFeatureError(
                f"Wallet app `{app_wallet.app_name}` does not support "
                f"SignData type `{payload_type}`, supported: {app_feature.types}"
            )

    wallet_feature = _find_sign_data_feature(wallet.device.features)
    if wallet_feature is None:
        raise WalletNotSupportFeatureError("Wallet does not support SignData")

    if payload_type is not None and payload_type not in wallet_feature.types:
        raise WalletNotSupportFeatureError(
            f"Wallet does not support SignData type `{payload_type}`, "
            f"supported: {wallet_feature.types}"
        )

    return wallet_feature


def verify_wallet_network(
    wallet: Wallet,
    expected_network: NetworkGlobalID,
) -> None:
    """Verify the wallet operates on the expected network.

    :param wallet: Connected wallet.
    :param expected_network: Expected network identifier.
    :raises WalletWrongNetworkError: If the network does not match.
    """
    if wallet.account.network != expected_network:
        raise WalletWrongNetworkError(
            f"Expected network {expected_network.value}, "
            f"got {wallet.account.network.value}"
        )
