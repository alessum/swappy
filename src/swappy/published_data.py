"""Load and normalize the static data shipped with the original repository."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from .spectral import charge_sector_page_entropy


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
DATA_ROOT = REPOSITORY_ROOT / "data"


def load_published_static_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return cleaned Figure-2 entanglement and gap-ratio tables.

    The archived CSV files use the older Pauli-angle convention in which the
    published couplings are four times the stored values.  This loader makes
    that conversion explicit and normalizes entropy by the fixed-charge Page
    value used in the final paper.
    """

    entanglement = pd.read_csv(DATA_ROOT / "eigvec_entanglement_data" / "fifth.csv")
    gap_ratio = pd.read_csv(DATA_ROOT / "gap_ratio_data" / "first.csv")

    entanglement = entanglement.copy()
    gap_ratio = gap_ratio.copy()
    for frame in (entanglement, gap_ratio):
        frame["J_paper"] = 4.0 * frame["J"]
        frame["Jz_paper"] = 4.0 * frame["Jz"]

    entanglement["page_entropy"] = [
        charge_sector_page_entropy(
            int(row.N),
            int(round(row.N / 2 + row.magnetization)),
        )
        for row in entanglement.itertuples()
    ]
    entanglement["normalized_entanglement"] = (
        entanglement["eigvec_entanglement_mean"] / entanglement["page_entropy"]
    )
    entanglement["sem"] = entanglement["eigvec_entanglement_std"] / (
        entanglement["num_rd_instances"].clip(lower=1) ** 0.5
    )
    gap_ratio["sem"] = gap_ratio["gap_ratio_std"] / (
        gap_ratio["num_rd_instances"].clip(lower=1) ** 0.5
    )
    return entanglement, gap_ratio
