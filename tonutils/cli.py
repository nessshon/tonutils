import argparse
import asyncio
import os
import typing as t
from contextlib import suppress

from ton_core import (
    GlobalConfig,
    NetworkGlobalID,
    get_mainnet_global_config,
    get_testnet_global_config,
    load_global_config,
)

from tonutils.__meta__ import __version__
from tonutils.tools.status_monitor import DhtMonitor, LiteServerMonitor
from tonutils.types import DEFAULT_ADNL_RETRY_POLICY

NETWORK_MAP: dict[str, NetworkGlobalID] = {
    "mainnet": NetworkGlobalID.MAINNET,
    "testnet": NetworkGlobalID.TESTNET,
}
"""Mapping of network names to ``NetworkGlobalID``."""


def parse_network(value: str) -> NetworkGlobalID:
    """Convert CLI network name to ``NetworkGlobalID``.

    :param value: "mainnet" or "testnet" (case-insensitive).
    :return: Resolved ``NetworkGlobalID``.
    :raises argparse.ArgumentTypeError: Unknown network name.
    """
    value = value.lower().strip()
    if value not in NETWORK_MAP:
        raise argparse.ArgumentTypeError(f"Unknown network: {value}")
    return NETWORK_MAP[value]


def _load_config(args: argparse.Namespace) -> GlobalConfig:
    """Load global config from CLI arguments.

    :param args: Parsed arguments with *network* and *config*.
    :return: Loaded ``GlobalConfig``.
    """
    if args.config:
        return load_global_config(args.config)

    config_getter: dict[NetworkGlobalID, t.Callable[[], GlobalConfig]] = {
        NetworkGlobalID.MAINNET: get_mainnet_global_config,
        NetworkGlobalID.TESTNET: get_testnet_global_config,
    }
    return config_getter[args.network]()


def cmd_status(args: argparse.Namespace) -> None:
    """Run the ``status`` subcommand.

    :param args: Parsed arguments with *network*, *config*, *rps*, and *status_command*.
    """
    sub = getattr(args, "status_command", None)

    if sub == "dht":
        _run_dht_monitor(args)
    else:
        _run_ls_monitor(args)


def _run_ls_monitor(args: argparse.Namespace) -> None:
    """Run the LiteServer status monitor.

    :param args: Parsed arguments with *network*, *config*, and *rps*.
    """
    config = _load_config(args)

    async def _run() -> None:
        monitor = LiteServerMonitor.from_config(
            config=config,
            network=args.network,
            rps_limit=args.rps,
            retry_policy=DEFAULT_ADNL_RETRY_POLICY if args.retry else None,
        )
        try:
            await monitor.run()
        finally:
            await monitor.stop()

    with suppress(KeyboardInterrupt):
        asyncio.run(_run())


def _run_dht_monitor(args: argparse.Namespace) -> None:
    """Run the DHT node status monitor.

    :param args: Parsed arguments with *network* and *config*.
    """
    config = _load_config(args)

    async def _run() -> None:
        monitor = DhtMonitor.from_config(config=config)
        try:
            await monitor.run()
        finally:
            await monitor.stop()

    with suppress(KeyboardInterrupt):
        asyncio.run(_run())


def _add_common_args(parser: argparse.ArgumentParser) -> None:
    """Add ``-n`` / ``-c`` arguments shared by status subcommands.

    :param parser: Parser or subparser to add arguments to.
    """
    parser.add_argument(
        "-n",
        "--network",
        type=parse_network,
        metavar="NET",
        default=NetworkGlobalID.MAINNET,
        help="mainnet (default) or testnet",
    )
    parser.add_argument(
        "-c",
        "--config",
        type=str,
        metavar="PATH",
        help="Config file path or URL",
    )


def _create_parser() -> argparse.ArgumentParser:
    """Build the top-level argument parser.

    :return: Configured ``ArgumentParser``.
    """
    parser = argparse.ArgumentParser(
        prog="tonutils",
        description="Tonutils CLI.",
    )
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=f"tonutils {__version__}",
    )

    subs = parser.add_subparsers(dest="command", metavar="command")

    status = subs.add_parser(
        "status",
        help="Monitor node status.",
    )
    _add_common_args(status)
    status.add_argument(
        "-r",
        "--rps",
        type=int,
        metavar="N",
        default=100,
        help="Requests per second (default: 100)",
    )
    status.add_argument(
        "--retry",
        action="store_true",
        default=False,
        help="Enable default ADNL retry policy",
    )
    status.set_defaults(func=cmd_status)

    status_subs = status.add_subparsers(dest="status_command", metavar="subcommand")

    ls_parser = status_subs.add_parser(
        "ls",
        help="Monitor lite-servers status.",
    )
    _add_common_args(ls_parser)
    ls_parser.add_argument(
        "-r",
        "--rps",
        type=int,
        metavar="N",
        default=100,
        help="Requests per second (default: 100)",
    )
    ls_parser.add_argument(
        "--retry",
        action="store_true",
        default=False,
        help="Enable default ADNL retry policy",
    )
    ls_parser.set_defaults(func=cmd_status, status_command="ls")

    dht_parser = status_subs.add_parser(
        "dht",
        help="Monitor DHT nodes status.",
    )
    _add_common_args(dht_parser)
    dht_parser.set_defaults(func=cmd_status, status_command="dht", rps=100)

    return parser


def main() -> None:
    """CLI entry-point. Dispatches to the matched subcommand or prints help."""
    if os.environ.get("PYTHONIOENCODING", "").lower() not in ("utf-8", "utf8"):
        os.environ.setdefault("PYTHONIOENCODING", "utf-8")

    parser = _create_parser()
    args = parser.parse_args()

    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
