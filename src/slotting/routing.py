"""How far somebody walks to pick one order.

This module is the reason the package exists, so it is worth being exact about
what it claims.

**Route length is not the sum of the distances.** That is the mistake every
first attempt at slotting makes, and it is the mistake that makes frequency
ranking look optimal when it is not. A picker walks one route through all the
locations on the list and comes back. Two items in the same aisle cost barely
more than one. Two items in aisles at opposite ends cost the width of the
warehouse whether or not either one is popular.

Three cost models, and the choice between them matters more than it looks:

`s_shape`
    Enter every aisle that holds a pick, traverse it end to end, move along the
    cross aisle to the next one. This is what most warehouses actually run,
    because it needs no thought from the picker: go in, sweep, come out. Its
    cost depends on **which aisles** are touched and almost not at all on how
    many items sit in each. That property is the whole argument of this
    package, so it is the default.

`return_route`
    Enter each aisle from the front, walk to the deepest pick, walk back out.
    Better than S-shape on sparse lists, worse on dense ones, and the crossover
    is around a third of the aisle occupied.

`optimal_route`
    The real shortest tour, by brute force. Far too slow for anything but small
    lists, and no warehouse runs it, because it asks a person to follow an
    arbitrary order. It exists so the tests can say how far off the heuristics
    are rather than assuming they are close.

Every function here takes the layout and a set of locations, and returns metres.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from itertools import pairwise, permutations

from slotting.layout import Layout, Location

__all__ = ["ROUTE_STRATEGIES", "RouteFn", "optimal_route", "return_route", "s_shape"]

RouteFn = Callable[[Layout, Iterable[Location]], float]


def s_shape(layout: Layout, locations: Iterable[Location]) -> float:
    """Traverse every aisle holding a pick, alternating direction.

    Starts and ends at the dock. Aisles are visited in index order, which is
    what a picker does when the pick list is sorted by location, and sorting
    the pick list by location is the one piece of warehouse software everybody
    already has.

    The last aisle is the exception. If turning round inside it and coming back
    out the front is shorter than sweeping it, the route does that instead.
    That refinement is standard, and leaving it out overstates the cost of
    every order whose deepest pick is near the front.
    """
    locs = list(locations)
    if not locs:
        return 0.0

    deepest: dict[int, float] = {}
    for loc in locs:
        y = layout.y(loc.bay)
        if y > deepest.get(loc.aisle, -1.0):
            deepest[loc.aisle] = y

    aisles = sorted(deepest)
    cost = 0.0
    x = layout.depot_x
    at_back = False

    for i, aisle in enumerate(aisles):
        ax = layout.x(aisle)
        cost += abs(ax - x)
        x = ax

        last = i == len(aisles) - 1
        if last and not at_back:
            # Turning round inside the final aisle rather than sweeping it. Only
            # available from the front, because coming in from the back and
            # returning to the back would leave the walk home from the far end.
            sweep = layout.depth + abs(layout.depot_x - ax)
            turn = 2 * deepest[aisle] + abs(layout.depot_x - ax)
            cost += min(sweep, turn)
            return cost

        cost += layout.depth
        at_back = not at_back

    # Ended at the far end of the last aisle: walk back along the cross aisle,
    # then down the depot aisle to the dock.
    cost += abs(layout.depot_x - x)
    if at_back:
        cost += layout.depth
    return cost


def return_route(layout: Layout, locations: Iterable[Location]) -> float:
    """Enter each aisle from the front, reach the deepest pick, come back out.

    The picker never uses the back cross aisle, which is why this wins on
    sparse lists: sweeping a whole aisle to collect one item near the front is
    a lot of walking for one item.
    """
    locs = list(locations)
    if not locs:
        return 0.0

    deepest: dict[int, float] = {}
    for loc in locs:
        y = layout.y(loc.bay)
        if y > deepest.get(loc.aisle, -1.0):
            deepest[loc.aisle] = y

    aisles = sorted(deepest)
    cost = 0.0
    x = layout.depot_x
    for aisle in aisles:
        ax = layout.x(aisle)
        cost += abs(ax - x) + 2 * deepest[aisle]
        x = ax
    cost += abs(layout.depot_x - x)
    return cost


def optimal_route(layout: Layout, locations: Iterable[Location]) -> float:
    """The genuinely shortest tour from the dock and back, by brute force.

    Exact, and exponential. It enumerates every ordering, so it is usable up to
    about eight distinct locations and hopeless past ten. Nothing in the
    optimiser calls it. The tests do, to state how far the heuristics sit from
    the floor instead of asserting that they are good.

    Raises on anything large rather than appearing to hang, because a routine
    that silently takes four hours is worse than one that refuses.
    """
    locs = sorted(set(locations))
    if not locs:
        return 0.0
    if len(locs) > 9:
        raise ValueError(
            f"optimal_route enumerates {len(locs)}! orderings; use a heuristic above 9"
        )

    best = float("inf")
    for order in permutations(locs):
        cost = layout.distance_from_depot(order[0])
        for a, b in pairwise(order):
            cost += layout.distance(a, b)
            if cost >= best:
                break
        else:
            cost += layout.distance_from_depot(order[-1])
            if cost < best:
                best = cost
    return best


ROUTE_STRATEGIES: dict[str, RouteFn] = {
    "s-shape": s_shape,
    "return": return_route,
}
"""The strategies a caller can name. `optimal_route` is deliberately absent:
it is a measuring stick, not something to run a warehouse on."""
