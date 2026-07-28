#!/usr/bin/env python3
"""Run the repository without requiring an editable installation first."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from swappy.cli import main

raise SystemExit(main())

