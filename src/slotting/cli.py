"""`slotting` on the command line.

The tool has to be runnable by somebody who has a CSV of last month's pick
lists and no interest in importing anything, because that is who actually has
the problem. So the whole thing is one command, and it prints the number that
matters first.

Exit codes follow the same reasoning as `recon`:

    0   ran, and found an improvement worth having
    1   ran, and found nothing worth doing
    2   could not run

Folding "no improvement" into 0 would let a scheduled job report success while
quietly doing nothing. Folding it into 2 would make every already-well-slotted
warehouse look broken. They are different answers and they get different codes.
"""

from __future__ import annotations

import argparse
import csv
import random
import sys
from pathlib import Path

from slotting.assign import frequency_assignment
from slotting.heatmap import heatmap_svg
from slotting.layout import Layout
from slotting.optimise import evaluate, optimise
from slotting.orders import Order, OrderHistory

__all__ = ["demo_history", "main", "read_orders"]


def read_orders(path: Path) -> OrderHistory:
    """One pick list per row, SKUs in the cells.

    Blank cells are skipped rather than treated as a SKU named "", which is
    what a spreadsheet export produces on every short row and which would
    otherwise become the most-picked item in the warehouse.
    """
    orders: list[Order] = []
    with path.open(newline="", encoding="utf-8-sig") as fh:
        for row in csv.reader(fh):
            skus = [cell.strip() for cell in row if cell.strip()]
            if skus:
                orders.append(Order(skus))
    if not orders:
        raise ValueError(f"{path} contained no orders")
    return OrderHistory(orders)


def demo_history(*, seed: int = 7) -> OrderHistory:
    """A synthetic warehouse, so the tool can be run with no data at all.

    Built to contain the effect the package is about rather than random noise:
    a few fast movers, and three pairs of items that are nearly always ordered
    together. A demo generated from a uniform distribution would show almost no
    improvement and would misrepresent the tool in the one place people try it.
    """
    rng = random.Random(seed)
    fast = [f"FAST-{i}" for i in range(6)]
    slow = [f"SLOW-{i}" for i in range(40)]
    pairs = [("KIT-A", "KIT-B"), ("KIT-C", "KIT-D"), ("KIT-E", "KIT-F")]

    orders: list[Order] = []
    for _ in range(600):
        line: list[str] = []
        line.extend(rng.sample(fast, rng.randint(1, 2)))
        if rng.random() < 0.45:
            line.extend(rng.choice(pairs))
        line.extend(rng.sample(slow, rng.randint(0, 3)))
        orders.append(Order(line))
    return OrderHistory(orders)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="slotting",
        description="Which SKU goes in which bin, so the picker walks less.",
    )
    parser.add_argument("orders", nargs="?", type=Path, help="CSV, one pick list per row")
    parser.add_argument("--demo", action="store_true", help="run on generated demand")
    parser.add_argument("--aisles", type=int, default=8)
    parser.add_argument("--bays", type=int, default=20, help="bays per aisle")
    parser.add_argument("--route", default="s-shape", choices=["s-shape", "return"])
    parser.add_argument("--max-passes", type=int, default=12)
    parser.add_argument("--before", type=Path, help="write the baseline heatmap here")
    parser.add_argument("--after", type=Path, help="write the optimised heatmap here")
    args = parser.parse_args(argv)

    if not args.demo and args.orders is None:
        parser.error("give a CSV of orders, or --demo")

    try:
        history = demo_history() if args.demo else read_orders(args.orders)
        layout = Layout(aisles=args.aisles, bays_per_aisle=args.bays)
        baseline = frequency_assignment(layout, history)
        base_metres = evaluate(layout, baseline, history, route=args.route)
        result = optimise(layout, history, route=args.route, max_passes=args.max_passes)
    except (OSError, ValueError) as exc:
        print(f"slotting: {exc}", file=sys.stderr)
        return 2

    print(f"orders            {len(history)}")
    print(f"SKUs              {len(history.skus)}")
    print(f"lines per order   {history.lines_per_order():.2f}")
    print(f"routing           {args.route}")
    print()
    print(f"frequency slotting {base_metres:>12,.0f} m")
    print(f"optimised          {result.optimised_metres:>12,.0f} m")
    print(f"saved              {result.saved_metres:>12,.0f} m   {result.improvement:.1%}")
    print()
    print(f"{result.swaps_applied} swaps over {result.passes} passes", end="")
    print("" if result.converged else "  (stopped at the pass limit, not a local optimum)")

    if history.lines_per_order() < 1.2:
        # Said out loud rather than left for the reader to infer from a small
        # number. Single-line orders have no co-occurrence to exploit, so a
        # disappointing result here is the correct answer, not a weak tool.
        print()
        print("Note: orders are nearly all single-line, so there is no affinity")
        print("to find and frequency slotting is already close to the best answer.")

    # One scale across both pictures. Rendering each against its own peak makes
    # two images that look equally hot and hides the whole result.
    if args.before or args.after:
        from slotting.heatmap import pick_density

        peak = max(
            max(pick_density(baseline, history).values(), default=0),
            max(pick_density(result.assignment, history).values(), default=0),
        )
        if args.before:
            args.before.write_text(
                heatmap_svg(layout, baseline, history, title="frequency slotting", peak=peak),
                encoding="utf-8",
            )
        if args.after:
            args.after.write_text(
                heatmap_svg(layout, result.assignment, history, title="optimised", peak=peak),
                encoding="utf-8",
            )

    return 0 if result.saved_metres > 0 else 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
