"""Generate the high-level umbrella analogy used in the README.

The phase and magnitude profiles are qualitative fits to the published N=20
trajectories. The circuit is shown at discrete R_n samples, while the umbrella
interpolates continuously between them. Blue-to-red encodes time only.
"""

from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageColor, ImageDraw, ImageFont


WIDTH, HEIGHT = 960, 540
SCALE = 2
# Render the physical motion at 25 fps. Every regime unfolds in four phases:
# the umbrella opens from a fixed vertical closed pose (OPEN_FRAMES), plays
# its regime-specific motion (MOTION_FRAMES), holds at the final state
# (HOLD_FRAMES) so the viewer can read it, then closes back down to the same
# fixed pose (CLOSE_FRAMES). The closed pose is shared across regimes so the
# transition between two regimes is a smooth open/close gesture rather than
# a jump between two arbitrarily different geometries. The downward-push
# handle slides smoothly through the closing + opening pair, tracking the
# per-regime target push force across the transition.
OPEN_FRAMES = 12
MOTION_FRAMES = 54
HOLD_FRAMES = 10
CLOSE_FRAMES = 14
FRAME_COUNT = OPEN_FRAMES + MOTION_FRAMES + HOLD_FRAMES + CLOSE_FRAMES
FRAME_DURATION_MS = 40
CIRCUIT_STEP_COUNT = 20
UMBRELLA_SHAFT_LENGTH = 145.0
# Length of the sand-auger anchor measured in the same world units as the
# shaft. The anchor is a RIGID extension of the pole (shaft and auger form
# one rigid body), so it tilts with the shaft; only the cone piercing tip
# at the very bottom of the auger is the pivot of the motion, and that
# cone tip is the point pinned to the fixed vertical axis.
UMBRELLA_AUGER_LENGTH = 30.0
SAND_SURFACE_Y = 334
# INITIAL_PIVOT_Y is the initial screen y of the auger cone tip (the pivot
# of the rigid pole). It sits ~12 px below the sand surface -- roughly one
# cone-length of penetration -- so the heavy-duty auger starts with just
# its piercing tip biting into the sand and the wing-bearing cylinder
# still fully visible above the sand line. The |R|-driven "deepening"
# then pushes the whole rigid pole progressively deeper along the fixed
# axis over the course of each regime.
INITIAL_PIVOT_Y = 346
INITIAL_PIVOT_CLEARANCE = SAND_SURFACE_Y - INITIAL_PIVOT_Y
MAX_UMBRELLA_DROP_FRACTION = 1.0 / 3.0

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "assets" / "figure1.gif"
# High-resolution, high-FPS companion GIF. Renders at the internal 2x raster
# (1920x1080) with double the phase frame counts and half the per-frame
# duration, so the total wall-clock length matches the standard GIF but the
# motion plays at 50 fps instead of 25 fps.
OUTPUT_HR = ROOT / "assets" / "figure1_hr.gif"
HR_FRAME_MULTIPLIER = 2
HR_FRAME_DURATION_MS = 20

# LaTeX-style typography: prefer Latin Modern Roman (the modern OTF port of
# Computer Modern that TeX uses by default), then CM Unicode, then any
# Linux-packaged Latin Modern, and finally the original sans candidates so the
# script still renders on machines without a TeX distribution installed.
FONT_REGULAR_CANDIDATES = (
    "/usr/local/texlive/2025/texmf-dist/fonts/opentype/public/lm/lmroman10-regular.otf",
    "/usr/local/texlive/2024/texmf-dist/fonts/opentype/public/lm/lmroman10-regular.otf",
    "/usr/local/texlive/2023/texmf-dist/fonts/opentype/public/lm/lmroman10-regular.otf",
    "/Library/TeX/texbin/../../../texlive/2025/texmf-dist/fonts/opentype/public/lm/lmroman10-regular.otf",
    "/usr/local/texlive/2025/texmf-dist/fonts/opentype/public/cm-unicode/cmunrm.otf",
    "/usr/share/texmf/fonts/opentype/public/lm/lmroman10-regular.otf",
    "/usr/share/texlive/texmf-dist/fonts/opentype/public/lm/lmroman10-regular.otf",
    "/usr/share/fonts/opentype/lmodern/lmroman10-regular.otf",
    "/usr/share/fonts/truetype/lmodern/lmroman10-regular.ttf",
    "/System/Library/Fonts/Supplemental/Arial.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
    "C:/Windows/Fonts/arial.ttf",
)
# Bold candidates: LM Roman ships optical-size variants. Smaller design sizes
# (lmroman8-bold) have proportionally thicker strokes so they read as visibly
# bold at pill / subtitle / body sizes. At the 26pt header, however, the
# 10pt-designed cut sits better than the chunkier 8pt cut, so the two lists
# below are kept separate and selected in `font()` based on the target size.
FONT_BOLD_CANDIDATES = (
    "/usr/local/texlive/2025/texmf-dist/fonts/opentype/public/lm/lmroman8-bold.otf",
    "/usr/local/texlive/2024/texmf-dist/fonts/opentype/public/lm/lmroman8-bold.otf",
    "/usr/local/texlive/2023/texmf-dist/fonts/opentype/public/lm/lmroman8-bold.otf",
    "/Library/TeX/texbin/../../../texlive/2025/texmf-dist/fonts/opentype/public/lm/lmroman8-bold.otf",
    "/usr/local/texlive/2025/texmf-dist/fonts/opentype/public/cm-unicode/cmunbx.otf",
    "/usr/share/texmf/fonts/opentype/public/lm/lmroman8-bold.otf",
    "/usr/share/texlive/texmf-dist/fonts/opentype/public/lm/lmroman8-bold.otf",
    "/usr/share/fonts/opentype/lmodern/lmroman8-bold.otf",
    "/usr/share/fonts/truetype/lmodern/lmroman8-bold.ttf",
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
)
FONT_BOLD_LARGE_CANDIDATES = (
    "/usr/local/texlive/2025/texmf-dist/fonts/opentype/public/lm/lmroman10-bold.otf",
    "/usr/local/texlive/2024/texmf-dist/fonts/opentype/public/lm/lmroman10-bold.otf",
    "/usr/local/texlive/2023/texmf-dist/fonts/opentype/public/lm/lmroman10-bold.otf",
    "/Library/TeX/texbin/../../../texlive/2025/texmf-dist/fonts/opentype/public/lm/lmroman10-bold.otf",
    "/usr/local/texlive/2025/texmf-dist/fonts/opentype/public/cm-unicode/cmunbx.otf",
    "/usr/share/texmf/fonts/opentype/public/lm/lmroman10-bold.otf",
    "/usr/share/texlive/texmf-dist/fonts/opentype/public/lm/lmroman10-bold.otf",
    "/usr/share/fonts/opentype/lmodern/lmroman10-bold.otf",
    "/usr/share/fonts/truetype/lmodern/lmroman10-bold.ttf",
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
)
# Bold sizes at or above this cutoff use the 10pt-designed cut; smaller sizes
# use the 8pt-designed cut so pill labels / subtitles read as clearly bold.
BOLD_LARGE_SIZE_THRESHOLD = 20

INK = "#18324A"
# INK_PROGRESS is a slightly darker shade of INK used to fill the footer
# loading bar left-to-right as the current regime plays through its
# opening + motion + hold + closing phases. Keeping the same hue lets the
# progress read as a subtle "tint" of the bar rather than a new colour.
INK_PROGRESS = "#0C1D30"
INK_PROGRESS_RGB = ImageColor.getrgb(INK_PROGRESS)
MUTED = "#64748B"
PAPER = "#FBFAF6"
SKY = "#EAF5F6"
SAND = "#E8CF91"
SAND_DARK = "#B88B45"
# BLUE and CORAL match the paper's canonical darkblue/darkred (preamble.tex)
# and are the endpoints of the R(t) time-colour ramp in figure04.
CORAL = "#822522"
GOLD = "#F2B84B"
# FIREBRICK is the CSS "firebrick" red used for the NEAR SWAP pill in
# docs/slider.html. It is intentionally redder (and "hotter") than CORAL
# so the NEAR SWAP footer badge reads as the strongest regime.
FIREBRICK = "#B22222"
BLUE = "#485DB5"
PURPLE = "#7656A7"
# PALM: a muted leaf green completing the umbrella's four-colour set. Chosen
# to sit at a similar tonal weight to CORAL and BLUE (mid saturation,
# medium value) so no single panel visually dominates its neighbours, and
# to read as a natural "beach umbrella" fourth stripe alongside the
# yellow / red / blue triad.
PALM = "#4E8B4A"
PALE_BLUE = "#DCE8F7"


def _darken(hex_color: str, factor: float) -> str:
    """Scale ``hex_color`` toward black by ``factor`` (0 = black, 1 = same)."""
    r, g, b = ImageColor.getrgb(hex_color)[:3]
    return "#{:02X}{:02X}{:02X}".format(
        int(round(r * factor)),
        int(round(g * factor)),
        int(round(b * factor)),
    )


# Side-view shading of the canopy. The side view shows the convex outer top
# of the near (front) half of the dome, but the far (back) half exposes its
# concave underside to the camera -- the surface a person standing under
# the umbrella would look up at. Those back-facing sectors are filled with
# slightly darker versions of the four canopy colours so the closed dome
# reads with a subtle self-shadow separating the sunlit outer top from the
# shaded inner bowl.
CANOPY_INNER_DARKEN = 0.80
GOLD_INNER = _darken(GOLD, CANOPY_INNER_DARKEN)
CORAL_INNER = _darken(CORAL, CANOPY_INNER_DARKEN)
BLUE_INNER = _darken(BLUE, CANOPY_INNER_DARKEN)
PALM_INNER = _darken(PALM, CANOPY_INNER_DARKEN)
# Muted, sun-bleached beach-umbrella variants of two of the canopy colours.
# When the palette bug was still active these tonalities briefly appeared on
# the umbrella (the frame-0 palette was quantising GOLD -> a warm sand tan
# and BLUE -> a dusty overcast blue), and they read very naturally against
# the beach background, so they're now used as the canonical umbrella
# palette in place of the more saturated GOLD/BLUE hues -- keeping PALM
# (green) and CORAL (red) unchanged as the other two tonalities.
CANOPY_TAN = "#BC9160"
CANOPY_DUSTY = "#6475BF"
CANOPY_TAN_INNER = _darken(CANOPY_TAN, CANOPY_INNER_DARKEN)
CANOPY_DUSTY_INNER = _darken(CANOPY_DUSTY, CANOPY_INNER_DARKEN)
# The CIRCULAR MOMENT panel on the right of the animation uses the actual
# per-regime panels of the paper's figure04 as its backdrop, so the grey
# disorder-realization cloud shown during each regime is the very same one
# published in the paper rather than a synthesised approximation.
FIGURE04_PDF_CANDIDATES = (
    Path(__file__).resolve().parents[2] / "figures" / "figure04.pdf",
    Path(__file__).resolve().parents[2]
    / "arxiv_resubmission"
    / "figures"
    / "figure04.pdf",
)
FIGURE04_PANELS_DIR = Path(__file__).resolve().parent / "assets" / "figure04_panels"
# Crop side length relative to the dashed unit circle radius: 2 * r * MARGIN.
# A tight margin keeps only the circle (plus a hair of breathing room), so
# the paper's "CASE:" panel label and axis labels stay outside the crop and
# do not clutter the animation's own overlay.
FIGURE04_CROP_MARGIN = 1.03
# Per-panel dashed-circle geometry in the 400-DPI raster of figure04
# (paper layout is a 2x2 subplot grid, so these values are stable across
# regenerations of the figure). Each regime is keyed by the paper marker
# already stored on it, so the panel binding uses the same source of truth
# as the regime table.
FIGURE04_PANELS = {
    "circle":   {"stem": "localized", "cx": 412,  "cy": 372,  "r": 308},
    "triangle": {"stem": "ergodic",   "cx": 1106, "cy": 372,  "r": 308},
    "square":   {"stem": "swappy",    "cx": 412,  "cy": 1094, "r": 308},
    "star":     {"stem": "near_swap", "cx": 1106, "cy": 1094, "r": 308},
}


# Data-inspired anchors (progress, |R|, unwrapped arg R) from figure04.pdf.
# They intentionally retain only the trajectories' qualitative geometry; the
# original numerical N=20 arrays are not present in the repository.
LOCALIZED_MOMENT_SAMPLES = (
    (0.00, 1.000, 0.029),
    (0.25, 0.995, 0.050),
    (0.50, 0.990, 0.080),
    (0.75, 0.985, 0.102),
    (1.00, 0.980, 0.118),
)
ERGODIC_MOMENT_SAMPLES = (
    (0.00, 1.000, 0.000),
    (0.10, 0.952, -0.107),
    (0.20, 0.848, -0.086),
    (0.30, 0.799, -0.101),
    (0.40, 0.712, -0.113),
    (0.50, 0.625, -0.117),
    (0.60, 0.524, -0.140),
    (0.70, 0.430, -0.154),
    (0.80, 0.327, -0.158),
    (0.90, 0.136, -0.165),
    (1.00, 0.030, -0.165),
)
# SWAPPY trajectory: qualitative fit to the paper's figure04 SWAPPY
# panel -- an aggressively-contracting clockwise spiral that plunges
# from the unit circle toward the origin while accumulating drift. The
# radial contraction is front-loaded (|R| drops by more than half in
# the first 30% of the motion) and the total angular sweep is ~1.5
# clockwise turns, matching the paper's mean R(t) shape.
SWAPPY_MOMENT_SAMPLES = (
    (0.00, 1.000, 0.020),
    (0.15, 0.770, -0.990),
    (0.30, 0.430, -2.210),
    (0.45, 0.375, -3.590),
    (0.60, 0.237, -4.350),
    (0.75, 0.170, -6.170),
    (0.90, 0.146, -7.430),
    (0.97, 0.130, -9.180),
    (1.00, 0.020, -9.180),
)
# NEAR SWAP orbit: the 20 discrete R_n samples wind 1.75 clockwise
# turns around the origin at a nearly fixed |R|, so the umbrella
# precesses 1.75 full revolutions during the regime's motion phase.
_NEAR_SWAP_TURNS = 1.75
NEAR_SWAP_MOMENT_SAMPLES = tuple(
    (step / 20.0, 0.990, -_NEAR_SWAP_TURNS * 2.0 * math.pi * step / 20.0)
    for step in range(21)
)


REGIMES = (
    {
        "name": "LOCALIZED",
        "description": "small phase wander; nearly fixed |R|",
        "tilt_deg": 8.0,
        "moment_samples": LOCALIZED_MOMENT_SAMPLES,
        "downward_push": 0.10,
        "descent_gamma": 1.0,
        "descent_boost": 1.0,
        # Localized shows "nearly fixed |R|" as a barely-moving umbrella.
        # We deliberately avoid any rotational tremor here: even with the
        # counter-spin applied to the canopy, oscillating the shaft's lean
        # direction changes which sectors face the viewer and reads as an
        # unwanted spin. A small tilt (magnitude) tremor is enough to keep
        # the umbrella feeling "alive" without visible rotation.
        "wobble_rot_amp": 0.0,
        "wobble_tilt_amp": 1.7,
        "wobble_tremor_amp": 0.0,
        "wobble_tremor_freq": 0.0,
        # Localized |R| barely moves, so the flutter must not fade with the
        # motion envelope; keep it alive right up to the held final frame.
        "wobble_persist": True,
        "color": MUTED,
        # Paper marker: \ding{108} -- filled circle.
        "marker": "circle",
    },
    {
        "name": "ERGODIC",
        "description": "radial contraction; negligible drift",
        "tilt_deg": 8.0,
        "moment_samples": ERGODIC_MOMENT_SAMPLES,
        "downward_push": 0.95,
        "descent_gamma": 1.0,
        "descent_boost": 1.0,
        "wobble_rot_amp": 0.33,
        "wobble_tilt_amp": 1.9,
        "color": BLUE,
        # Paper marker: \filledtriangle -- upward filled triangle.
        "marker": "triangle",
    },
    {
        "name": "SWAPPY",
        "description": "clockwise spiral; drift plus contraction",
        "tilt_deg": 20.0,
        "moment_samples": SWAPPY_MOMENT_SAMPLES,
        "downward_push": 0.65,
        # Front-loaded descent: swappy plunges into the sand well before
        # ergodic reaches half-drop. Boost > 1 makes the final resting depth
        # visibly deeper than the ergodic one.
        "descent_gamma": 0.55,
        "descent_boost": 1.20,
        "wobble_rot_amp": 0.0,
        "wobble_tilt_amp": 0.0,
        "color": CORAL,
        # Paper marker: $\blacksquare$ -- filled square.
        "marker": "square",
    },
    {
        "name": "NEAR SWAP",
        "description": "20-point orbit; nearly fixed |R|",
        "tilt_deg": 32.0,
        "moment_samples": NEAR_SWAP_MOMENT_SAMPLES,
        "downward_push": 0.10,
        "descent_gamma": 1.0,
        "descent_boost": 1.0,
        "wobble_rot_amp": 0.0,
        "wobble_tilt_amp": 0.0,
        "color": FIREBRICK,
        # Paper marker: $\bigstar$ -- five-pointed filled star.
        "marker": "star",
    },
)
MIN_RELATIVE_MOMENT_RADIUS = min(
    float(sample[1]) / float(regime["moment_samples"][0][1])
    for regime in REGIMES
    for sample in regime["moment_samples"]
)


def sc(value: float) -> int:
    return round(value * SCALE)


def point(x: float, y: float) -> tuple[int, int]:
    return sc(x), sc(y)


def box(x0: float, y0: float, x1: float, y1: float) -> tuple[int, int, int, int]:
    return sc(x0), sc(y0), sc(x1), sc(y1)


def font(size: int, *, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    if bold:
        candidates = (
            FONT_BOLD_LARGE_CANDIDATES
            if size >= BOLD_LARGE_SIZE_THRESHOLD
            else FONT_BOLD_CANDIDATES
        )
    else:
        candidates = FONT_REGULAR_CANDIDATES
    for candidate in candidates:
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, sc(size))
    return ImageFont.load_default(size=sc(size))


def ease(value: float) -> float:
    return value * value * (3.0 - 2.0 * value)


def monotone_tangents(
    samples: tuple[tuple[float, float, float], ...],
    component: int,
) -> list[float]:
    """Return shape-preserving PCHIP tangents for one sampled component."""

    coordinates = [float(sample[0]) for sample in samples]
    values = [float(sample[component]) for sample in samples]
    if len(samples) == 2:
        slope = (values[1] - values[0]) / (coordinates[1] - coordinates[0])
        return [slope, slope]

    spans = [
        coordinates[index + 1] - coordinates[index]
        for index in range(len(samples) - 1)
    ]
    slopes = [
        (values[index + 1] - values[index]) / spans[index]
        for index in range(len(samples) - 1)
    ]
    tangents = [0.0] * len(samples)

    for index in range(1, len(samples) - 1):
        left_slope = slopes[index - 1]
        right_slope = slopes[index]
        if left_slope == 0.0 or right_slope == 0.0 or left_slope * right_slope < 0.0:
            tangents[index] = 0.0
            continue
        left_span = spans[index - 1]
        right_span = spans[index]
        left_weight = 2.0 * right_span + left_span
        right_weight = right_span + 2.0 * left_span
        tangents[index] = (left_weight + right_weight) / (
            left_weight / left_slope + right_weight / right_slope
        )

    first = (
        (2.0 * spans[0] + spans[1]) * slopes[0] - spans[0] * slopes[1]
    ) / (spans[0] + spans[1])
    if first * slopes[0] <= 0.0:
        first = 0.0
    elif slopes[0] * slopes[1] < 0.0 and abs(first) > abs(3.0 * slopes[0]):
        first = 3.0 * slopes[0]
    tangents[0] = first

    last = (
        (2.0 * spans[-1] + spans[-2]) * slopes[-1]
        - spans[-1] * slopes[-2]
    ) / (spans[-1] + spans[-2])
    if last * slopes[-1] <= 0.0:
        last = 0.0
    elif slopes[-1] * slopes[-2] < 0.0 and abs(last) > abs(3.0 * slopes[-1]):
        last = 3.0 * slopes[-1]
    tangents[-1] = last
    return tangents


def smooth_component(
    samples: tuple[tuple[float, float, float], ...],
    component: int,
    left_index: int,
    amount: float,
    tangents: list[float],
) -> float:
    """Evaluate one cubic Hermite segment of a sampled trajectory."""

    right_index = left_index + 1
    left_progress = float(samples[left_index][0])
    right_progress = float(samples[right_index][0])
    span = right_progress - left_progress
    left_value = float(samples[left_index][component])
    right_value = float(samples[right_index][component])
    amount_squared = amount * amount
    amount_cubed = amount_squared * amount
    return (
        (2.0 * amount_cubed - 3.0 * amount_squared + 1.0) * left_value
        + (amount_cubed - 2.0 * amount_squared + amount)
        * span
        * tangents[left_index]
        + (-2.0 * amount_cubed + 3.0 * amount_squared) * right_value
        + (amount_cubed - amount_squared) * span * tangents[right_index]
    )


def mix(first: str, second: str, amount: float) -> tuple[int, int, int]:
    a = tuple(int(first[i : i + 2], 16) for i in (1, 3, 5))
    b = tuple(int(second[i : i + 2], 16) for i in (1, 3, 5))
    return tuple(round(x + (y - x) * amount) for x, y in zip(a, b))


def dashed_circle(
    draw: ImageDraw.ImageDraw,
    center: tuple[float, float],
    radius: float,
    *,
    fill: str,
    width: int,
) -> None:
    cx, cy = center
    for degree in range(0, 360, 8):
        start = math.radians(degree)
        stop = math.radians(degree + 4)
        draw.line(
            [
                point(cx + radius * math.cos(start), cy + radius * math.sin(start)),
                point(cx + radius * math.cos(stop), cy + radius * math.sin(stop)),
            ],
            fill=fill,
            width=sc(width),
        )


def arrow_head(
    draw: ImageDraw.ImageDraw,
    tip: tuple[float, float],
    angle: float,
    *,
    fill: str,
    size: float = 9,
) -> None:
    tx, ty = tip
    left = (
        tx - size * math.cos(angle - 0.55),
        ty - size * math.sin(angle - 0.55),
    )
    right = (
        tx - size * math.cos(angle + 0.55),
        ty - size * math.sin(angle + 0.55),
    )
    draw.polygon([point(tx, ty), point(*left), point(*right)], fill=fill)


def draw_header(draw: ImageDraw.ImageDraw) -> None:
    draw.text(point(48, 30), "THE SWAPPY UMBRELLA", fill=INK, font=font(26, bold=True))
    draw.text(
        point(48, 67),
        "precession = arg R(t)",
        fill=CORAL,
        font=font(14, bold=True),
    )
    draw.text(point(229, 67), "•", fill=MUTED, font=font(14, bold=True))
    draw.text(
        point(249, 67),
        "height tracks |R(t)|",
        fill=BLUE,
        font=font(14, bold=True),
    )


def draw_sand(draw: ImageDraw.ImageDraw) -> None:
    # The beach spans the full canvas -- edge to edge horizontally and all
    # the way down to the bottom margin -- so it reads as a continuous
    # background. The CIRCULAR MOMENT panel and the footer/loading bar are
    # drawn on top afterwards and cover their own footprints, so the sand
    # is only visible around them.
    #
    # The wave-line phase stays anchored at x=30 so it remains consistent
    # with the `beach_horizon` calc in `draw_umbrella`, which uses the same
    # (x - 30) / 24 argument.
    draw.rectangle(box(0, 334, WIDTH, HEIGHT), fill=SAND)
    wave = []
    for x in range(0, WIDTH + 1, 6):
        y = 334 + 4 * math.sin((x - 30) / 24)
        wave.append(point(x, y))
    draw.line(wave, fill=SAND_DARK, width=sc(2))

    # Original speckle pattern preserved verbatim inside the historical
    # sand band (y = 352..443, x = 8..951). Grain positions are the same
    # ones that existed before the sand rectangle was deepened, so this
    # band doesn't visually shift or "duplicate" between old and new
    # renders.
    for i in range(115):
        x = 8 + ((i * 83) % 944)
        y = 352 + ((i * 47) % 92)
        radius = 1 + (i % 2)
        draw.ellipse(
            box(x - radius, y - radius, x + radius, y + radius),
            fill=mix(SAND_DARK, PAPER, 0.35),
        )

    # Extra speckle populating ONLY the newly extended vertical band, from
    # just below the original grain band (y >= 444) down to the canvas
    # floor. Uses different prime offsets / multipliers than the loop
    # above so the added grains interleave naturally with the historical
    # pattern instead of landing on the same columns. Count is chosen to
    # match the original density (~115 grains over 944 x 92 -> ~120
    # grains over 944 x 96).
    for i in range(120):
        x = 12 + ((i * 89) % 936)
        y = 444 + ((i * 53) % 96)
        radius = 1 + (i % 2)
        draw.ellipse(
            box(x - radius, y - radius, x + radius, y + radius),
            fill=mix(SAND_DARK, PAPER, 0.35),
        )

    disorder_label = "STRONG DISORDER"
    disorder_font = font(12, bold=True)
    disorder_width = draw.textlength(disorder_label, font=disorder_font) / SCALE
    disorder_pad_x = 16
    disorder_left = 54
    disorder_top = 416
    disorder_bottom = 448
    disorder_right = disorder_left + disorder_width + 2 * disorder_pad_x
    draw.rounded_rectangle(
        box(disorder_left, disorder_top, disorder_right, disorder_bottom),
        radius=sc(14),
        fill="#F7EAC8",
        outline=SAND_DARK,
        width=sc(1),
    )
    draw.text(
        point(
            (disorder_left + disorder_right) / 2,
            (disorder_top + disorder_bottom) / 2,
        ),
        disorder_label,
        fill=INK,
        font=disorder_font,
        anchor="mm",
    )


def draw_umbrella(
    draw: ImageDraw.ImageDraw,
    *,
    rotation: float,
    tilt_deg: float,
    moment_radius: float,
    tip_depth: float,
    push: float,
    show_rotation: bool,
    show_downward_push: bool,
    canopy_scale: float = 1.0,
) -> None:
    drill_x, surface_y = 269, SAND_SURFACE_Y
    tilt = math.radians(tilt_deg)

    # Three-dimensional rigid-body geometry with an orthographic side
    # projection. The pole is a single rigid body: the shaft (upper part)
    # and the sand-auger anchor (lower part) share one axis and precess
    # together. The pivot of the motion is the auger's very cone tip: it
    # sits on the fixed vertical axis (world x = z = 0) and its y is
    # driven ONLY by ``tip_depth`` -- the |R|-driven "deepening" that
    # screws the anchor further into the sand. Rotation (precession) and
    # tilt (nutation / wobble) rotate the whole pole about that pivot
    # without ever moving it, so any oscillation keeps the anchor's cone
    # tip perfectly steady while the rest of the anchor rigidly follows
    # the shaft.
    #
    # The precession arrow drawn above the umbrella advertises a CLOCKWISE
    # sweep viewed from above (see draw_precession_arc). The physics data
    # feeds ``rotation`` = arg R, which decreases (goes negative) for the
    # clockwise-in-the-complex-plane regimes. With the naive mapping
    # sin(rotation) -> world z, a decreasing arg R would move the crown
    # 3 -> 12 -> 9 -> 6 o'clock from above (COUNTER-clockwise), the wrong
    # direction. Negating the geometric angle flips that to 3 -> 6 -> 9
    # -> 12 o'clock (clockwise), matching the arrow. The raw ``rotation``
    # is preserved for the arg R readout so the pill still shows the
    # unmodified data value.
    precession_angle = -rotation
    shaft_length = UMBRELLA_SHAFT_LENGTH
    auger_length = UMBRELLA_AUGER_LENGTH
    axis = (
        math.sin(tilt) * math.cos(precession_angle),
        math.cos(tilt),
        math.sin(tilt) * math.sin(precession_angle),
    )
    # Pivot = cone tip = the very peak of the anchor. Pinned to the fixed
    # axis; only ``tip_depth`` (deepening) shifts it, straight down.
    pivot_world = (
        0.0,
        INITIAL_PIVOT_CLEARANCE - tip_depth,
        0.0,
    )
    # Shaft/auger junction sits one auger-length up the pole from the pivot.
    tip_world = (
        pivot_world[0] + auger_length * axis[0],
        pivot_world[1] + auger_length * axis[1],
        pivot_world[2] + auger_length * axis[2],
    )
    # Crown of the shaft (canopy attachment) sits one shaft-length above
    # the shaft/auger junction along the same axis.
    canopy_world = (
        tip_world[0] + shaft_length * axis[0],
        tip_world[1] + shaft_length * axis[1],
        tip_world[2] + shaft_length * axis[2],
    )

    def project(world: tuple[float, float, float]) -> tuple[float, float]:
        x_coord, y_coord, _ = world
        return drill_x + x_coord, surface_y - y_coord

    pivot_x, pivot_y = project(pivot_world)
    tip_x, tip_y = project(tip_world)
    canopy_x, canopy_y = project(canopy_world)

    # These orthonormal vectors span the plane perpendicular to the shaft.
    # Projecting the resulting circle gives the correct changing ellipse as
    # the umbrella precesses into and out of the page. They are built from
    # the same ``precession_angle`` as ``axis`` so the rim stays truly
    # perpendicular to the (flipped-direction) shaft.
    azimuth_basis = (-math.sin(precession_angle), 0.0, math.cos(precession_angle))
    tilt_basis = (
        math.cos(tilt) * math.cos(precession_angle),
        -math.sin(tilt),
        math.cos(tilt) * math.sin(precession_angle),
    )
    # `canopy_scale` continuously blends between a closed (0 -> ribs folded
    # parallel to the shaft, no radial extent) and a fully deployed (1 ->
    # ribs perpendicular to the shaft with a slight dome tilt) canopy. The
    # ribs pivot around the crown (top of the shaft) at a fixed
    # `rib_length`, exactly like the ribs of a real umbrella: they rotate
    # down toward the pole rather than shrinking radially, so the visible
    # length of every rib is preserved across the fold.
    #
    # `rib_length` and the maximum pivot angle `rib_open_angle_max` are
    # chosen so that the fully-open canopy retains its familiar visual
    # (~90 units radial extent with a ~45-unit dome drop below the crown).
    # At any intermediate opening the two Pythagorean legs sum to the same
    # squared length, so the rib meridians never lengthen or shorten
    # during the animation.
    clamped_canopy_scale = max(0.0, min(1.0, canopy_scale))
    open_rib_horizontal = 90.0
    open_dome_drop = 45.0
    rib_length = math.hypot(open_rib_horizontal, open_dome_drop)
    rib_open_angle_max = math.atan2(open_rib_horizontal, open_dome_drop)
    rib_open_angle = rib_open_angle_max * clamped_canopy_scale
    rib_radial_extent = rib_length * math.sin(rib_open_angle)
    rib_axial_extent = rib_length * math.cos(rib_open_angle)

    def canopy_world_point(angle: float, t: float = 1.0) -> tuple[float, float, float]:
        # Counter-spin the sector parameterisation by the precession angle
        # so the canopy's coloured sectors stay world-fixed as the shaft
        # precesses (arg R). Without this, the sectors would rigidly follow
        # the shaft and the umbrella would visibly rotate around its own
        # axis -- an unwanted "spin" on top of the intended precession. We
        # use ``precession_angle`` (not the raw ``rotation``) here so the
        # counter-spin exactly cancels the intrinsic spin of the (flipped-
        # direction) azimuth/tilt basis.
        effective_angle = angle + precession_angle
        radial = tuple(
            math.cos(effective_angle) * azimuth_basis[index]
            + math.sin(effective_angle) * tilt_basis[index]
            for index in range(3)
        )
        # Two-frequency scallop, both keyed off `angle` (not
        # `effective_angle`) so the rim shape stays locked to the panels
        # as the shaft precesses:
        #   * `broad`  peaks at each panel midpoint (theta = (2k+1) * pi/8)
        #     and models the wide U-shaped sag between ribs.
        #   * `narrow` peaks sharply at each rib (theta = k * pi/4) and
        #     models the small pointed fabric tab that hangs from every
        #     rib tip. Raising cos^2 to the 8th power narrows the peak so
        #     the rim between the tab and the broad scallop lifts back up,
        #     reproducing the wavy shape of a real beach umbrella rim.
        broad = 0.5 * (1.0 - math.cos(8 * angle))
        narrow = (0.5 * (1.0 + math.cos(8 * angle))) ** 8
        radial_scale = 1.0 + 0.15 * broad + 0.03 * narrow
        # The scalloped rim sag is a decoration of a fully deployed canopy,
        # so it fades with `canopy_scale` -- otherwise the "closed" umbrella
        # would still show hanging rib tabs at radius 0.
        axial_drop = (14.0 * broad + 8.0 * narrow) * clamped_canopy_scale
        # Cambered dome profile in the (radial, axial) plane. At t=0 we
        # are at the apex (top of the shaft) and at t=1 we are at the rim
        # tip for the given angle. The sinusoidal spacing
        #   radial_amount = sin(pi/2 * t)
        #   axial_amount  = 1 - cos(pi/2 * t)
        # traces a quarter-ellipse rather than a straight line, so the
        # fabric bulges outward radially quickly and only starts dropping
        # toward the rim once it's already almost all the way out. The
        # net effect is a convex, cambered canopy instead of a flat cone.
        phi = 0.5 * math.pi * t
        radial_amount = math.sin(phi)
        axial_amount = 1.0 - math.cos(phi)
        rim_radial_full = rib_radial_extent * radial_scale
        rim_axial_full = rib_axial_extent + axial_drop
        return tuple(
            canopy_world[index]
            + rim_radial_full * radial_amount * radial[index]
            - rim_axial_full * axial_amount * axis[index]
            for index in range(3)
        )

    def canopy_point(angle: float, t: float = 1.0) -> tuple[int, int]:
        return point(*project(canopy_world_point(angle, t)))

    if tip_world[1] < 0.0 < canopy_world[1]:
        crossing = -tip_world[1] / (canopy_world[1] - tip_world[1])
        surface_world = tuple(
            tip_world[index]
            + crossing * (canopy_world[index] - tip_world[index])
            for index in range(3)
        )
    else:
        surface_world = (0.0, 0.0, 0.0)
    surface_x, _ = project(surface_world)

    # The shadow is an ellipse whose centre moves only left/right. Clip its
    # upper portion against the wavy beach horizon so no shadow enters the sky.
    light_horizontal = -0.28
    shaft_shadow_x = canopy_world[0] + light_horizontal * canopy_world[1]
    shadow_center = (surface_x + drill_x + shaft_shadow_x) / 2.0
    # The cast shadow contracts with the deployed canopy so the closed
    # umbrella casts only a small pool around the tip.
    shadow_radius_x = 47.0 * clamped_canopy_scale
    shadow_radius_y = 14.0 * clamped_canopy_scale
    shadow_center = max(
        38.0 + shadow_radius_x,
        min(488.0 - shadow_radius_x, shadow_center),
    )
    shadow_center_y = surface_y + 4
    lower_edge: list[tuple[float, float]] = []
    clipped_edge: list[tuple[float, float]] = []
    if shadow_radius_x > 0.5 and shadow_radius_y > 0.5:
        for step in range(121):
            x_coord = shadow_center - shadow_radius_x + 2 * shadow_radius_x * step / 120
            normalized_x = (x_coord - shadow_center) / shadow_radius_x
            vertical_radius = shadow_radius_y * math.sqrt(max(0.0, 1.0 - normalized_x**2))
            ellipse_top = shadow_center_y - vertical_radius
            ellipse_bottom = shadow_center_y + vertical_radius
            beach_horizon = surface_y + 4 * math.sin((x_coord - 30) / 24)
            visible_top = max(ellipse_top, beach_horizon)
            if ellipse_bottom >= visible_top:
                lower_edge.append((x_coord, ellipse_bottom))
                clipped_edge.append((x_coord, visible_top))
    if lower_edge:
        shadow_polygon = lower_edge + list(reversed(clipped_edge))
        draw.polygon([point(*item) for item in shadow_polygon], fill="#B19D6D")
        draw.line(
            [point(*item) for item in lower_edge],
            fill="#9C8757",
            width=sc(2),
        )

    # The fixed drill guide belongs underground; it is not the cast shadow.
    for y in range(surface_y + 8, 450, 12):
        draw.line(
            [point(drill_x, y), point(drill_x, min(y + 5, 450))],
            fill="#91A3B1",
            width=sc(2),
        )
    draw.text(
        point(drill_x + 9, 426),
        "FIXED AXIS",
        fill="#6E7F89",
        font=font(9, bold=True),
    )

    displayed_phase = math.degrees(rotation) % 360
    readout_text = f"arg R={displayed_phase:3.0f}°  •  |R|={moment_radius:.2f}"
    readout_font = font(11, bold=True)
    # Size the pill to the readout width so it never floats in empty space.
    # `textlength` returns width in scaled pixels; divide by SCALE to get
    # layout coordinates that compose with the rest of the layout maths.
    readout_width = draw.textlength(readout_text, font=readout_font) / SCALE
    readout_pad_x = 14
    readout_left = 48
    readout_top = 113
    readout_bottom = 143
    readout_right = readout_left + readout_width + 2 * readout_pad_x
    draw.rounded_rectangle(
        box(readout_left, readout_top, readout_right, readout_bottom),
        radius=sc(14),
        fill="#FFFFFF",
        outline=CORAL if show_rotation else "#91A3B1",
        width=sc(1),
    )
    draw.text(
        point(
            (readout_left + readout_right) / 2,
            (readout_top + readout_bottom) / 2,
        ),
        readout_text,
        fill=CORAL if show_rotation else MUTED,
        font=readout_font,
        anchor="mm",
    )

    # The pole passes THROUGH the canopy: the far (back) half of the dome
    # sits behind the shaft while the near (front) half occludes it. We
    # therefore split the eight sectors and the rim outline by their z
    # coordinate relative to the crown (canopy_world[2]): world z > crown
    # z means the piece extends toward the viewer (front, drawn on top
    # of the pole); world z < crown z means it extends away (back, drawn
    # under the pole). The pole itself is drawn between the two halves.
    pole_line = [point(canopy_x, canopy_y), point(tip_x, tip_y)]
    # Four-colour cycle over eight panels. Because 4 divides 8, the plain
    # A-B-C-D-A-B-C-D sequence tiles the umbrella perfectly: every
    # consecutive 4-panel arc -- i.e. every half of the canopy that faces
    # the viewer at any precession angle -- contains all four colours, so
    # the side view is never dominated by only two hues.
    colors = (
        CANOPY_TAN, CORAL, PALM, CANOPY_DUSTY,
        CANOPY_TAN, CORAL, PALM, CANOPY_DUSTY,
    )
    # Slightly darker parallel palette for the back-facing sectors, whose
    # outward normal points away from the camera; from the viewer's side
    # we are therefore looking at the concave inner underside of those
    # panels, which should read a touch darker than the sunlit outer top
    # of the front-facing sectors.
    inner_colors = (
        CANOPY_TAN_INNER,
        CORAL_INNER,
        PALM_INNER,
        CANOPY_DUSTY_INNER,
        CANOPY_TAN_INNER,
        CORAL_INNER,
        PALM_INNER,
        CANOPY_DUSTY_INNER,
    )
    # Skip the coloured canopy sectors entirely while the umbrella is folded
    # (canopy_scale ~ 0). At that scale the polygons collapse onto the shaft
    # apex and Pillow would only draw an ugly speckle of paper-coloured
    # outlines; the closed umbrella is meant to read as a plain stick.
    if clamped_canopy_scale > 0.02:
        # Elevations at which we sample the cambered rib meridian between
        # the apex (t=0) and the rim (t=1). Five intermediate steps give a
        # visibly smooth curve while keeping polygon complexity modest.
        rib_meridian_ts = (0.18, 0.36, 0.54, 0.72, 0.88)
        crown_z = canopy_world[2]
        # Small epsilon so a strictly-vertical shaft (tilt = 0, all rim
        # midpoints share the crown's z) doesn't collapse into a
        # degenerate all-back or all-front classification.
        depth_epsilon = 1e-6

        def is_front(z: float) -> bool:
            return z > crown_z + depth_epsilon

        sector_polys: list[tuple[float, int, list[tuple[int, int]]]] = []
        for sector in range(8):
            start = 2 * math.pi * sector / 8
            stop = 2 * math.pi * (sector + 1) / 8
            polygon = [point(canopy_x, canopy_y)]
            # Left rib meridian: cambered path from apex out and down to
            # the rim tip at `start`. Each sector shares its rib
            # meridians with its neighbour, so adjacent panels join
            # cleanly along a common curved rib.
            for t_val in rib_meridian_ts:
                polygon.append(canopy_point(start, t_val))
            # Rim arc: dense sampling so the sharp tab peaks and the wide
            # U-scallops both render as smooth curves.
            steps = 28
            for step in range(steps + 1):
                angle = start + (stop - start) * step / steps
                polygon.append(canopy_point(angle))
            # Right rib meridian back up to the apex at `stop`.
            for t_val in reversed(rib_meridian_ts):
                polygon.append(canopy_point(stop, t_val))
            mid_angle = 0.5 * (start + stop)
            mid_rim_z = canopy_world_point(mid_angle, 1.0)[2]
            sector_polys.append((mid_rim_z, sector, polygon))

        # Precompute the eight rib meridians as densely-sampled polylines
        # from the crown apex to their rim tip. Tagged with rim-tip z so
        # the back-facing ribs can be drawn behind the shaft and the
        # front-facing ones on top of it. These are the ONLY panel-to-
        # panel boundaries actually painted: the sector polygons below
        # are filled with no outline, so adjacent panels merge into one
        # continuous canopy surface and the ribs re-add just the thin
        # structural line where real umbrella spokes would sit -- avoiding
        # the harsh cream seams that ``outline=PAPER`` used to leave.
        rib_polyline_ts = tuple(step / 16.0 for step in range(17))
        rib_polylines: list[tuple[float, list[tuple[int, int]]]] = []
        for rib_index in range(8):
            rib_angle = 2 * math.pi * rib_index / 8
            tip_z = canopy_world_point(rib_angle, 1.0)[2]
            line_pts = [
                point(*project(canopy_world_point(rib_angle, t_val)))
                for t_val in rib_polyline_ts
            ]
            rib_polylines.append((tip_z, line_pts))

        # Sample the rim outline densely and tag each vertex as front/back
        # so we can split the ink line into a "behind pole" arc and an
        # "in front of pole" arc.
        outline_samples: list[tuple[float, tuple[int, int]]] = []
        for step in range(241):
            angle = 2 * math.pi * step / 240
            world = canopy_world_point(angle)
            outline_samples.append((world[2], point(*project(world))))

        # 1. Back sectors first (they sit behind the shaft). Filled with
        # no outline so adjacent panels merge edge-to-edge. The back half
        # of the dome shows its concave underside to the camera, so it is
        # painted in the darker inner-side palette (see CANOPY_INNER_DARKEN).
        for mid_z, sector, polygon in sector_polys:
            if not is_front(mid_z):
                draw.polygon(polygon, fill=inner_colors[sector])

        # 1b. Back-facing rib meridians on top of the back sectors, thin
        # enough to read as structural spokes rather than heavy divisions.
        for tip_z, line_pts in rib_polylines:
            if not is_front(tip_z) and len(line_pts) > 1:
                draw.line(line_pts, fill=INK, width=sc(2), joint="curve")

        # 2. Back arc of the rim outline (also behind the shaft). We walk
        # the closed loop and emit contiguous runs of back-side samples.
        back_run: list[tuple[int, int]] = []
        for z, sp in outline_samples:
            if is_front(z):
                if len(back_run) > 1:
                    draw.line(back_run, fill=INK, width=sc(3), joint="curve")
                back_run = []
            else:
                back_run.append(sp)
        if len(back_run) > 1:
            draw.line(back_run, fill=INK, width=sc(3), joint="curve")

        # 3. The shaft, between the two dome halves.
        draw.line(pole_line, fill="#0C2034", width=sc(7))

        # 4. Front sectors on top of the shaft. Same seamless fill as the
        # back sectors so the near half of the canopy also merges cleanly.
        for mid_z, sector, polygon in sector_polys:
            if is_front(mid_z):
                draw.polygon(polygon, fill=colors[sector])

        # 4b. Front-facing rib meridians on top of the front sectors.
        for tip_z, line_pts in rib_polylines:
            if is_front(tip_z) and len(line_pts) > 1:
                draw.line(line_pts, fill=INK, width=sc(2), joint="curve")

        # 5. Front arc of the rim outline on top of the shaft.
        front_run: list[tuple[int, int]] = []
        for z, sp in outline_samples:
            if is_front(z):
                front_run.append(sp)
            else:
                if len(front_run) > 1:
                    draw.line(front_run, fill=INK, width=sc(3), joint="curve")
                front_run = []
        if len(front_run) > 1:
            draw.line(front_run, fill=INK, width=sc(3), joint="curve")
    else:
        # Closed umbrella collapses to a plain stick; no sectors to
        # occlude the pole, so just draw the shaft.
        draw.line(pole_line, fill="#0C2034", width=sc(7))

    # Beach-umbrella finial: a small onion-shaped cap sitting on the
    # crown with a short pointed knob on top, painted in the same dark
    # ink as the pole so it reads as an integral extension of the shaft
    # rather than a raw joint of eight ribs. The finial is expressed in
    # a local (axial, transverse) frame anchored at (canopy_x, canopy_y)
    # with +axial running UP the shaft (away from the tip) and
    # +transverse 90 degrees CCW from that, so the whole cap stays glued
    # to the pole as the umbrella tilts and precesses.
    finial_up_dx = canopy_x - tip_x
    finial_up_dy = canopy_y - tip_y
    finial_up_len = math.hypot(finial_up_dx, finial_up_dy)
    if finial_up_len < 1e-6:
        finial_axial_dir = (0.0, -1.0)
    else:
        finial_axial_dir = (
            finial_up_dx / finial_up_len,
            finial_up_dy / finial_up_len,
        )
    finial_transverse_dir = (-finial_axial_dir[1], finial_axial_dir[0])

    def finial_pt(axial_local: float, transverse_local: float) -> tuple[int, int]:
        return point(
            canopy_x
            + finial_axial_dir[0] * axial_local
            + finial_transverse_dir[0] * transverse_local,
            canopy_y
            + finial_axial_dir[1] * axial_local
            + finial_transverse_dir[1] * transverse_local,
        )

    # Onion / acorn silhouette. The base row sits slightly below the crown
    # (negative axial) so the fill hides the small triangle where all
    # eight rib meridians meet at the apex. The widest belly is just
    # above the crown line, and the profile tapers into a short pointed
    # knob at axial ~= 8.3. Coordinates are 1/1.5x of the earlier
    # pale-onion design so the finial reads as a small dark cap that
    # continues the pole rather than a prominent white knob.
    finial_body_local = (
        (-1.67, -4.00),
        ( 0.33, -5.00),
        ( 2.67, -5.00),
        ( 4.67, -4.00),
        ( 6.33, -2.33),
        ( 7.33, -1.00),
        ( 8.33,  0.00),
        ( 7.33,  1.00),
        ( 6.33,  2.33),
        ( 4.67,  4.00),
        ( 2.67,  5.00),
        ( 0.33,  5.00),
        (-1.67,  4.00),
    )
    finial_polygon = [finial_pt(a, t) for a, t in finial_body_local]
    # Filled with the pole ink so the finial reads as an integral cap on
    # the top of the pole, matching the shaft and sand-auger colour.
    draw.polygon(finial_polygon, fill="#0C2034")

    # Beach-umbrella sand auger ("screw anchor"): the pole ends in a helical
    # corkscrew that a real beach umbrella twists into the sand. Rather than
    # drawing a smooth cylinder with thread lines painted on top, we build
    # the silhouette itself as a series of alternating left- and right-
    # pointing wing flares (one visible thread flight per half-turn), ending
    # in a small pointed cone. Filled with the pole ink so the auger reads
    # as an integral extension of the shaft.
    #
    # The auger is a RIGID extension of the shaft: it precesses / tilts
    # together with the pole above it. Only the very cone piercing tip at
    # the bottom is the pivot of the motion, and that cone tip is pinned
    # to the fixed vertical axis (drawn to land exactly at (pivot_x,
    # pivot_y)). The rest of the auger swings rigidly with the shaft.
    #
    # Axial coordinates run FROM (tip_x, tip_y) [shaft/auger junction]
    # TOWARDS (pivot_x, pivot_y) [cone tip on the fixed axis]. Positive
    # axial values point down-along-the-shaft; the transverse direction is
    # perpendicular to the shaft in screen space.
    tip_to_pivot_dx = pivot_x - tip_x
    tip_to_pivot_dy = pivot_y - tip_y
    axial_screen_length = math.hypot(tip_to_pivot_dx, tip_to_pivot_dy)
    if axial_screen_length < 1e-6:
        # Degenerate case (shouldn't happen with a nonzero auger length),
        # fall back to straight-down so drawing still produces something.
        auger_axial_dir = (0.0, 1.0)
        axial_screen_length = 1e-6
    else:
        auger_axial_dir = (
            tip_to_pivot_dx / axial_screen_length,
            tip_to_pivot_dy / axial_screen_length,
        )
    auger_transverse_dir = (-auger_axial_dir[1], auger_axial_dir[0])

    # Reference proportions (in screen units at zero-tilt projection): a
    # 16-unit stub above the shaft/auger junction (so the first wing pair
    # clears the sand line at rest), 26-unit wing-bearing cylinder, then a
    # 6-unit conical piercing tip. Total axial extent is 32, and the cone
    # tip sits 16 units below the junction. We scale the axial dimensions
    # uniformly by ``axial_screen_length / 16`` so the cone tip always
    # lands exactly at (pivot_x, pivot_y) regardless of how the tilted
    # shaft foreshortens under the orthographic projection.
    pole_hw = 3.5              # matches shaft half-width (line width=sc(7))
    wing_extent_top = 5.0      # how far the first (topmost) wing juts out
    wing_extent_bottom = 1.8   # last wing before the cone — tapered inward
    n_turns = 2                # visible helical turns
    axial_reference = 16.0
    axial_scale = axial_screen_length / axial_reference
    top_stub_axial = 16.0 * axial_scale
    cyl_length = 26.0 * axial_scale
    cone_length = 6.0 * axial_scale
    turn_len = cyl_length / n_turns
    # Asymmetric wing profile: the leading (upper) edge of a helical flight
    # slopes gently away from the pole to the outer tip, while the trailing
    # (lower) edge returns to the pole more sharply. This matches how a
    # real corkscrew flight reads from the side and gives the wings a
    # forward-canted "downward drilling" character rather than a symmetric
    # triangle.
    wing_taper_up = 0.42 * turn_len
    wing_taper_dn = 0.18 * turn_len
    # Silhouette axial anchors, all measured from (tip_x, tip_y):
    #   auger_top_axial   -> topmost point of the silhouette (above tip)
    #   cyl_bottom_axial  -> where the cylindrical body ends and the cone starts
    #   tip_bottom_axial  -> the piercing cone tip = pivot; lands at (pivot_x, pivot_y)
    auger_top_axial = -top_stub_axial

    def offset_pt(axial: float, transverse: float) -> tuple[float, float]:
        return (
            tip_x
            + auger_axial_dir[0] * axial
            + auger_transverse_dir[0] * transverse,
            tip_y
            + auger_axial_dir[1] * axial
            + auger_transverse_dir[1] * transverse,
        )

    def wing_extent_at(peak_axial: float) -> float:
        # Linearly taper wing extent from wing_extent_top at the topmost
        # wing down to wing_extent_bottom at the last wing before the cone.
        # This makes the auger read as a genuinely conical drill bit rather
        # than a straight-sided cylinder with fins.
        u = (peak_axial - auger_top_axial) / max(1e-6, cyl_length)
        u = max(0.0, min(1.0, u))
        return wing_extent_top + (wing_extent_bottom - wing_extent_top) * u

    # LEFT wing tips at 1/4, 5/4, ... of a turn; RIGHT wing tips at
    # 3/4, 7/4, ... — a half-turn offset that produces the classic
    # alternating corkscrew silhouette.
    left_peaks = [auger_top_axial + turn_len * (0.25 + i) for i in range(n_turns)]
    right_peaks = [auger_top_axial + turn_len * (0.75 + i) for i in range(n_turns)]
    cyl_bottom_axial = auger_top_axial + cyl_length
    tip_bottom_axial = cyl_bottom_axial + cone_length

    silhouette: list[tuple[float, float]] = []
    # Down the LEFT edge, adding a wing bulge at each left-peak axial.
    silhouette.append(offset_pt(auger_top_axial, -pole_hw))
    for peak in left_peaks:
        w = wing_extent_at(peak)
        silhouette.append(offset_pt(peak - wing_taper_up, -pole_hw))
        silhouette.append(offset_pt(peak, -(pole_hw + w)))
        silhouette.append(offset_pt(peak + wing_taper_dn, -pole_hw))
    silhouette.append(offset_pt(cyl_bottom_axial, -pole_hw))
    # Cone piercing tip.
    silhouette.append(offset_pt(tip_bottom_axial, 0.0))
    # Back UP the RIGHT edge, mirror pattern (reversed) with right-peak wings.
    silhouette.append(offset_pt(cyl_bottom_axial, pole_hw))
    for peak in reversed(right_peaks):
        w = wing_extent_at(peak)
        silhouette.append(offset_pt(peak + wing_taper_dn, pole_hw))
        silhouette.append(offset_pt(peak, pole_hw + w))
        silhouette.append(offset_pt(peak - wing_taper_up, pole_hw))
    silhouette.append(offset_pt(auger_top_axial, pole_hw))

    draw.polygon([point(x, y) for x, y in silhouette], fill="#0C2034")

    if show_rotation:
        # Precession is rotation about the FIXED vertical axis, so the arc's
        # horizontal centre is pinned to drill_x -- it never shifts left or
        # right. Its vertical position tracks the shaft top (canopy_y) with
        # a small clearance, so the precession indicator descends together
        # with the umbrella as |R| shrinks, matching the physical meaning
        # advertised by the "FIXED AXIS" marker below the sand: the drill
        # line is the true axis of rotation, and the arrow sweeps clockwise
        # around it.
        precess_center_x = drill_x
        # A small offset above canopy_y keeps the arc floating just clear of
        # the shaft top rather than crossing it as the umbrella descends.
        precess_center_y = canopy_y - 18
        precess_rx = 100
        # A shallow ellipse reads as a horizontal circle seen almost edge-on
        # (the precession trajectory in perspective) and keeps the arc top
        # well clear of the "PRECESS" label above it.
        precess_ry = 22
        draw.arc(
            box(
                precess_center_x - precess_rx,
                precess_center_y - precess_ry,
                precess_center_x + precess_rx,
                precess_center_y + precess_ry,
            ),
            start=205,
            end=332,
            fill=CORAL,
            width=sc(4),
        )
        arrow_angle = math.radians(332)
        arc_end = (
            precess_center_x + precess_rx * math.cos(arrow_angle),
            precess_center_y + precess_ry * math.sin(arrow_angle),
        )
        # Tangent to an ELLIPSE at parameter theta is (-rx*sin(theta),
        # ry*cos(theta)); the naive `arrow_angle + pi/2` shortcut is only
        # correct on a true circle. On our flattened arc (rx >> ry) the
        # arrowhead needs the ellipse-aware direction, otherwise it points
        # steeply down-right instead of tangentially along the sweep.
        tangent_angle = math.atan2(
            precess_ry * math.cos(arrow_angle),
            -precess_rx * math.sin(arrow_angle),
        )
        # Custom arrowhead: the standard triangular arrow_head puts its base
        # points PERPENDICULAR to the tangent, which -- on our very flat arc --
        # makes the back-upper vertex jut visibly above the stroke and reads
        # as a misaligned "hook" instead of a clean arrow. Here we instead
        # pin the base to the arc endpoint (so it merges into the stroke
        # width) and advance a slender tip FORWARD along the tangent. This
        # makes the arrowhead a clear pointer that continues the arc's
        # direction of sweep.
        head_length = 12.0
        head_half_width = 4.0
        tip_x = arc_end[0] + head_length * math.cos(tangent_angle)
        tip_y = arc_end[1] + head_length * math.sin(tangent_angle)
        perp_x = -math.sin(tangent_angle)
        perp_y = math.cos(tangent_angle)
        base_a = (
            arc_end[0] + head_half_width * perp_x,
            arc_end[1] + head_half_width * perp_y,
        )
        base_b = (
            arc_end[0] - head_half_width * perp_x,
            arc_end[1] - head_half_width * perp_y,
        )
        draw.polygon(
            [point(tip_x, tip_y), point(*base_a), point(*base_b)],
            fill=CORAL,
        )
        # Label sits at a fixed offset above the arc so it descends with the
        # arc when the umbrella drops, while staying centred on the fixed
        # axis at drill_x. Its vertical anchor mirrors the arc's, so only
        # vertical motion is inherited from canopy_y -- no horizontal drift.
        label_font = font(13, bold=True)
        draw.text(
            point(precess_center_x, precess_center_y - 50),
            "PRECESS",
            fill=CORAL,
            font=label_font,
            anchor="mm",
        )

    if show_downward_push:
        # Vertical "force handle": a slotted track with a fluid-style fill and
        # a wide horizontal knob at the marker level. Position along the slot
        # encodes the static per-regime push force magnitude (how fast |R|
        # decays). The layout is kept within the left panel (x <= 515).
        handle_cx = 447
        track_top = 234
        track_bottom = 325
        track_half_width = 6
        track_padding = 4

        # Two-line title centred above the handle so it fits the panel width.
        title_font = font(11, bold=True)
        title_lines = ("DOWNWARD", "PUSH FORCE")
        title_line_height = 14
        title_first_center_y = 207
        for line_index, line in enumerate(title_lines):
            draw.text(
                point(
                    handle_cx,
                    title_first_center_y + line_index * title_line_height,
                ),
                line,
                fill=BLUE,
                font=title_font,
                anchor="mm",
            )

        # Slot outline: rounded pale rectangle acting as the guide rail.
        draw.rounded_rectangle(
            box(
                handle_cx - track_half_width,
                track_top - track_padding,
                handle_cx + track_half_width,
                track_bottom + track_padding,
            ),
            radius=sc(track_half_width),
            fill="#E8EEF7",
            outline="#7C8CA1",
            width=sc(1),
        )

        marker_y = track_top + (track_bottom - track_top) * push

        # Force fill from the top of the slot down to the knob.
        fill_top = track_top - track_padding + 1
        if marker_y > fill_top:
            draw.rounded_rectangle(
                box(
                    handle_cx - track_half_width + 1,
                    fill_top,
                    handle_cx + track_half_width - 1,
                    marker_y,
                ),
                radius=sc(track_half_width - 1),
                fill=BLUE,
            )

        # Scale ticks + low/high labels on the right side of the slot.
        scale_x0 = handle_cx + track_half_width + 3
        scale_x1 = handle_cx + track_half_width + 8
        for step in range(5):
            tick_y = track_top + (track_bottom - track_top) * step / 4
            draw.line(
                [point(scale_x0, tick_y), point(scale_x1, tick_y)],
                fill="#7C8CA1",
                width=sc(1),
            )
        label_x = handle_cx + track_half_width + 11
        draw.text(point(label_x, track_top - 5), "LOW", fill=MUTED, font=font(9, bold=True))
        draw.text(point(label_x, track_bottom - 5), "HIGH", fill=MUTED, font=font(9, bold=True))

        # Wide horizontal T-handle knob at the marker level.
        knob_half_width = 15
        knob_half_height = 5
        draw.rounded_rectangle(
            box(
                handle_cx - knob_half_width,
                marker_y - knob_half_height,
                handle_cx + knob_half_width,
                marker_y + knob_half_height,
            ),
            radius=sc(knob_half_height),
            fill=INK,
        )
        # Grip lines for a tactile "hand-grip" look.
        for offset in (-6, -2, 2, 6):
            draw.line(
                [
                    point(handle_cx + offset, marker_y - 2),
                    point(handle_cx + offset, marker_y + 2),
                ],
                fill="#8595AC",
                width=sc(1),
            )


def profile_state(
    regime: dict[str, object],
    progress: float,
) -> tuple[float, float]:
    """Smoothly interpolate the loose data-inspired phase/magnitude profile."""

    samples = regime["moment_samples"]
    progress = max(0.0, min(1.0, progress))
    radius_tangents = monotone_tangents(samples, 1)
    phase_tangents = monotone_tangents(samples, 2)
    for index in range(1, len(samples)):
        right_progress = samples[index][0]
        if progress <= right_progress:
            left_progress = samples[index - 1][0]
            span = right_progress - left_progress
            amount = 0.0 if span == 0.0 else (progress - left_progress) / span
            radius = smooth_component(
                samples,
                1,
                index - 1,
                amount,
                radius_tangents,
            )
            phase = smooth_component(
                samples,
                2,
                index - 1,
                amount,
                phase_tangents,
            )
            return float(phase), float(radius)
    _, radius, phase = samples[-1]
    return float(phase), float(radius)


def circuit_state(
    regime: dict[str, object],
    step: int,
) -> tuple[float, float]:
    """Return the circular moment at one discrete circuit step."""

    bounded_step = max(0, min(CIRCUIT_STEP_COUNT, step))
    return profile_state(regime, bounded_step / CIRCUIT_STEP_COUNT)


def _find_figure04_pdf() -> Path | None:
    for candidate in FIGURE04_PDF_CANDIDATES:
        if candidate.exists():
            return candidate
    return None


def _ensure_figure04_panels_extracted() -> None:
    """Crop each panel of figure04.pdf tightly around its dashed unit circle
    and cache the result under ``docs/assets/figure04_panels/``.

    Runs only if any cached panel is missing. The paper's PDF is rasterised
    at 400 DPI, then each of the four panels is cropped as a square window
    of side ``2 * r * FIGURE04_CROP_MARGIN`` centred on the panel's dashed
    unit circle. The window intentionally excludes the paper's ``CASE:``
    label and axis labels so only the plot region ends up in the crop.
    """

    FIGURE04_PANELS_DIR.mkdir(parents=True, exist_ok=True)
    needed = [
        FIGURE04_PANELS_DIR / f"{entry['stem']}.png"
        for entry in FIGURE04_PANELS.values()
    ]
    if all(target.exists() for target in needed):
        return
    pdf_path = _find_figure04_pdf()
    if pdf_path is None:
        return
    try:
        import fitz  # PyMuPDF -- only imported if we actually need to extract.
    except ImportError:
        return
    doc = fitz.open(pdf_path)
    pix = doc[0].get_pixmap(dpi=400)
    raster = Image.frombytes(
        "RGB", (pix.width, pix.height), pix.samples
    ).convert("RGB")
    for entry in FIGURE04_PANELS.values():
        stem = entry["stem"]
        cx = int(entry["cx"])
        cy = int(entry["cy"])
        r = int(entry["r"])
        out = FIGURE04_PANELS_DIR / f"{stem}.png"
        if out.exists():
            continue
        margin = int(round(r * FIGURE04_CROP_MARGIN))
        crop_box = (cx - margin, cy - margin, cx + margin, cy + margin)
        raster.crop(crop_box).save(out)


_figure04_panel_cache: dict[str, Image.Image] = {}


def figure04_panel_for(
    regime: dict[str, object],
) -> Image.Image | None:
    """Return the cached figure04 panel image aligned with ``regime``.

    The image is a square crop centred on the paper's dashed unit circle,
    so pasting it centred on the animation's own unit circle overlays the
    published grey disorder cloud (and dashed axes) in place.
    """

    marker = str(regime.get("marker", ""))
    entry = FIGURE04_PANELS.get(marker)
    if entry is None:
        return None
    stem = entry["stem"]
    cached = _figure04_panel_cache.get(stem)
    if cached is not None:
        return cached
    path = FIGURE04_PANELS_DIR / f"{stem}.png"
    if not path.exists():
        _ensure_figure04_panels_extracted()
    if not path.exists():
        return None
    img = Image.open(path).convert("RGB")
    _figure04_panel_cache[stem] = img
    return img


def moment_state(    regime: dict[str, object],
    progress: float,
) -> tuple[float, float]:
    """Return the continuous umbrella state, independent of circuit sampling."""

    return profile_state(regime, progress)


def regime_wobble(
    regime: dict[str, object], raw_progress: float
) -> tuple[float, float]:
    """Small rotation/tilt tremor mimicking the residual phase fluctuations of
    R(t) inside a regime. Amplitude is set per regime (0 for regimes with no
    stochastic component). Tapers off near the end so the umbrella settles
    into its final pose -- unless the regime opts in to ``wobble_persist``, in
    which case the tremor stays alive through the held final frame (the
    localized regime uses this because its |R| never actually settles)."""

    rot_amp = float(regime.get("wobble_rot_amp", 0.0))
    tilt_amp = float(regime.get("wobble_tilt_amp", 0.0))
    tremor_amp = float(regime.get("wobble_tremor_amp", 0.0))
    tremor_freq = float(regime.get("wobble_tremor_freq", 0.0))
    if rot_amp == 0.0 and tilt_amp == 0.0 and tremor_amp == 0.0:
        return 0.0, 0.0
    if bool(regime.get("wobble_persist", False)):
        envelope = 1.0
    else:
        envelope = max(0.0, 1.0 - raw_progress ** 3)
    angle_wobble = envelope * rot_amp * (
        0.67 * math.sin(2.0 * math.pi * 3.3 * raw_progress)
        + 0.33 * math.sin(2.0 * math.pi * 6.7 * raw_progress + 1.1)
    )
    tilt_wobble_deg = envelope * tilt_amp * (
        0.67 * math.sin(2.0 * math.pi * 4.1 * raw_progress + 0.7)
        + 0.33 * math.sin(2.0 * math.pi * 9.3 * raw_progress + 2.3)
    )
    if tremor_amp != 0.0 and tremor_freq != 0.0:
        # High-frequency jitter shared between rotation and tilt with a small
        # phase offset so the axes don't move in lock-step. This is what
        # turns the underlying slow sway into a visible tremble.
        fast_rot = math.sin(2.0 * math.pi * tremor_freq * raw_progress + 0.4)
        fast_tilt = math.sin(
            2.0 * math.pi * tremor_freq * 1.17 * raw_progress + 1.9
        )
        angle_wobble += envelope * tremor_amp * fast_rot
        tilt_wobble_deg += envelope * tremor_amp * 3.2 * fast_tilt
    return angle_wobble, tilt_wobble_deg


def umbrella_tip_depth(
    regime: dict[str, object],
    moment_radius: float,
) -> float:
    """Return how far the auger tip has been driven below its initial pose.

    Only the |R|-driven contraction moves the anchor: the tip slides straight
    down along the fixed vertical axis by this amount, and nothing else
    (precession, tilt wobble, opening/closing) shifts it. That is what pins
    the anchor as the pivot of the entire motion.

    The reference drop is a fraction of the shaft length, scaled by the
    regime's descent-shape parameters:

    * ``descent_gamma < 1`` front-loads the drop against |R| contraction so a
      regime whose |R| shrinks aggressively (swappy) plunges into the sand
      earlier than a regime with the same final |R| but a gentler
      trajectory (ergodic).
    * ``descent_boost > 1`` lets a regime settle deeper than the shared cap
      (up to ``MAX_UMBRELLA_DROP_FRACTION * shaft_length * boost``).
    """

    initial_radius = float(regime["moment_samples"][0][1])
    relative_radius = max(
        MIN_RELATIVE_MOMENT_RADIUS,
        min(1.0, moment_radius / initial_radius),
    )
    contraction = (1.0 - relative_radius) / (1.0 - MIN_RELATIVE_MOMENT_RADIUS)
    descent_gamma = float(regime.get("descent_gamma", 1.0))
    descent_boost = float(regime.get("descent_boost", 1.0))
    effective_contraction = (contraction ** descent_gamma) * descent_boost
    return (
        MAX_UMBRELLA_DROP_FRACTION * UMBRELLA_SHAFT_LENGTH * effective_contraction
    )


def circuit_trajectory(
    regime: dict[str, object],
    progress: float,
) -> list[tuple[float, float, float]]:
    points: list[tuple[float, float, float]] = []
    last_step = min(
        CIRCUIT_STEP_COUNT,
        math.floor(max(0.0, min(1.0, progress)) * CIRCUIT_STEP_COUNT + 1e-12),
    )
    for step in range(last_step + 1):
        sample_progress = step / CIRCUIT_STEP_COUNT
        phase, radius = circuit_state(regime, step)
        points.append(
            (
                radius * math.cos(phase),
                radius * math.sin(phase),
                sample_progress,
            )
        )
    return points


def draw_circular_moment(
    draw: ImageDraw.ImageDraw,
    *,
    image: Image.Image,
    regime: dict[str, object],
    progress: float,
) -> None:
    cx, cy, radius = 731, 299, 135
    draw.rounded_rectangle(
        box(525, 104, 931, 458),
        radius=sc(24),
        fill="#FFFFFF",
        outline="#DCE4EA",
        width=sc(2),
    )
    draw.text(point(550, 126), "CIRCULAR MOMENT  R(t)", fill=INK, font=font(15, bold=True))
    # Light Re and Im coordinate axes: rather than crossing the dashed unit
    # circle, the two axes sit as an L-shaped frame just outside the circle
    # on the left (Im) and bottom (Re) with a small breathing gap. Only two
    # lines, no arrowheads -- the intent is a subtle plot frame, not vectors.
    axis_color = "#A9B7C2"
    axis_gap = 14
    im_axis_x = cx - radius - axis_gap
    re_axis_y = cy + radius + axis_gap
    draw.line(
        [point(im_axis_x, cy - radius), point(im_axis_x, re_axis_y)],
        fill=axis_color,
        width=sc(2),
    )
    draw.line(
        [point(im_axis_x, re_axis_y), point(cx + radius, re_axis_y)],
        fill=axis_color,
        width=sc(2),
    )
    # Axis labels: "Im R" sits on the top-left side of the vertical axis
    # (right-edge flush just left of the line, near its top), "Re R" sits a
    # touch above the right end of the horizontal axis.
    draw.text(point(im_axis_x - 6, cy - radius + 6), "Im R", fill=MUTED, font=font(12), anchor="rm")
    draw.text(point(cx + radius + 16, re_axis_y - 5), "Re R", fill=MUTED, font=font(12), anchor="lm")

    # Ghost cloud backdrop: paste the actual figure04 panel that corresponds
    # to the current regime. The paper's panel already ships with its own
    # dashed unit circle, origin marker, grey disorder cloud, and mean R(t)
    # trace, so no synthetic reproduction is needed. The animation's own
    # coloured trace is drawn on top and traces out the same mean.
    panel_img = figure04_panel_for(regime)
    if panel_img is not None:
        # The paper crop is a square window whose side is
        # 2 * paper_r * FIGURE04_CROP_MARGIN, so at the animation's target
        # unit-circle radius the pasted side must be
        # 2 * radius * SCALE * FIGURE04_CROP_MARGIN to keep the two circles
        # exactly aligned.
        target_side = int(round(2 * FIGURE04_CROP_MARGIN * radius * SCALE))
        resized = panel_img.resize(
            (target_side, target_side), Image.Resampling.LANCZOS
        )
        paste_x = cx * SCALE - target_side // 2
        paste_y = cy * SCALE - target_side // 2
        image.paste(resized, (paste_x, paste_y))

    # Background reference frame: a dashed |R|=1 ring and a small dot at
    # the origin. These sit on top of the ghost figure04 backdrop but under
    # the coloured trajectory, so the unit circle and centre of the R(t)
    # plane read clearly in every regime -- including when the paper panel
    # cannot be loaded and the backdrop is blank.
    dashed_circle(draw, (cx, cy), radius, fill=axis_color, width=1)
    draw.ellipse(box(cx - 2.5, cy - 2.5, cx + 2.5, cy + 2.5), fill=INK)

    points = circuit_trajectory(regime, progress)
    pixels = [
        (point(cx + radius * x, cy - radius * y), sample_progress)
        for x, y, sample_progress in points
    ]
    if len(pixels) > 1:
        for index in range(len(pixels) - 1):
            amount = pixels[index + 1][1]
            draw.line(
                [pixels[index][0], pixels[index + 1][0]],
                fill=mix(BLUE, CORAL, amount),
                width=sc(5),
            )
    for (node_x, node_y), sample_progress in pixels:
        node_radius = sc(3)
        draw.ellipse(
            (
                node_x - node_radius,
                node_y - node_radius,
                node_x + node_radius,
                node_y + node_radius,
            ),
            fill=mix(BLUE, CORAL, sample_progress),
            outline="#FFFFFF",
            width=sc(1),
        )
    px, py = pixels[-1][0]
    endpoint_progress = pixels[-1][1]
    draw.ellipse(
        (px - sc(8), py - sc(8), px + sc(8), py + sc(8)),
        fill=mix(BLUE, CORAL, endpoint_progress),
        outline="#FFFFFF",
        width=sc(3),
    )

    # Sweeping arc drift indicator: a genuine curved arrow that shares its
    # centre with the unit circle of R(t), so it visually reads as "R(t)
    # precesses in this direction around the origin". The arc therefore sits
    # concentric to (and just outside) the dashed unit circle, in the top-
    # right corner of the panel next to the "drift" label.
    drift_cx, drift_cy = cx, cy
    drift_radius = radius + 25
    drift_head_size = 12
    drift_start_deg = 295
    drift_end_deg = 342
    draw.arc(
        box(
            drift_cx - drift_radius,
            drift_cy - drift_radius,
            drift_cx + drift_radius,
            drift_cy + drift_radius,
        ),
        start=drift_start_deg,
        end=drift_end_deg,
        fill=CORAL,
        width=sc(4),
    )
    end_rad = math.radians(drift_end_deg)
    arc_tip = (
        drift_cx + drift_radius * math.cos(end_rad),
        drift_cy + drift_radius * math.sin(end_rad),
    )
    # Tangent to the arc at its endpoint is perpendicular to the radius,
    # rotated a quarter-turn clockwise (matching the sweep direction), so
    # the arrowhead axis lies along the arc rather than jutting straight down.
    arrow_head(
        draw,
        arc_tip,
        end_rad + math.pi / 2,
        fill=CORAL,
        size=drift_head_size,
    )
    draw.text(point(848, 154), "drift", fill=CORAL, font=font(11, bold=True))

    draw.line([point(817, 342), point(772, 318)], fill=BLUE, width=sc(3))
    arrow_head(
        draw,
        (772, 318),
        math.atan2(318 - 342, 772 - 817),
        fill=BLUE,
        size=7,
    )
    draw.text(point(817, 346), "spreading", fill=BLUE, font=font(11, bold=True))


def draw_regime_marker(
    draw: ImageDraw.ImageDraw,
    marker: str,
    center: tuple[float, float],
    size: float,
    fill: str,
) -> None:
    """Draw the same markers the paper uses to label the four regimes.

    The shapes mirror the LaTeX symbols \\ding{108}, \\filledtriangle,
    $\\blacksquare$, and $\\bigstar$ as compact vector primitives so they
    stay crisp at both draft and final resolutions.
    """

    cx, cy = center
    half = size / 2.0
    if marker == "circle":
        draw.ellipse(
            box(cx - half, cy - half, cx + half, cy + half),
            fill=fill,
        )
    elif marker == "triangle":
        # Slightly enlarge so the visual weight matches the circle/square.
        top = (cx, cy - half * 1.05)
        bottom_left = (cx - half * 1.05, cy + half * 0.75)
        bottom_right = (cx + half * 1.05, cy + half * 0.75)
        draw.polygon(
            [point(*top), point(*bottom_left), point(*bottom_right)],
            fill=fill,
        )
    elif marker == "square":
        # Trim a hair so the square does not read as heavier than the circle.
        inset = half * 0.92
        draw.rectangle(
            box(cx - inset, cy - inset, cx + inset, cy + inset),
            fill=fill,
        )
    elif marker == "star":
        outer = half * 1.15
        inner = outer * 0.42
        vertices: list[tuple[int, int]] = []
        for step in range(10):
            angle = -math.pi / 2 + step * math.pi / 5
            radius = outer if step % 2 == 0 else inner
            vertices.append(
                point(cx + radius * math.cos(angle), cy + radius * math.sin(angle))
            )
        draw.polygon(vertices, fill=fill)


def draw_footer(
    draw: ImageDraw.ImageDraw,
    regime: dict[str, object],
    *,
    image: Image.Image,
    progress: float,
) -> None:
    footer_left = 52
    footer_right = 908
    footer_top = 477
    footer_bottom = 525
    footer_center_y = (footer_top + footer_bottom) / 2.0
    footer_radius = sc(20)
    draw.rounded_rectangle(
        box(footer_left, footer_top, footer_right, footer_bottom),
        radius=footer_radius,
        fill=INK,
    )

    # Loading bar: a slightly darker blue sweeps left-to-right in step
    # with the current regime's own dynamics (opening + motion + hold +
    # closing). The fill is clipped to the base bar's rounded shape via
    # a mask, so the leading edge stays flush with the footer corners
    # without having to draw a rounded rectangle that would round the
    # trailing (right) edge as well. Drawn BEFORE the pill / marker /
    # description so the label overlays the tinted background.
    clamped_progress = max(0.0, min(1.0, float(progress)))
    if clamped_progress > 0.0:
        progress_pixel_right = round(
            (footer_left + clamped_progress * (footer_right - footer_left))
            * SCALE
        )
        mask = Image.new("L", image.size, 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.rounded_rectangle(
            box(footer_left, footer_top, footer_right, footer_bottom),
            radius=footer_radius,
            fill=255,
        )
        # Erase everything to the right of the progress marker so the
        # mask is white only where the fill should appear.
        mask_draw.rectangle(
            (progress_pixel_right, 0, image.size[0], image.size[1]),
            fill=0,
        )
        image.paste(INK_PROGRESS_RGB, mask=mask)

    # Regime pill: sized dynamically around marker + name with even padding
    # so short names ("SWAPPY") aren't lost inside a giant pill and longer
    # names ("NEAR SWAP") still fit with matching visual weight.
    name = str(regime["name"])
    name_font = font(13, bold=True)
    # `textlength` returns width in scaled pixels; convert back to layout
    # units so it composes with the marker in the same coordinate system.
    name_width = draw.textlength(name, font=name_font) / SCALE
    marker_size = 11.0
    marker_gap = 6.0
    pill_pad_x = 16
    pill_top = 485
    pill_bottom = 517
    pill_left = 65
    content_width = marker_size + marker_gap + name_width
    pill_right = pill_left + content_width + 2 * pill_pad_x
    draw.rounded_rectangle(
        box(pill_left, pill_top, pill_right, pill_bottom),
        radius=sc(14),
        fill=str(regime["color"]),
    )
    marker_center = (pill_left + pill_pad_x + marker_size / 2.0, footer_center_y)
    draw_regime_marker(
        draw,
        str(regime["marker"]),
        marker_center,
        marker_size,
        fill="#FFFFFF",
    )
    name_center_x = pill_left + pill_pad_x + marker_size + marker_gap + name_width / 2.0
    draw.text(
        point(name_center_x, footer_center_y),
        name,
        fill="#FFFFFF",
        font=name_font,
        anchor="mm",
    )

    # Description sits to the right of the pill with a consistent gap and
    # shares the pill's vertical centre so the two elements read as one row.
    # Font size is trimmed from 16 to 14 so it doesn't visually overpower
    # the 13pt pill label.
    desc_font = font(14, bold=True)
    draw.text(
        point(pill_right + 22, footer_center_y),
        str(regime["description"]),
        fill="#FFFFFF",
        font=desc_font,
        anchor="lm",
    )


def frame_state(
    regime: dict[str, object],
    frame_index: int,
    *,
    previous_regime: dict[str, object],
    next_regime: dict[str, object],
) -> dict[str, object]:
    """Return the per-frame pose parameters for a regime.

    The animation is split into four contiguous phases:

    * ``opening`` (``OPEN_FRAMES``) -- the umbrella begins the regime
      standing perpendicular to the beach (tilt = 0, rotation = 0), the
      canonical resting pose delivered by the previous regime's closing
      phase. As the ribs pivot open the shaft eases from that vertical
      stance into the regime's own initial pose (target_tilt,
      initial_rotation).
    * ``motion`` (``MOTION_FRAMES``) -- the regime's ``moment_samples``
      trajectory plays out with the usual eased ``moment_state`` mapping
      for arg R and |R|, and the shaft's tilt is simultaneously faded
      from ``target_tilt`` back to 0. The fade rides the same eased
      ``motion_progress`` that governs arg R and |R|, so the settling
      to a straight vertical shaft reads as an intrinsic continuation
      of the time evolution rather than a separate transition.
    * ``holding`` (``HOLD_FRAMES``) -- the final motion frame is held so
      the viewer can read the settled outcome: a shaft standing straight
      up (potentially deep in the sand) at the trajectory's final arg R
      and |R|.
    * ``closing`` (``CLOSE_FRAMES``) -- the ribs fold back parallel to
      the (already-vertical) shaft, the auger extracts to the surface
      (|R| -> 1), and the arg R readout unwinds toward 0. By the end of
      this phase the umbrella is standing straight up with its canopy
      folded, ready for the next regime's opening to ease it into a new
      initial pose.

    The downward-push handle slides through the closing + opening pair as a
    single linear interpolation from the previous regime's push to the next
    regime's push. During closing we run from the current push to the
    midpoint; during opening we continue from the midpoint to the new push.
    """

    prev_push = float(previous_regime["downward_push"])
    curr_push = float(regime["downward_push"])
    next_push = float(next_regime["downward_push"])
    initial_rotation = float(regime["moment_samples"][0][2])
    initial_radius = float(regime["moment_samples"][0][1])
    target_tilt = float(regime["tilt_deg"])
    has_precession = (
        abs(float(regime["moment_samples"][-1][2]) - initial_rotation) > 0.01
    )

    motion_start = OPEN_FRAMES
    hold_start = motion_start + MOTION_FRAMES
    close_start = hold_start + HOLD_FRAMES

    if frame_index < motion_start:
        # Opening phase: the umbrella starts perpendicular to the beach
        # (tilt = 0, rotation = 0), the canonical resting pose delivered
        # by the previous regime's closing phase. As the ribs pivot open
        # from parallel to the pole (canopy_scale = 0) to fully deployed
        # (canopy_scale = 1) the shaft eases in tandem from that vertical
        # stance into the regime's own initial pose (target_tilt,
        # initial_rotation), while the handle finishes its slide from
        # the previous-regime midpoint up to the current regime's target
        # push.
        denominator = max(1, OPEN_FRAMES - 1)
        raw_t = frame_index / denominator if OPEN_FRAMES > 1 else 1.0
        t = ease(raw_t)
        canopy_scale = t
        tilt_deg = t * target_tilt
        rotation = t * initial_rotation
        moment_radius = initial_radius
        motion_progress = 0.0
        raw_progress_for_wobble = 0.0
        mid_push = 0.5 * (prev_push + curr_push)
        push = mid_push + t * (curr_push - mid_push)
        show_rotation = False
    elif frame_index < hold_start:
        # Motion phase: play the regime trajectory through its eased
        # mapping for arg R and |R|, and simultaneously fade the shaft's
        # tilt from ``target_tilt`` back to 0. The fade rides the same
        # eased ``motion_progress`` that governs the trajectory, so the
        # umbrella smoothly settles into a straight vertical stance as
        # part of the time evolution rather than through a separate
        # post-motion transition. Using ``1 - motion_progress**2`` keeps
        # the regime's distinctive tilt visible through most of the
        # motion and only eases to vertical near the end.
        motion_frame = frame_index - motion_start
        denominator = max(1, MOTION_FRAMES - 1)
        raw_progress = motion_frame / denominator if MOTION_FRAMES > 1 else 1.0
        motion_progress = ease(raw_progress)
        rotation, moment_radius = moment_state(regime, motion_progress)
        tilt_fade = 1.0 - motion_progress * motion_progress
        tilt_deg = target_tilt * tilt_fade
        canopy_scale = 1.0
        push = curr_push
        raw_progress_for_wobble = raw_progress
        show_rotation = has_precession
    elif frame_index < close_start:
        # Held phase: freeze at the final motion pose so the viewer has
        # time to read the settled outcome. By the end of the motion the
        # shaft has smoothly straightened to vertical, so we hold it
        # there (tilt = 0) with the moment radius and arg R at their
        # trajectory-final values -- potentially deep in the sand for
        # regimes whose |R| contracted aggressively.
        rotation, moment_radius = moment_state(regime, 1.0)
        tilt_deg = 0.0
        canopy_scale = 1.0
        push = curr_push
        motion_progress = 1.0
        raw_progress_for_wobble = 1.0
        show_rotation = has_precession
    else:
        # Closing + return to the shared vertical resting pose. The shaft
        # is already vertical from the end of the motion (and stayed
        # vertical through the hold), so during the closing phase we
        # keep it there (tilt = 0) while the ribs fold flat, the auger
        # extracts to the surface (|R| -> 1), and the arg R readout
        # unwinds toward 0. The next regime's opening phase then eases
        # the shaft from this shared vertical pose into its own initial
        # pose.
        close_frame = frame_index - close_start
        denominator = max(1, CLOSE_FRAMES - 1)
        raw_t = close_frame / denominator if CLOSE_FRAMES > 1 else 1.0
        t = ease(raw_t)
        final_rotation, final_radius = moment_state(regime, 1.0)
        next_initial_radius = float(next_regime["moment_samples"][0][1])
        canopy_scale = 1.0 - t
        tilt_deg = 0.0
        rotation = final_rotation * (1.0 - t)
        moment_radius = final_radius * (1.0 - t) + next_initial_radius * t
        motion_progress = 1.0
        raw_progress_for_wobble = 1.0
        mid_push = 0.5 * (curr_push + next_push)
        push = curr_push + t * (mid_push - curr_push)
        show_rotation = False

    tip_depth = umbrella_tip_depth(regime, moment_radius)
    return {
        "rotation": rotation,
        "tilt_deg": tilt_deg,
        "canopy_scale": canopy_scale,
        "moment_radius": moment_radius,
        "tip_depth": tip_depth,
        "motion_progress": motion_progress,
        "push": push,
        "show_rotation": show_rotation,
        "raw_progress_for_wobble": raw_progress_for_wobble,
    }


def render_frame(
    regime: dict[str, object],
    frame_index: int,
    *,
    previous_regime: dict[str, object] | None = None,
    next_regime: dict[str, object] | None = None,
    downsample: bool = True,
) -> Image.Image:
    if previous_regime is None:
        previous_regime = regime
    if next_regime is None:
        next_regime = regime
    state = frame_state(
        regime,
        frame_index,
        previous_regime=previous_regime,
        next_regime=next_regime,
    )

    image = Image.new("RGB", (WIDTH * SCALE, HEIGHT * SCALE), PAPER)
    draw = ImageDraw.Draw(image)

    # Sky and sand span the entire canvas -- sky reaches the top margin
    # and sand reaches the bottom margin -- so the beach scene reads as
    # an edge-to-edge backdrop. The header, readout pill, CIRCULAR MOMENT
    # panel, and footer/loading bar are all drawn on top afterwards, so
    # the background is only visible where they don't cover it.
    draw.rectangle(box(0, 0, WIDTH, 467), fill=SKY)
    draw_header(draw)
    draw_sand(draw)

    rotation = float(state["rotation"])
    tilt_deg = float(state["tilt_deg"])
    canopy_scale = float(state["canopy_scale"])
    # Scale the tremor by the deployed canopy so it fades in during opening
    # and out during closing, and stays at full amplitude while the canopy
    # is open. This keeps the "closed" pose truly still.
    rotation_wobble, tilt_wobble = regime_wobble(
        regime, float(state["raw_progress_for_wobble"])
    )
    rotation += rotation_wobble * canopy_scale
    tilt_deg += tilt_wobble * canopy_scale

    draw_umbrella(
        draw,
        rotation=rotation,
        tilt_deg=tilt_deg,
        moment_radius=float(state["moment_radius"]),
        tip_depth=float(state["tip_depth"]),
        push=float(state["push"]),
        show_rotation=bool(state["show_rotation"]),
        show_downward_push=True,
        canopy_scale=canopy_scale,
    )
    draw_circular_moment(
        draw, image=image, regime=regime, progress=float(state["motion_progress"])
    )
    # Regime progress used to fill the footer loading bar: 0 at the first
    # frame of the opening phase, 1 at the last frame of the closing
    # phase. The bar resets to 0 when the next regime begins, giving a
    # clean "loading complete -> next regime loading" cadence.
    regime_progress = (
        frame_index / (FRAME_COUNT - 1) if FRAME_COUNT > 1 else 1.0
    )
    draw_footer(draw, regime, image=image, progress=regime_progress)

    if downsample:
        return image.resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)
    return image


def render_gif(
    output_path: Path,
    *,
    frame_multiplier: int = 1,
    duration_ms: int = FRAME_DURATION_MS,
    downsample: bool = True,
) -> None:
    """Render every regime and save the resulting animation as a GIF.

    ``frame_multiplier`` scales all four phase frame counts (opening,
    motion, holding, closing) uniformly; halving ``duration_ms`` at the
    same time preserves the total wall-clock length while doubling the
    temporal resolution. ``downsample=False`` skips the final
    ``WIDTH*SCALE`` -> ``WIDTH`` LANCZOS downscale and emits the raw 2x
    raster, yielding a 1920x1080 GIF instead of the default 960x540.
    """

    global OPEN_FRAMES, MOTION_FRAMES, HOLD_FRAMES, CLOSE_FRAMES, FRAME_COUNT
    saved = (OPEN_FRAMES, MOTION_FRAMES, HOLD_FRAMES, CLOSE_FRAMES, FRAME_COUNT)
    try:
        OPEN_FRAMES = saved[0] * frame_multiplier
        MOTION_FRAMES = saved[1] * frame_multiplier
        HOLD_FRAMES = saved[2] * frame_multiplier
        CLOSE_FRAMES = saved[3] * frame_multiplier
        FRAME_COUNT = OPEN_FRAMES + MOTION_FRAMES + HOLD_FRAMES + CLOSE_FRAMES

        output_path.parent.mkdir(parents=True, exist_ok=True)
        frames: list[Image.Image] = []
        n_regimes = len(REGIMES)
        for regime_index, regime in enumerate(REGIMES):
            # The GIF loops, so the "previous" regime for the first entry
            # is the last one -- this keeps the handle slide continuous
            # across the loop boundary.
            previous_regime = REGIMES[(regime_index - 1) % n_regimes]
            next_regime = REGIMES[(regime_index + 1) % n_regimes]
            for frame_index in range(FRAME_COUNT):
                frames.append(
                    render_frame(
                        regime,
                        frame_index,
                        previous_regime=previous_regime,
                        next_regime=next_regime,
                        downsample=downsample,
                    )
                )

        # Build the shared GIF palette from a frame in which the umbrella
        # is fully deployed. ``frames[0]`` has ``canopy_scale = 0`` (the
        # canopy is folded flat and the sector-drawing block is skipped
        # entirely), so a palette built from it contains only background
        # hues (sky, sand, ink, muted, coral/blue from the header) and
        # every panel colour ends up mapped to whatever background hue is
        # nearest -- PALM turns slate grey, CANOPY_TAN turns brown. Any
        # frame from the middle of a regime's motion phase draws all
        # eight sectors (both halves of the dome), so all four panel
        # colours contribute enough pixels to be preserved by the
        # 192-colour median-cut palette.
        palette_source = frames[OPEN_FRAMES + MOTION_FRAMES // 2]
        palette = palette_source.quantize(colors=192)
        paletted = [
            frame.quantize(palette=palette, dither=Image.Dither.NONE)
            for frame in frames
        ]
        paletted[0].save(
            output_path,
            save_all=True,
            append_images=paletted[1:],
            duration=duration_ms,
            loop=0,
            disposal=2,
            optimize=True,
        )
        print(f"Wrote {output_path} ({len(frames)} frames)")
    finally:
        OPEN_FRAMES, MOTION_FRAMES, HOLD_FRAMES, CLOSE_FRAMES, FRAME_COUNT = saved


def main() -> None:
    render_gif(OUTPUT)
    render_gif(
        OUTPUT_HR,
        frame_multiplier=HR_FRAME_MULTIPLIER,
        duration_ms=HR_FRAME_DURATION_MS,
        downsample=False,
    )


if __name__ == "__main__":
    main()

