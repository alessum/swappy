"""Command-line interface for the reproducibility workflow."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .reproduce import PROFILES, run_reproduction


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Reproduce the static and dynamical signatures of the swappy paper."
    )
    parser.add_argument(
        "--profile",
        choices=sorted(PROFILES),
        default="quick",
        help="smoke checks wiring; quick is laptop-scale; paper matches published main settings",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="output directory (default: artifacts/<profile>)",
    )
    parser.add_argument("--seed", type=int, default=241114357)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    summary = run_reproduction(args.profile, args.output, args.seed)
    print(json.dumps(summary, indent=2))
    return 0

