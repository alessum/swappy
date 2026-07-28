"""Generate the high-level umbrella analogy used in the README.

The phase and magnitude profiles are qualitative fits to the published N=20
trajectories. The circuit is shown at discrete R_n samples, while the umbrella
interpolates continuously between them. Blue-to-red encodes time only.
"""

from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


WIDTH, HEIGHT = 960, 540
SCALE = 2
# Render the physical motion at 25 fps. Repeated final frames are folded into
# one longer pause by Pillow's GIF optimiser.
FRAME_COUNT = 90
MOVING_FRAMES = 72
FRAME_DURATION_MS = 40
CIRCUIT_STEP_COUNT = 20
UMBRELLA_SHAFT_LENGTH = 145.0
UMBRELLA_TIP_LENGTH = 13.0
SAND_SURFACE_Y = 334
INITIAL_TIP_Y = 330
INITIAL_TIP_CLEARANCE = SAND_SURFACE_Y - INITIAL_TIP_Y
MAX_UMBRELLA_DROP_FRACTION = 1.0 / 3.0

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "assets" / "swappy-umbrella.gif"

FONT_REGULAR_CANDIDATES = (
    "/System/Library/Fonts/Supplemental/Arial.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
    "C:/Windows/Fonts/arial.ttf",
)
FONT_BOLD_CANDIDATES = (
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
)

INK = "#18324A"
MUTED = "#64748B"
PAPER = "#FBFAF6"
SKY = "#EAF5F6"
SAND = "#E8CF91"
SAND_DARK = "#B88B45"
CORAL = "#E76F51"
GOLD = "#F2B84B"
TEAL = "#2A9D8F"
BLUE = "#4067C9"
PURPLE = "#7656A7"
PALE_BLUE = "#DCE8F7"


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
NEAR_SWAP_MOMENT_SAMPLES = tuple(
    (step / 20.0, 0.990, -2.0 * math.pi * step / 20.0)
    for step in range(21)
)


REGIMES = (
    {
        "name": "LOCALIZED",
        "description": "small phase wander; nearly fixed |R|",
        "tilt_deg": 8.0,
        "moment_samples": LOCALIZED_MOMENT_SAMPLES,
        "downward_push": 0.0,
        "color": MUTED,
    },
    {
        "name": "ERGODIC",
        "description": "radial contraction; negligible drift",
        "tilt_deg": 8.0,
        "moment_samples": ERGODIC_MOMENT_SAMPLES,
        "downward_push": 0.55,
        "color": BLUE,
    },
    {
        "name": "SWAPPY",
        "description": "clockwise spiral; drift plus contraction",
        "tilt_deg": 20.0,
        "moment_samples": SWAPPY_MOMENT_SAMPLES,
        "downward_push": 0.65,
        "color": CORAL,
    },
    {
        "name": "NEAR SWAP",
        "description": "20-point orbit; nearly fixed |R|",
        "tilt_deg": 32.0,
        "moment_samples": NEAR_SWAP_MOMENT_SAMPLES,
        "downward_push": 0.0,
        "color": TEAL,
    },
)
MAX_DOWNWARD_PUSH = max(float(regime["downward_push"]) for regime in REGIMES)
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
    candidates = FONT_BOLD_CANDIDATES if bold else FONT_REGULAR_CANDIDATES
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
    draw.rectangle(box(30, 334, 493, 458), fill=SAND)
    wave = []
    for x in range(30, 494, 6):
        y = 334 + 4 * math.sin((x - 30) / 24)
        wave.append(point(x, y))
    draw.line(wave, fill=SAND_DARK, width=sc(2))

    for i in range(52):
        x = 44 + ((i * 83) % 430)
        y = 352 + ((i * 47) % 92)
        radius = 1 + (i % 2)
        draw.ellipse(
            box(x - radius, y - radius, x + radius, y + radius),
            fill=mix(SAND_DARK, PAPER, 0.35),
        )

    draw.rounded_rectangle(
        box(54, 416, 203, 448),
        radius=sc(14),
        fill="#F7EAC8",
        outline=SAND_DARK,
        width=sc(1),
    )
    draw.text(point(75, 423), "STRONG DISORDER", fill=INK, font=font(12, bold=True))


def draw_umbrella(
    draw: ImageDraw.ImageDraw,
    *,
    rotation: float,
    tilt_deg: float,
    moment_radius: float,
    canopy_height: float,
    push: float,
    show_rotation: bool,
    show_downward_push: bool,
) -> None:
    drill_x, surface_y = 269, SAND_SURFACE_Y
    tilt = math.radians(tilt_deg)

    # Three-dimensional rigid-body geometry with an orthographic side
    # projection. Ignoring depth in the screen-y coordinate ensures that every
    # point of the umbrella moves vertically only when |R(t)| changes.
    shaft_length = UMBRELLA_SHAFT_LENGTH
    axis = (
        math.sin(tilt) * math.cos(rotation),
        math.cos(tilt),
        math.sin(tilt) * math.sin(rotation),
    )
    canopy_world = (
        shaft_length * axis[0],
        canopy_height,
        shaft_length * axis[2],
    )
    tip_world = (
        0.0,
        canopy_world[1] - shaft_length * axis[1],
        0.0,
    )
    canopy_drop = 22
    rim_world = tuple(
        canopy_world[index] - canopy_drop * axis[index] for index in range(3)
    )

    def project(world: tuple[float, float, float]) -> tuple[float, float]:
        x_coord, y_coord, _ = world
        return drill_x + x_coord, surface_y - y_coord

    tip_x, tip_y = project(tip_world)
    canopy_x, canopy_y = project(canopy_world)

    # These orthonormal vectors span the plane perpendicular to the shaft.
    # Projecting the resulting circle gives the correct changing ellipse as
    # the umbrella precesses into and out of the page.
    azimuth_basis = (-math.sin(rotation), 0.0, math.cos(rotation))
    tilt_basis = (
        math.cos(tilt) * math.cos(rotation),
        -math.sin(tilt),
        math.cos(tilt) * math.sin(rotation),
    )
    canopy_radius = 120

    def canopy_world_point(angle: float) -> tuple[float, float, float]:
        radial = tuple(
            math.cos(angle) * azimuth_basis[index]
            + math.sin(angle) * tilt_basis[index]
            for index in range(3)
        )
        return tuple(
            rim_world[index] + canopy_radius * radial[index]
            for index in range(3)
        )

    def canopy_point(angle: float) -> tuple[int, int]:
        return point(*project(canopy_world_point(angle)))

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
    shadow_radius_x = 62.0
    shadow_radius_y = 19.0
    shadow_center = max(
        38.0 + shadow_radius_x,
        min(488.0 - shadow_radius_x, shadow_center),
    )
    shadow_center_y = surface_y + 4
    lower_edge: list[tuple[float, float]] = []
    clipped_edge: list[tuple[float, float]] = []
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

    draw.rounded_rectangle(
        box(48, 113, 236, 143),
        radius=sc(14),
        fill="#FFFFFF",
        outline=CORAL if show_rotation else "#91A3B1",
        width=sc(1),
    )
    displayed_phase = math.degrees(rotation) % 360
    draw.text(
        point(59, 120),
        f"arg R={displayed_phase:3.0f}°  •  |R|={moment_radius:.2f}",
        fill=CORAL if show_rotation else MUTED,
        font=font(11, bold=True),
    )

    # The pole remains visible through the sand as a diagrammatic cutaway.
    draw.line(
        [point(canopy_x, canopy_y), point(tip_x, tip_y)],
        fill="#0C2034",
        width=sc(9),
    )
    draw.line(
        [point(canopy_x - 3, canopy_y), point(tip_x - 3, tip_y)],
        fill="#F5F1E8",
        width=sc(2),
    )
    colors = (CORAL, GOLD, TEAL, PALE_BLUE, PURPLE, GOLD, CORAL, PALE_BLUE)
    for sector in range(8):
        start = 2 * math.pi * sector / 8
        stop = 2 * math.pi * (sector + 1) / 8
        polygon = [point(canopy_x, canopy_y)]
        steps = 10
        for step in range(steps + 1):
            angle = start + (stop - start) * step / steps
            polygon.append(canopy_point(angle))
        draw.polygon(polygon, fill=colors[sector], outline=PAPER)

    outline = [canopy_point(2 * math.pi * step / 80) for step in range(81)]
    draw.line(outline, fill=INK, width=sc(3), joint="curve")
    draw.ellipse(
        box(canopy_x - 8, canopy_y - 8, canopy_x + 8, canopy_y + 8),
        fill=INK,
    )

    draw.line(
        [point(canopy_x, canopy_y), point(tip_x, tip_y)],
        fill="#0C2034",
        width=sc(7),
    )
    shaft_dx = tip_x - canopy_x
    shaft_dy = tip_y - canopy_y
    shaft_screen_length = math.hypot(shaft_dx, shaft_dy)
    shaft_direction = (
        shaft_dx / shaft_screen_length,
        shaft_dy / shaft_screen_length,
    )
    shaft_normal = (-shaft_direction[1], shaft_direction[0])
    base_center = (
        tip_x - 2 * shaft_direction[0],
        tip_y - 2 * shaft_direction[1],
    )
    draw.polygon(
        [
            point(
                base_center[0] - 7 * shaft_normal[0],
                base_center[1] - 7 * shaft_normal[1],
            ),
            point(
                base_center[0] + 7 * shaft_normal[0],
                base_center[1] + 7 * shaft_normal[1],
            ),
            point(
                tip_x + UMBRELLA_TIP_LENGTH * shaft_direction[0],
                tip_y + UMBRELLA_TIP_LENGTH * shaft_direction[1],
            ),
        ],
        fill="#0C2034",
    )

    if show_rotation:
        rotation_arc_radius_x = 125
        rotation_arc_radius_y = 58
        draw.arc(
            box(
                canopy_x - rotation_arc_radius_x,
                canopy_y - rotation_arc_radius_y,
                canopy_x + rotation_arc_radius_x,
                canopy_y + rotation_arc_radius_y,
            ),
            start=205,
            end=332,
            fill=CORAL,
            width=sc(4),
        )
        arrow_angle = math.radians(332)
        arrow_tip = (
            canopy_x + rotation_arc_radius_x * math.cos(arrow_angle),
            canopy_y + rotation_arc_radius_y * math.sin(arrow_angle),
        )
        arrow_head(draw, arrow_tip, arrow_angle + math.pi / 2, fill=CORAL)
        draw.text(
            point(canopy_x - 100, max(108, canopy_y - 78)),
            "PRECESS",
            fill=CORAL,
            font=font(13, bold=True),
        )

    if show_downward_push:
        x = 459
        draw.line([point(x, 232), point(x, 327)], fill=BLUE, width=sc(4))
        arrow_head(draw, (x, 327), math.pi / 2, fill=BLUE)
        draw.text(point(381, 204), "DOWNWARD PUSH", fill=BLUE, font=font(13, bold=True))
        marker_y = 232 + 95 * push
        draw.ellipse(box(x - 7, marker_y - 7, x + 7, marker_y + 7), fill=BLUE)


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


def moment_state(
    regime: dict[str, object],
    progress: float,
) -> tuple[float, float]:
    """Return the continuous umbrella state, independent of circuit sampling."""

    return profile_state(regime, progress)


def umbrella_height(regime: dict[str, object], moment_radius: float) -> float:
    """Map the global deepest data point to a drop of one third of H0."""

    tilt = math.radians(float(regime["tilt_deg"]))
    initial_rotation = float(regime["moment_samples"][0][2])
    projected_axis_length = math.hypot(
        math.sin(tilt) * math.cos(initial_rotation),
        math.cos(tilt),
    )
    initial_tip_extension_y = (
        UMBRELLA_TIP_LENGTH * math.cos(tilt) / projected_axis_length
    )
    initial_height = (
        UMBRELLA_SHAFT_LENGTH * math.cos(tilt)
        + initial_tip_extension_y
        + INITIAL_TIP_CLEARANCE
    )
    initial_radius = float(regime["moment_samples"][0][1])
    relative_radius = max(
        MIN_RELATIVE_MOMENT_RADIUS,
        min(1.0, moment_radius / initial_radius),
    )
    contraction = (1.0 - relative_radius) / (1.0 - MIN_RELATIVE_MOMENT_RADIUS)
    return initial_height * (
        1.0 - MAX_UMBRELLA_DROP_FRACTION * contraction
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
    draw.line([point(cx - radius, cy), point(cx + radius, cy)], fill="#D9E1E7", width=sc(1))
    draw.line([point(cx, cy - radius), point(cx, cy + radius)], fill="#D9E1E7", width=sc(1))
    dashed_circle(draw, (cx, cy), radius, fill=INK, width=2)
    draw.ellipse(box(cx - 5, cy - 5, cx + 5, cy + 5), outline=INK, width=sc(2))
    draw.text(point(859, 421), "Re R", fill=MUTED, font=font(12))
    draw.text(point(545, 147), "Im R", fill=MUTED, font=font(12))

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

    draw.arc(box(833, 165, 889, 221), start=210, end=520, fill=CORAL, width=sc(3))
    arrow_angle = math.radians(520)
    arrow_head(
        draw,
        (861 + 28 * math.cos(arrow_angle), 193 + 28 * math.sin(arrow_angle)),
        arrow_angle + math.pi / 2,
        fill=CORAL,
        size=7,
    )
    draw.text(point(815, 226), "drift", fill=CORAL, font=font(11, bold=True))

    draw.line([point(817, 342), point(772, 318)], fill=BLUE, width=sc(3))
    arrow_head(
        draw,
        (772, 318),
        math.atan2(318 - 342, 772 - 817),
        fill=BLUE,
        size=7,
    )
    draw.text(point(817, 346), "spreading", fill=BLUE, font=font(11, bold=True))


def draw_footer(draw: ImageDraw.ImageDraw, regime: dict[str, object]) -> None:
    draw.rounded_rectangle(
        box(52, 477, 908, 525),
        radius=sc(20),
        fill=INK,
    )
    draw.rounded_rectangle(
        box(65, 485, 208, 517),
        radius=sc(14),
        fill=str(regime["color"]),
    )
    name = str(regime["name"])
    name_width = draw.textlength(name, font=font(13, bold=True))
    draw.text(
        point(136 - name_width / (2 * SCALE), 493),
        name,
        fill="#FFFFFF",
        font=font(13, bold=True),
    )
    draw.text(
        point(230, 491),
        str(regime["description"]),
        fill="#FFFFFF",
        font=font(16, bold=True),
    )


def render_frame(regime: dict[str, object], raw_progress: float) -> Image.Image:
    image = Image.new("RGB", (WIDTH * SCALE, HEIGHT * SCALE), PAPER)
    draw = ImageDraw.Draw(image)

    draw.rectangle(box(0, 100, 515, 467), fill=SKY)
    draw_header(draw)
    draw_sand(draw)

    # A continuous ease-in/ease-out avoids velocity jumps when each physical
    # demonstration starts and when it settles into the final held pose.
    motion_progress = ease(raw_progress)
    rotation, radius = moment_state(regime, motion_progress)
    canopy_height = umbrella_height(regime, radius)
    push = (
        float(regime["downward_push"])
        * ease(raw_progress)
        / MAX_DOWNWARD_PUSH
    )
    draw_umbrella(
        draw,
        rotation=rotation,
        tilt_deg=float(regime["tilt_deg"]),
        moment_radius=radius,
        canopy_height=canopy_height,
        push=push,
        show_rotation=(
            abs(
                float(regime["moment_samples"][-1][2])
                - float(regime["moment_samples"][0][2])
            )
            > 0.01
        ),
        show_downward_push=float(regime["downward_push"]) > 0.0,
    )
    draw_circular_moment(draw, regime=regime, progress=motion_progress)
    draw_footer(draw, regime)

    return image.resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)


def main() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    frames: list[Image.Image] = []
    for regime in REGIMES:
        for frame_index in range(FRAME_COUNT):
            raw_progress = min(frame_index / (MOVING_FRAMES - 1), 1.0)
            frames.append(render_frame(regime, raw_progress))

    palette = frames[0].quantize(colors=192)
    paletted = [
        frame.quantize(palette=palette, dither=Image.Dither.NONE) for frame in frames
    ]
    paletted[0].save(
        OUTPUT,
        save_all=True,
        append_images=paletted[1:],
        duration=FRAME_DURATION_MS,
        loop=0,
        disposal=2,
        optimize=True,
    )
    print(f"Wrote {OUTPUT} ({len(frames)} frames)")


if __name__ == "__main__":
    main()
