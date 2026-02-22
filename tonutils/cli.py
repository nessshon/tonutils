import argparse
import asyncio
import typing as t

from tonutils import __version__
from tonutils.clients.adnl.provider.config import (
    get_mainnet_global_config,
    get_testnet_global_config,
    load_global_config,
)
from tonutils.tools.status_monitor import LiteServerMonitor
from tonutils.types import NetworkGlobalID

NETWORK_MAP: t.Dict[str, NetworkGlobalID] = {
    "mainnet": NetworkGlobalID.MAINNET,
    "testnet": NetworkGlobalID.TESTNET,
}
"""Mapping of network names to `NetworkGlobalID`."""


def parse_network(value: str) -> NetworkGlobalID:
    """Convert CLI network name to `NetworkGlobalID`.

    :param value: "mainnet" or "testnet" (case-insensitive).
    :return: Resolved `NetworkGlobalID`.
    :raises argparse.ArgumentTypeError: Unknown network name.
    """
    value = value.lower().strip()
    if value not in NETWORK_MAP:
        raise argparse.ArgumentTypeError(f"Unknown network: {value}")
    return NETWORK_MAP[value]


def cmd_status(args: argparse.Namespace) -> None:
    """Run the `status` subcommand.

    :param args: Parsed arguments with *network*, *config*, and *rps*.
    """
    if args.config:
        config = load_global_config(args.config)
    else:
        config_getter = {
            NetworkGlobalID.MAINNET: get_mainnet_global_config,
            NetworkGlobalID.TESTNET: get_testnet_global_config,
        }
        config = config_getter[args.network]()

    async def _run() -> None:
        monitor = LiteServerMonitor.from_config(
            config=config,
            network=args.network,
            rps_limit=args.rps,
        )
        try:
            await monitor.run()
        finally:
            await monitor.stop()

    try:
        asyncio.run(_run())
    except KeyboardInterrupt:
        pass


def _create_parser() -> argparse.ArgumentParser:
    """Build the top-level argument parser.

    :return: Configured `ArgumentParser`.
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
        help="Monitor lite-servers status.",
    )
    status.add_argument(
        "-n",
        "--network",
        type=parse_network,
        metavar="NET",
        default=NetworkGlobalID.MAINNET,
        help="mainnet (default) or testnet",
    )
    status.add_argument(
        "-c",
        "--config",
        type=str,
        metavar="PATH",
        help="Config file path or URL",
    )
    status.add_argument(
        "-r",
        "--rps",
        type=int,
        metavar="N",
        default=100,
        help="Requests per second (default: 100)",
    )
    status.set_defaults(func=cmd_status)

    return parser


def main() -> None:
    """CLI entry-point. Dispatches to the matched subcommand or prints help."""
    parser = _create_parser()
    args = parser.parse_args()

    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
