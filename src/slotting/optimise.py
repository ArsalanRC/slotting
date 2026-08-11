"""Measuring an assignment, and improving it.

`evaluate` is the only definition of "better" in this package: total metres
walked over the whole order history, under a named routing strategy. Everything
else is judged against that one number. It is worth being blunt about why the
number is defined this way rather than as an average or a per-order figure: a
warehouse pays for the total, and an average hides the effect of the long tail
of large orders, which is precisely where slotting earns its keep.

`optimise` starts from the frequency assignment and improves it with pairwise
swaps. Two things about that are worth knowing.

**It starts from the good heuristic, not from nothing.** Local search from a
random start would spend its whole budget re-deriving what an ABC analysis
gives away for free, and would land somewhere worse.

**It evaluates the real objective, not a proxy.** Every candidate swap is
scored by what it does to actual route length over actual orders. That is the
difference between this and frequency ranking, which optimises a proxy that
happens to correlate. Doing it naively would be far too slow, so swapping two
SKUs only re-costs the orders that mention one of them, which is usually a
handful out of thousands.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from slotting.assign import Assignment, frequency_assignment
from slotting.layout import Layout
from slotting.orders import Order, OrderHistory, Sku
from slotting.routing import ROUTE_STRATEGIES, RouteFn

__all__ = ["Result", "evaluate", "optimise"]


def _resolve(route: str | RouteFn) -> RouteFn:
    if callable(route):
        return route
    try:
        return ROUTE_STRATEGIES[route]
    except KeyError:
        known = ", ".join(sorted(ROUTE_STRATEGIES))
        raise ValueError(f"unknown routing strategy {route!r}; known: {known}") from None


def evaluate(
    layout: Layout,
    assignment: Assignment,
    history: OrderHistory,
    *,
    route: str | RouteFn = "s-shape",
) -> float:
    """Total metres walked across the whole history. Lower is better."""
    route_fn = _resolve(route)
    total = 0.0
    for order in history:
        total += route_fn(layout, assignment.locations_for(order.skus))
    return total


@dataclass(frozen=True, slots=True)
class Result:
    """What the search did, including the parts that did not go well."""

    assignment: Assignment
    baseline_metres: float
    optimised_metres: float
    swaps_applied: int
    passes: int
    converged: bool
    """False means the pass limit stopped the search rather than the search
    running out of improving swaps. The result is still valid and still better
    than the baseline; it just is not a local optimum, and saying so is the
    difference between a measurement and a claim."""

    @property
    def saved_metres(self) -> float:
        return self.baseline_metres - self.optimised_metres

    @property
    def improvement(self) -> float:
        """Fraction of walking removed, between 0 and 1."""
        if self.baseline_metres == 0:
            return 0.0
        return self.saved_metres / self.baseline_metres


def optimise(
    layout: Layout,
    history: OrderHistory,
    *,
    route: str | RouteFn = "s-shape",
    max_passes: int = 12,
    start: Assignment | None = None,
    on_pass: Callable[[int, float], None] | None = None,
) -> Result:
    """Improve a slotting by pairwise swaps, scored on real route length.

    Starts from `frequency_assignment` unless given something else, then
    repeatedly looks for a swap of two SKUs that lowers the total. Stops when a
    full pass finds nothing, or when `max_passes` runs out.

    First-improvement rather than best-improvement: the first swap that helps
    is taken immediately. Best-improvement would score every pair before moving
    and lands in much the same place for several times the work.
    """
    route_fn = _resolve(route)
    current = start.copy() if start is not None else frequency_assignment(layout, history)

    baseline = evaluate(layout, current, history, route=route_fn)

    # Which orders mention each SKU. This index is what makes the search
    # tractable: swapping two SKUs changes the cost of the orders that contain
    # one of them and nothing else, so a swap costs a few route calculations
    # rather than one per order in the history.
    touching: dict[Sku, list[Order]] = {}
    for order in history:
        for sku in order.skus:
            touching.setdefault(sku, []).append(order)

    skus = [s for s in history.skus if s in current]

    def affected(a: Sku, b: Sku) -> list[Order]:
        seen: dict[int, Order] = {}
        for order in touching.get(a, ()):
            seen[id(order)] = order
        for order in touching.get(b, ()):
            seen[id(order)] = order
        return list(seen.values())

    def cost_of(orders: list[Order]) -> float:
        return sum(route_fn(layout, current.locations_for(o.skus)) for o in orders)

    total = baseline
    swaps = 0
    passes = 0
    converged = False

    while passes < max_passes:
        passes += 1
        improved_this_pass = False

        for i, a in enumerate(skus):
            for b in skus[i + 1 :]:
                orders = affected(a, b)
                if not orders:
                    continue
                before = cost_of(orders)
                current.swap(a, b)
                after = cost_of(orders)
                if after < before:
                    total += after - before
                    swaps += 1
                    improved_this_pass = True
                else:
                    current.swap(a, b)

        if on_pass is not None:
            on_pass(passes, total)

        if not improved_this_pass:
            converged = True
            break

    # Recomputed from scratch rather than trusted. The running total is a sum
    # of thousands of deltas, and float error accumulates; more importantly, a
    # bug in the delta bookkeeping would otherwise report a saving that the
    # assignment does not actually deliver, which is the one failure this
    # package must not have.
    final = evaluate(layout, current, history, route=route_fn)

    return Result(
        assignment=current,
        baseline_metres=baseline,
        optimised_metres=final,
        swaps_applied=swaps,
        passes=passes,
        converged=converged,
    )
