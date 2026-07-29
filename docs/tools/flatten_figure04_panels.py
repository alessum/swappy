"""Flatten the figure04 panels used by the umbrella GIF.

For each PNG under ``docs/assets/figure04_panels/`` this script:

* removes the two dashed and the one continuous concentric black circles by
  replacing dark low-saturation pixels (and their anti-alias halo) with
  white;
* converts the coloured red/blue trajectory into a uniform grey that
  matches the cloud, while keeping the trajectory's own white border and
  the surrounding grey cloud intact.

The originals are copied to ``figure04_panels/original/`` on the first run
so the transformation is reproducible from a clean source.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

PANELS_DIR = Path(__file__).resolve().parents[1] / "assets" / "figure04_panels"
BACKUP_DIR = PANELS_DIR / "original"

# Uniform grey used for the trajectory. Chosen to sit between the darker
# cloud samples (~143) and the lighter ones (~175) so the flattened
# trajectory blends into every panel without visible seams.
TARGET_GREY = np.array([170, 170, 170], dtype=np.uint8)

# Pixels darker than this (in any channel) count as "black" ink, no matter
# their chroma. The perimeter dashes of the outer dashed circle carry a
# tiny channel imbalance from the PDF renderer (RGB values around
# (18, 16, 15)) which would otherwise register as coloured; treating them
# as black here keeps them out of the trajectory halo.
BLACK_MAX = 120
# Saturation above this counts as colour (0-255 scale).
SAT_THRESHOLD = 40
# Lower brightness bound for a pixel to be treated as truly coloured. Real
# trajectory pixels always have max_c > 130; using 100 leaves a safe
# margin while excluding the near-black perimeter dashes.
COLOR_MIN_VALUE = 100
# Dilation radius applied to the black mask so anti-alias halos of the
# concentric circles are removed too.
BLACK_HALO = 2
# Dilation radius applied to the trajectory mask so the trajectory's own
# white outline (and its anti-alias fringe with the coloured core) also
# gets recoloured into the target grey.
TRAJECTORY_HALO = 8
# Any pixel with a max-minus-min channel spread above this counts as
# "still tinted" and is neutralised in the final desaturation pass.
CHROMA_TINT_THRESHOLD = 3
# Any (already neutral) grey pixel darker than this is flattened to
# TARGET_GREY so the whole cloud renders as one uniform shade. Values
# above this bound are treated as background anti-alias fringe and left
# alone, which keeps the cloud edges smooth rather than jagged.
FLATTEN_MAX = 250


def _classify(arr: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Return ``(black_mask, colored_mask)`` for the RGB image ``arr``."""

    # int32 to avoid overflow in ``(max_c - min_c) * 255`` (int16 wraps
    # for saturated reds/blues, silently flipping the sign of ``sat``).
    r = arr[..., 0].astype(np.int32)
    g = arr[..., 1].astype(np.int32)
    b = arr[..., 2].astype(np.int32)
    max_c = np.maximum(np.maximum(r, g), b)
    min_c = np.minimum(np.minimum(r, g), b)
    sat = np.where(
        max_c > 0,
        (max_c - min_c) * 255 // np.maximum(max_c, 1),
        0,
    )
    # Colour: high chroma AND bright enough to be part of the trajectory
    # (not a near-black perimeter dash with a small channel imbalance).
    colored_mask = (sat > SAT_THRESHOLD) & (max_c > COLOR_MIN_VALUE)
    # Black: any dark ink, regardless of chroma, so the coloured-looking
    # near-black perimeter dashes are still treated as circle ink.
    black_mask = max_c < BLACK_MAX
    return black_mask, colored_mask


def _process(path: Path) -> None:
    img = Image.open(path).convert("RGB")
    arr = np.array(img)
    black_mask, colored_mask = _classify(arr)

    # Grow the black mask so the anti-aliased ring around each concentric
    # circle also disappears. The dilation runs before the colour swap so
    # the extra pixels are still recognisably "not cloud".
    if BLACK_HALO > 0:
        halo = ndimage.binary_dilation(black_mask, iterations=BLACK_HALO)
        # Only sweep away halo pixels that are neither strongly coloured
        # nor part of the light cloud — i.e. the darker greys that come
        # from anti-aliasing.
        max_c = arr.max(axis=-1)
        halo_extra = halo & (~black_mask) & (~colored_mask) & (max_c < 210)
        black_mask = black_mask | halo_extra

    out = arr.copy()
    out[colored_mask] = TARGET_GREY
    out[black_mask] = np.array([255, 255, 255], dtype=np.uint8)

    # Sweep the white outline that the trajectory drew on top of the cloud
    # into the same grey. We look at pixels within TRAJECTORY_HALO of the
    # original coloured mask that are still very light (i.e. the white
    # border ring, not the surrounding cloud).
    if TRAJECTORY_HALO > 0:
        traj_zone = ndimage.binary_dilation(
            colored_mask, iterations=TRAJECTORY_HALO
        )
        current_max = out.max(axis=-1)
        border_mask = traj_zone & (~colored_mask) & (current_max >= 230)
        out[border_mask] = TARGET_GREY

    # Neutralise any residual chroma so faint pink/blue anti-alias fringes
    # around the trajectory (and the cloud's own subtle tint) become plain
    # grey. Each affected pixel keeps its own brightness so the cloud's
    # soft shading is preserved rather than flattened to TARGET_GREY.
    r_out = out[..., 0].astype(np.int32)
    g_out = out[..., 1].astype(np.int32)
    b_out = out[..., 2].astype(np.int32)
    chroma = (
        np.maximum(np.maximum(r_out, g_out), b_out)
        - np.minimum(np.minimum(r_out, g_out), b_out)
    )
    tint_mask = chroma > CHROMA_TINT_THRESHOLD
    if tint_mask.any():
        neutral = ((r_out + g_out + b_out) // 3).astype(np.uint8)
        out[..., 0] = np.where(tint_mask, neutral, out[..., 0])
        out[..., 1] = np.where(tint_mask, neutral, out[..., 1])
        out[..., 2] = np.where(tint_mask, neutral, out[..., 2])

    # Collapse every remaining grey shade to the single TARGET_GREY. We
    # keep the brightest anti-alias fringe (values above FLATTEN_MAX) so
    # the cloud outline still fades softly into the white background.
    grey_val = out[..., 0]
    flat_mask = grey_val < FLATTEN_MAX
    out[flat_mask] = TARGET_GREY

    Image.fromarray(out).save(path)


def main() -> None:
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    for src in sorted(PANELS_DIR.glob("*.png")):
        if src.parent != PANELS_DIR:
            continue
        backup = BACKUP_DIR / src.name
        if not backup.exists():
            shutil.copy2(src, backup)
        # Always process from the backup so re-runs are idempotent.
        shutil.copy2(backup, src)
        _process(src)
        print(f"flattened {src.name}")


if __name__ == "__main__":
    main()
