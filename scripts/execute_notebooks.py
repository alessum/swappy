#!/usr/bin/env python3
"""Execute every walkthrough notebook in place and fail on the first error."""

from pathlib import Path
import os

import nbformat
from nbclient import NotebookClient


ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("PYTHONPATH", str(ROOT / "src"))
os.environ.setdefault("MPLCONFIGDIR", str(ROOT / ".cache" / "matplotlib"))

for notebook_path in sorted((ROOT / "notebooks").glob("*.ipynb")):
    notebook = nbformat.read(notebook_path, as_version=4)
    client = NotebookClient(
        notebook,
        timeout=600,
        kernel_name="python3",
        resources={"metadata": {"path": str(ROOT)}},
    )
    client.execute()
    nbformat.write(notebook, notebook_path)
    print(f"executed {notebook_path.relative_to(ROOT)}")

