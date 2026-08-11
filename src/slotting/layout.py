"""The warehouse floor, and how far it is between two places on it.

Everything in this package rests on one function: the walking distance between
two storage locations. Get it wrong and every number the optimiser reports is
confidently false, because the search will happily minimise a distance nobody
walks.

**A picker cannot walk through a rack.** Two bays facing each other across a
rack are about a metre apart in a straight line and thirty metres apart on
foot, because getting from one to the other means walking to the end of the
aisle, along a cross aisle, and back down the next one. Euclidean distance is
not an approximation of that. It is a different number that happens to be
smaller, and it is smallest exactly where it is most wrong.

So distance here is computed on the aisle graph. Within one aisle it is the
difference in depth. Between two aisles the route has to leave through one end
or the other, and the cheaper end wins.

Geometry, all in metres:

    depot                  cross aisle (front, y = 0)
      +----+----+----+----+----+
      |    |    |    |    |     each vertical gap is an aisle
      |    |    |    |    |     each side of a gap is a run of bays
      |    |    |    |    |
      +----+----+----+----+----+
                             cross aisle (back, y = depth)

Bays are numbered from the front, so bay 0 is the one nearest the dock. Aisles
are numbered from the depot, so aisle 0 is the one the depot sits at the mouth
of. Both of those are conventions rather than requirements, but they are the
conventions the rest of the package assumes when it talks about "near".
"""

from __future__ import annotations

from dataclasses import dataclass

__all__ = ["Layout", "Location"]


@dataclass(frozen=True, slots=True, order=True)
class Location:
    """One storage position: which aisle, how far down it, and which side.

    Ordered so that sorting a set of locations gives a stable, readable
    sequence. The order is aisle, then bay, then side, which is roughly the
    order somebody walking the warehouse would meet them.
    """

    aisle: int
    bay: int
    side: str = "L"
    """`"L"` or `"R"`. Which face of the aisle the bay is on."""

    def __str__(self) -> str:
        return f"A{self.aisle}-B{self.bay}-{self.side}"


@dataclass(frozen=True, slots=True)
class Layout:
    """A rectangular warehouse: parallel aisles, cross aisles at both ends.

    This is the standard single-block layout, which is what most small and
    mid-sized distribution centres actually are. It is deliberately not a
    general graph. A general graph would be more flexible and would make every
    routing heuristic below either wrong or much slower, and the heuristics are
    the part worth being exact about.
    """

    aisles: int
    bays_per_aisle: int

    aisle_pitch: float = 3.6
    """Centre-to-centre distance between neighbouring aisles, in metres."""

    bay_width: float = 1.2
    """Depth of one bay along the aisle, in metres."""

    depot_aisle: int = 0
    """Which aisle mouth the dock sits at. The route starts and ends here."""

    def __post_init__(self) -> None:
        if self.aisles < 1:
            raise ValueError("a warehouse needs at least one aisle")
        if self.bays_per_aisle < 1:
            raise ValueError("an aisle needs at least one bay")
        if not 0 <= self.depot_aisle < self.aisles:
            raise ValueError(f"depot_aisle {self.depot_aisle} is not an aisle in this layout")

    # -- geometry ---------------------------------------------------------

    # Plain properties, not `cached_property`: this is a slotted dataclass, so
    # there is no instance `__dict__` for a cache to live in and the decorator
    # raises at first access. Both are one multiplication anyway.
    @property
    def depth(self) -> float:
        """Distance from the front cross aisle to the back one, in metres.

        A bay is measured at its centre, so the run of bays is one bay short of
        the full aisle. The half bay of clearance at each end is what the aisle
        actually has, and including it is what makes a full traverse cost more
        than walking to the last bay.
        """
        return self.bays_per_aisle * self.bay_width

    def x(self, aisle: int) -> float:
        """Horizontal position of an aisle centreline, in metres."""
        return aisle * self.aisle_pitch

    def y(self, bay: int) -> float:
        """Depth of a bay centre from the front cross aisle, in metres."""
        return (bay + 0.5) * self.bay_width

    @property
    def depot_x(self) -> float:
        """Horizontal position of the dock. It sits on the front cross aisle."""
        return self.x(self.depot_aisle)

    # -- distance ---------------------------------------------------------

    def distance(self, a: Location, b: Location) -> float:
        """Walking distance between two locations, in metres.

        Same aisle: straight down it. Different aisles: out one end, along the
        cross aisle, back down the other. The side of the aisle a bay is on
        does not change the distance, because crossing an aisle is a step and
        the aisle is 3.6 metres wide at most.
        """
        if a.aisle == b.aisle:
            return abs(self.y(a.bay) - self.y(b.bay))

        across = abs(self.x(a.aisle) - self.x(b.aisle))
        ya, yb = self.y(a.bay), self.y(b.bay)
        via_front = ya + yb
        via_back = (self.depth - ya) + (self.depth - yb)
        return across + min(via_front, via_back)

    def distance_from_depot(self, loc: Location) -> float:
        """Walking distance from the dock to a location, in metres."""
        across = abs(self.depot_x - self.x(loc.aisle))
        return across + self.y(loc.bay)

    # -- enumeration ------------------------------------------------------

    def locations(self) -> list[Location]:
        """Every storage position, nearest the dock first.

        The order matters to callers that assign by rank, because "the first
        `n` locations" has to mean "the `n` nearest the dock" for that to be
        the strategy it claims to be.

        Ties are broken by the location's own ordering rather than left to the
        sort, so two runs on the same layout produce the same list. A strategy
        that quietly depended on dictionary insertion order would still look
        deterministic on one machine.
        """
        out = [
            Location(aisle, bay, side)
            for aisle in range(self.aisles)
            for bay in range(self.bays_per_aisle)
            for side in ("L", "R")
        ]
        out.sort(key=lambda loc: (self.distance_from_depot(loc), loc))
        return out

    @property
    def capacity(self) -> int:
        """How many SKUs this warehouse can hold, one per location."""
        return self.aisles * self.bays_per_aisle * 2
