import typing as t
from urllib.parse import (
    parse_qsl,
    urlencode,
    urlparse,
    urlsplit,
    urlunsplit,
)

from tonutils.tonconnect.models.request import ConnectRequest

TONCONNECT_PROTOCOL_VERSION = "2"
STANDARD_UNIVERSAL_LINK = "tc://"


def add_path_to_url(url: str, path: str) -> str:
    """Append a path segment to a URL.

    :param url: Base URL.
    :param path: Path segment to append.
    :return: Combined URL.
    """
    return f"{_remove_url_last_slash(url)}/{path}"


def is_telegram_url(link: t.Optional[str] = None) -> bool:
    """Check whether a link is a Telegram URL.

    :param link: URL to check, or `None`.
    :return: `True` if the link uses `tg://` scheme or `t.me` host.
    """
    if not link:
        return False
    parsed = urlparse(link)
    return parsed.scheme == "tg" or parsed.hostname == "t.me"


def encode_telegram_url_parameters(parameters: str) -> str:
    """Encode query parameters for Telegram `startapp` format.

    :param parameters: Raw query string.
    :return: Telegram-safe encoded string.
    """
    return (
        parameters.replace(".", "%2E")
        .replace("-", "%2D")
        .replace("_", "%5F")
        .replace("&", "-")
        .replace("=", "__")
        .replace("%", "--")
    )


def decode_telegram_url_parameters(parameters: str) -> str:
    """Decode Telegram `startapp` parameters back to a query string.

    :param parameters: Telegram-encoded string.
    :return: Decoded query string.
    """
    return (
        parameters.replace("--", "%")
        .replace("__", "=")
        .replace("-", "&")
        .replace("%5F", "_")
        .replace("%2D", "-")
        .replace("%2E", ".")
    )


def generate_universal_link(
    universal_link: str,
    *,
    message: ConnectRequest,
    session_id: str,
    protocol_version: t.Optional[str] = None,
    redirect_url: t.Optional[str] = None,
) -> str:
    """Generate a TonConnect universal link.

    :param universal_link: Wallet universal link base URL.
    :param message: Connect request payload.
    :param session_id: Bridge session identifier.
    :param protocol_version: Protocol version string, or `None` for default.
    :param redirect_url: Post-connect redirect URL, or `None`.
    :return: Ready-to-use universal link.
    """
    if protocol_version is None:
        protocol_version = TONCONNECT_PROTOCOL_VERSION
    if is_telegram_url(universal_link):
        return _generate_tg_universal_link(
            universal_link,
            message=message,
            session_id=session_id,
            protocol_version=protocol_version,
            redirect_url=redirect_url,
        )
    return _generate_regular_universal_link(
        universal_link,
        message=message,
        session_id=session_id,
        protocol_version=protocol_version,
        redirect_url=redirect_url,
    )


def _generate_regular_universal_link(
    universal_link: str,
    *,
    message: ConnectRequest,
    session_id: str,
    protocol_version: str,
    redirect_url: t.Optional[str] = None,
) -> str:
    """Generate a regular (non-Telegram) universal link."""
    split = urlsplit(universal_link)
    q = dict(parse_qsl(split.query, keep_blank_values=True))

    q["v"] = protocol_version
    q["id"] = session_id
    q["r"] = message.dump_json()
    if redirect_url is not None:
        q["ret"] = redirect_url

    query = urlencode(q)

    if universal_link == STANDARD_UNIVERSAL_LINK:
        base = f"{split.scheme}://{split.path}"
        return f"{base}?{query}" if query else base

    comps = (split.scheme, split.netloc, split.path, query, split.fragment)
    return urlunsplit(comps)


def _generate_tg_universal_link(
    universal_link: str,
    *,
    message: ConnectRequest,
    session_id: str,
    protocol_version: str,
    redirect_url: t.Optional[str] = None,
) -> str:
    """Generate a Telegram-specific universal link with `startapp`."""
    url_to_wrap = _generate_regular_universal_link(
        "about:blank",
        message=message,
        session_id=session_id,
        protocol_version=protocol_version,
        redirect_url=redirect_url,
    )
    link_params = urlsplit(url_to_wrap).query

    startapp = "tonconnect-" + encode_telegram_url_parameters(link_params)

    updated = _convert_to_direct_link(universal_link)

    split = urlsplit(updated)
    q = dict(parse_qsl(split.query, keep_blank_values=True))
    q["startapp"] = startapp

    comps = (split.scheme, split.netloc, split.path, urlencode(q), split.fragment)
    return urlunsplit(comps)


def _convert_to_direct_link(universal_link: str) -> str:
    """Convert a Telegram attach-menu link to a direct bot link."""
    split = urlsplit(universal_link)
    q = dict(parse_qsl(split.query, keep_blank_values=True))

    if "attach" in q:
        q.pop("attach", None)
        path = split.path.rstrip("/") + "/start"
    else:
        path = split.path

    comps = (split.scheme, split.netloc, path, urlencode(q), split.fragment)
    return urlunsplit(comps)


def _remove_url_last_slash(url: str) -> str:
    """Strip trailing slash from a URL."""
    if url.endswith("/"):
        return url[:-1]
    return url
