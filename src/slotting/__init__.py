"""slotting: which SKU goes in which bin, so the picker walks less.

The argument, in one paragraph. Ranking SKUs by how often they are picked and
putting the popular ones nearest the dock is the standard answer, and it is a
good one. It is also solving the wrong problem, because it minimises the sum of
distances to individual items while a picker walks a single route through a
whole pick list and comes back. Two SKUs that always appear on the same order
belong near each other even when neither is individually hot, and no amount of
frequency ranking will ever discover that.

So this package measures what a warehouse actually pays, total metres over a
real order history under a real routing policy, and searches against it.

    from slotting import Layout, OrderHistory, optimise

    layout = Layout(aisles=8, bays_per_aisle=20)
    history = OrderHistory(orders)
    result = optimise(layout, history)

    print(f"{result.improvement:.1%} less walking")

What it will not do is promise an optimum. Slotting is a quadratic assignment
problem and it is NP-hard, so `optimise` returns a better assignment and says
how much better, never a best one. `Result.converged` tells you whether the
search ran out of improving swaps or ran out of passes.
"""

from __future__ import annotations

from slotting.assign import Assignment, frequency_assignment, random_assignment
from slotting.layout import Layout, Location
from slotting.optimise import Result, evaluate, optimise
from slotting.orders import Order, OrderHistory
from slotting.routing import optimal_route, return_route, s_shape

__all__ = [
    "Assignment",
    "Layout",
    "Location",
    "Order",
    "OrderHistory",
    "Result",
    "evaluate",
    "frequency_assignment",
    "optimal_route",
    "optimise",
    "random_assignment",
    "return_route",
    "s_shape",
]

__version__ = "0.1.0"
