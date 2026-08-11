# slotting

**English** · [Deutsch](./README.de.md)

Which SKU goes in which bin, so the picker walks less.

Rank your SKUs by how often they are picked, put the popular ones nearest the
dock. That is the standard answer and it is a good one. It is also solving the
wrong problem.

A picker does not walk to one item and come back. They walk **one route**
through a whole pick list and return to the dock. So the cost is route length
per order, not the sum of the distances to individual items. Those are
different numbers, and they disagree in a way that matters: two SKUs that
always appear on the same order belong near each other even when neither is
individually popular. No amount of frequency ranking will ever find that,
because frequency cannot see co-occurrence at all.

This measures what a warehouse actually pays and searches against it.

```python
from slotting import Layout, OrderHistory, optimise

layout = Layout(aisles=8, bays_per_aisle=20)
history = OrderHistory(orders)  # each order is the SKUs on one pick list

result = optimise(layout, history)
print(f"{result.improvement:.1%} less walking")
```

## Try it without any data

```bash
git clone https://github.com/ArsalanRC/slotting.git
cd slotting && pip install -e .
slotting --demo --before before.svg --after after.svg
```

```
orders            600
SKUs              52
lines per order   3.98
routing           s-shape

frequency slotting       27,947 m
optimised                26,202 m
saved                     1,745 m   6.2%

77 swaps over 4 passes
```

Two SVG heatmaps of the floor come out, on one shared colour scale so they can
honestly be compared. Real data instead of the demo:

```bash
slotting orders.csv --aisles 8 --bays 20 --after after.svg
```

One pick list per row, SKUs in the cells. That is what every WMS export already
looks like.

## What it will not tell you

**It never claims an optimum.** Slotting is a quadratic assignment problem and
it is NP-hard. `optimise` returns a better assignment and says how much better.
`result.converged` tells you whether the search ran out of improving swaps or
ran out of passes, because those are different answers.

**Six percent is a realistic number, not a disappointing one.** Published
slotting work lands between about five and twenty percent depending on how
badly the warehouse started. Anything advertising fifty percent is either
measuring against a random baseline or measuring the wrong thing.

**If your orders are single-line, this cannot help you** and it says so in the
output. One SKU per order means no co-occurrence anywhere, so frequency ranking
is already close to right. That is a property of your demand, not a weakness in
the tool, and a package that reported a double-digit improvement there would be
measuring noise.

## The three parts worth knowing about

**Distance is computed on the aisle graph, never in a straight line.** Two bays
facing each other across a rack are about a metre apart and thirty metres apart
on foot. Euclidean distance is not an approximation of that, it is a different
number that happens to be smaller, and it is smallest exactly where it is most
wrong. There is a test that fails if this ever regresses.

**Routing is a choice and it changes the answer.** `s-shape` is the default
because it is what most warehouses actually run: enter every aisle holding a
pick, sweep it, move on. Its cost depends on which aisles you touch and barely
on how many items sit in each, which is precisely why co-locating related SKUs
pays. `return` is the alternative. `optimal_route` exists too, by brute force,
and nothing calls it except the tests, which use it to state how far the
heuristics sit from the true floor rather than assuming they are close.

**The search scores the real objective.** Every candidate swap is evaluated by
what it does to actual route length over actual orders, not by a proxy. Doing
that naively would be far too slow, so swapping two SKUs only re-costs the
orders that mention one of them. The running total is then thrown away and
recomputed from scratch before reporting, because a bug in the delta
bookkeeping would otherwise report a saving the assignment does not deliver,
and that is the one failure this tool must not have.

## Exit codes

| | |
|---|---|
| `0` | ran, and found an improvement worth having |
| `1` | ran, and found nothing worth doing |
| `2` | could not run |

Folding "nothing to do" into `0` lets a scheduled job report success while
quietly doing nothing. Folding it into `2` makes every already-well-slotted
warehouse look broken.

## Install

Python 3.10 or newer. **No runtime dependencies**, on purpose: this runs on a
warehouse server on a scheduled job, and every dependency is a reason it will
not run there when it matters. The heatmap is SVG written as text rather than a
plotting library.

```bash
git clone https://github.com/ArsalanRC/slotting.git
cd slotting && pip install -e ".[dev]"
pytest
```

50 tests, `ruff` and `mypy --strict` clean, on Python 3.10 through 3.13.

## Author

Arsalan Khadim, software architect and full-stack engineer.
Warehouse and ERP integration is the day job, which is where this problem comes
from.

- [Portfolio](https://arsalanrc.github.io)
- [LinkedIn](https://www.linkedin.com/in/muhammad-arsalan-khadim-b87550259/)
- [GitHub](https://github.com/ArsalanRC)

## Licence

MIT. See [LICENSE](./LICENSE).
