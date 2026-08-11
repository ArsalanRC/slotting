"""Which SKU sits in which location, and the two obvious ways to decide.

An assignment is a one-to-one map from SKU to location. One SKU per location is
a simplification, and a real warehouse holds a fast mover in several, but it
keeps the comparison honest: every strategy here is handed the same warehouse
and the same demand, so the only thing that differs is where things went.

Two baselines live here, and neither is a straw man.

`random_assignment` is what you get with no policy at all, which is also what
you get after two years of putting each new SKU wherever there was a gap. It is
the state most warehouses are actually in.

`frequency_assignment` is the textbook answer: rank by pick frequency, put the
most-picked SKU nearest the dock. It is a genuinely good heuristic and it is
what an ABC analysis produces. The point of this package is not that it is bad.
The point is that it optimises the sum of individual distances while the thing
you pay is route length per order, and those are not the same number.
"""

from __future__ import annotations

import random
from collections.abc import Iterable, Iterator, Mapping

from slotting.layout import Layout, Location
from slotting.orders import OrderHistory, Sku

__all__ = ["Assignment", "frequency_assignment", "random_assignment"]


class Assignment:
    """A one-to-one map from SKU to storage location.

    Mutable, and swap-based, because the local search in `optimise` performs
    tens of thousands of swaps and rebuilding a frozen map each time would make
    the search the slowest part of a package about efficiency.
    """

    def __init__(self, layout: Layout, mapping: Mapping[Sku, Location]) -> None:
        locations = list(mapping.values())
        if len(set(locations)) != len(locations):
            raise ValueError("two SKUs were given the same location")
        unknown = set(locations) - set(layout.locations())
        if unknown:
            raise ValueError(f"locations not in this layout: {sorted(map(str, unknown))}")

        self.layout = layout
        self._by_sku: dict[Sku, Location] = dict(mapping)

    def __len__(self) -> int:
        return len(self._by_sku)

    def __iter__(self) -> Iterator[Sku]:
        return iter(self._by_sku)

    def __contains__(self, sku: object) -> bool:
        return sku in self._by_sku

    def location(self, sku: Sku) -> Location:
        """Where this SKU lives."""
        return self._by_sku[sku]

    def locations_for(self, skus: Iterable[Sku]) -> list[Location]:
        """Where these SKUs live, skipping any the assignment does not hold.

        Skipping rather than raising is deliberate. A history nearly always
        mentions a SKU that has since been discontinued, and refusing to
        evaluate the whole run because of one dead line would make the tool
        unusable on real data. The count of skipped SKUs is worth reporting at
        the call site, which `optimise.evaluate` does.
        """
        out = []
        for sku in skus:
            loc = self._by_sku.get(sku)
            if loc is not None:
                out.append(loc)
        return out

    def swap(self, a: Sku, b: Sku) -> None:
        """Exchange the locations of two SKUs, in place."""
        self._by_sku[a], self._by_sku[b] = self._by_sku[b], self._by_sku[a]

    def copy(self) -> Assignment:
        """An independent copy, so a search can be run without losing the input."""
        return Assignment(self.layout, self._by_sku)

    def as_dict(self) -> dict[Sku, Location]:
        """A plain dictionary, for reporting and for the heatmap."""
        return dict(self._by_sku)


def _check_capacity(layout: Layout, skus: list[Sku]) -> list[Location]:
    slots = layout.locations()
    if len(skus) > len(slots):
        raise ValueError(f"{len(skus)} SKUs will not fit in {len(slots)} locations")
    return slots


def random_assignment(
    layout: Layout, history: OrderHistory, *, seed: int | None = None
) -> Assignment:
    """Scatter the SKUs, with no regard for demand at all.

    `seed` is not optional in practice. Every improvement figure this package
    reports is measured against a baseline, so a baseline that changes between
    runs makes the headline number unreproducible, and an unreproducible
    improvement figure is a sales claim rather than a measurement.
    """
    skus = history.skus
    slots = _check_capacity(layout, skus)
    rng = random.Random(seed)
    chosen = rng.sample(slots, len(skus))
    # strict: the sample is drawn at exactly len(skus), so a length mismatch
    # here would be a bug rather than something to absorb quietly.
    return Assignment(layout, dict(zip(skus, chosen, strict=True)))


def frequency_assignment(layout: Layout, history: OrderHistory) -> Assignment:
    """The textbook heuristic: most-picked SKU nearest the dock.

    Ties break on the SKU name so the result is stable. Without that, two runs
    over the same data can produce different assignments and therefore
    different costs, purely from dictionary ordering, which is exactly the kind
    of quiet non-determinism that makes a benchmark meaningless.
    """
    skus = history.skus
    slots = _check_capacity(layout, skus)
    counts = history.frequency()
    ranked = sorted(skus, key=lambda s: (-counts[s], s))
    # Not strict, and deliberately so: `slots` is every location in the
    # warehouse and is normally longer than the catalogue. Truncating to the
    # SKUs is the behaviour wanted, and `_check_capacity` has already refused
    # the one case where the lengths are wrong in the direction that matters.
    return Assignment(layout, dict(zip(ranked, slots, strict=False)))
