"""Command-line interface for the reproducibility workflow."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from .reproduce import PROFILES, run_reproduction


def execute_notebooks() -> None:
    """Execute every walkthrough notebook in place."""

    try:
        import nbformat
        from nbclient import NotebookClient
    except ImportError as error:
        raise SystemExit('Install notebook support first with "make setup".') from error

    root = Path(__file__).resolve().parents[2]
    os.environ.setdefault("PYTHONPATH", str(root / "src"))
    os.environ.setdefault("MPLCONFIGDIR", str(root / ".cache" / "matplotlib"))

    for notebook_path in sorted((root / "notebooks").glob("*.ipynb")):
        notebook = nbformat.read(notebook_path, as_version=4)
        NotebookClient(
            notebook,
            timeout=600,
            kernel_name="python3",
            resources={"metadata": {"path": str(root)}},
        ).execute()
        nbformat.write(notebook, notebook_path)
        print(f"executed {notebook_path.relative_to(root)}")


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
    parser.add_argument(
        "--notebooks",
        action="store_true",
        help="execute and save both walkthrough notebooks instead of a profile",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.notebooks:
        execute_notebooks()
        return 0
    summary = run_reproduction(args.profile, args.output, args.seed)
    print(json.dumps(summary, indent=2))
    return 0
