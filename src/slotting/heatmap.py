"""Drawing the warehouse, so the result is legible without reading a number.

A slotting result is a table of SKU against location, which nobody can judge.
The same result as a picture of the floor is obvious in a second: before, the
heat is scattered across every aisle; after, it is pulled into the aisles
nearest the dock. That is the entire reason this module exists, and it is why
the package ships a renderer at all rather than leaving it to the caller.

**SVG written as text, with no dependencies.** A plotting library would be the
obvious choice and would be wrong here. This runs on a warehouse server on a
scheduled job, and every dependency is a reason it will not run there when it
matters. SVG is a text format, the output is a few kilobytes, and it opens in
the browser everybody already has.

Heat is **picks per location**, not the number of SKUs. A location holding one
SKU picked four hundred times is hot; a location holding one picked twice is
not. Colouring by occupancy instead would draw a picture of the warehouse being
full, which is true of every warehouse and tells you nothing.
"""

from __future__ import annotations

from collections import Counter

from slotting.assign import Assignment
from slotting.layout import Layout, Location
from slotting.orders import OrderHistory

__all__ = ["heatmap_svg", "pick_density"]

# Warm sequential scale, pale to hot. Deliberately not a rainbow: a rainbow has
# no perceptual order, so a reader has to consult the legend for every cell
# rather than seeing "darker means busier" immediately.
_SCALE = [
    "#F5F0E6",
    "#F0DFC0",
    "#E8C79A",
    "#DDA974",
    "#CC8455",
    "#B35F41",
    "#8F3F33",
]


def pick_density(assignment: Assignment, history: OrderHistory) -> Counter[Location]:
    """How many picks land on each location, over the whole history."""
    counts: Counter[Location] = Counter()
    for order in history:
        for loc in assignment.locations_for(order.skus):
            counts[loc] += 1
    return counts


def _colour(value: int, peak: int) -> str:
    if peak <= 0 or value <= 0:
        return _SCALE[0]
    # Square-root rather than linear. Pick counts are heavily skewed, so a
    # linear ramp puts one fast mover at the top of the scale and renders
    # everything else as the same pale beige, which hides the whole middle of
    # the distribution: exactly the part slotting moves.
    frac = (value / peak) ** 0.5
    index = min(len(_SCALE) - 1, 1 + int(frac * (len(_SCALE) - 2)))
    return _SCALE[index]


def heatmap_svg(
    layout: Layout,
    assignment: Assignment,
    history: OrderHistory,
    *,
    title: str = "",
    cell: int = 14,
    peak: int | None = None,
) -> str:
    """Render the floor as an SVG string, hottest locations darkest.

    Aisles run left to right, bays run front to back with bay 0 at the top,
    which is the way somebody standing at the dock sees the building.

    `peak` fixes the top of the colour scale. Pass the same value when
    rendering a before and an after, or the two pictures use different scales
    and the comparison is meaningless while looking convincing. `cli` does
    exactly that.
    """
    density = pick_density(assignment, history)
    top = peak if peak is not None else max(density.values(), default=0)

    pad = 18
    label_h = 22 if title else 0
    # Two cells per aisle, one per side, with a gap between aisles for the walk.
    cols = layout.aisles * 2
    width = pad * 2 + cols * cell + (layout.aisles - 1) * 6
    height = pad * 2 + label_h + layout.bays_per_aisle * cell + 26

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img">',
        f'<rect width="{width}" height="{height}" fill="#FBF9F4"/>',
    ]
    if title:
        parts.append(
            f'<text x="{pad}" y="{pad + 12}" font-family="ui-monospace,monospace" '
            f'font-size="12" fill="#3A342B">{_escape(title)}</text>'
        )

    y0 = pad + label_h
    for aisle in range(layout.aisles):
        ax = pad + aisle * (cell * 2 + 6)
        for bay in range(layout.bays_per_aisle):
            for i, side in enumerate(("L", "R")):
                loc = Location(aisle, bay, side)
                fill = _colour(density.get(loc, 0), top)
                x = ax + i * cell
                y = y0 + bay * cell
                parts.append(
                    f'<rect x="{x}" y="{y}" width="{cell - 1}" height="{cell - 1}" '
                    f'fill="{fill}" stroke="#E2DACB" stroke-width="0.5"/>'
                )

    # The dock, drawn where it actually is, because "near the dock" is the whole
    # claim being made and a picture without it cannot be checked.
    dx = pad + layout.depot_aisle * (cell * 2 + 6)
    dy = y0 + layout.bays_per_aisle * cell + 4
    parts.append(f'<rect x="{dx}" y="{dy}" width="{cell * 2 - 1}" height="7" fill="#3A342B"/>')
    parts.append(
        f'<text x="{dx}" y="{dy + 20}" font-family="ui-monospace,monospace" '
        f'font-size="9" fill="#6B6152">DOCK</text>'
    )
    parts.append("</svg>")
    return "\n".join(parts)


def _escape(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
