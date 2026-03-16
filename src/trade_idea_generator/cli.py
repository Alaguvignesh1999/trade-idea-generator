from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path

from .config import load_settings
from .snapshots import generate_market_outputs, validate_snapshot_tree, write_manifest
from .utils import slugify


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="trade-idea-generator")
    parser.add_argument("--config", default="configs/default.json")
    subparsers = parser.add_subparsers(dest="command", required=True)

    snapshot_parser = subparsers.add_parser("generate-snapshot")
    snapshot_parser.add_argument("--market", required=True)
    snapshot_parser.add_argument("--as-of", default=str(date.today()))

    all_parser = subparsers.add_parser("generate-all-snapshots")
    all_parser.add_argument("--as-of", default=str(date.today()))

    backtest_parser = subparsers.add_parser("run-backtest")
    backtest_parser.add_argument("--market", required=True)
    backtest_parser.add_argument("--as-of", default=str(date.today()))

    validate_parser = subparsers.add_parser("validate-snapshots")
    validate_parser.add_argument("--path", default="artifacts")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    settings = load_settings(args.config)

    if args.command == "generate-snapshot":
        snapshot, backtest, paths = generate_market_outputs(settings, args.market, as_of=args.as_of)
        manifest = write_manifest(
            settings,
            [
                {
                    "market": snapshot.market,
                    "slug": slugify(snapshot.market),
                    "snapshot_path": f"latest/markets/{slugify(snapshot.market)}/snapshot.json",
                    "backtest_path": f"latest/markets/{slugify(snapshot.market)}/backtest.json",
                    "bias": snapshot.regime.get("bias", ""),
                    "composite": snapshot.regime.get("composite", 0.0),
                }
            ],
            as_of=args.as_of,
        )
        print(json.dumps({"snapshot": snapshot.to_dict(), "backtest": backtest.to_dict(), "paths": paths, "manifest": str(manifest)}, indent=2))
        return 0

    if args.command == "generate-all-snapshots":
        records = []
        for market_name in settings.indices:
            snapshot, _, _ = generate_market_outputs(settings, market_name, as_of=args.as_of)
            records.append(
                {
                    "market": market_name,
                    "slug": slugify(market_name),
                    "snapshot_path": f"latest/markets/{slugify(market_name)}/snapshot.json",
                    "backtest_path": f"latest/markets/{slugify(market_name)}/backtest.json",
                    "bias": snapshot.regime.get("bias", ""),
                    "composite": snapshot.regime.get("composite", 0.0),
                }
            )
        manifest = write_manifest(settings, records, args.as_of)
        print(json.dumps({"manifest": str(manifest), "markets": records}, indent=2))
        return 0

    if args.command == "run-backtest":
        _, backtest, paths = generate_market_outputs(settings, args.market, as_of=args.as_of)
        print(json.dumps({"backtest": backtest.to_dict(), "paths": paths}, indent=2))
        return 0

    if args.command == "validate-snapshots":
        checked = validate_snapshot_tree(Path(args.path))
        print(json.dumps({"validated_files": checked}, indent=2))
        return 0

    parser.error("unknown command")
    return 2
