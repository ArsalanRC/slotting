"""What was actually picked, and what was picked alongside it.

Slotting is an argument about demand, so demand is the input. An order here is
just the set of SKUs on one pick list. That is a deliberately thin model: no
quantities, no timestamps, no priorities. Quantity changes how long somebody
stands at a bay and barely changes how far they walk, and walking is the whole
cost being optimised.

Two summaries come out of a history, and the difference between them is the
argument this package makes:

**Frequency** is how often each SKU is picked at all. It is what every
introduction to slotting starts with, and it is what an ABC analysis ranks on.

**Affinity** is how often two SKUs turn up on the same pick list. It is the
part frequency cannot see, and it is where the remaining money is, because a
picker walks a route rather than a set of independent errands.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Iterator
from dataclasses import dataclass

__all__ = ["Order", "OrderHistory", "Sku"]

Sku = str


@dataclass(frozen=True, slots=True)
class Order:
    """One pick list: the distinct SKUs somebody was sent to collect.

    Stored as a frozenset because a pick list has no meaningful order. The
    sequence a picker visits them in is a routing decision, made later and
    made against the layout, not something the order itself dictates.
    """

    skus: frozenset[Sku]

    def __init__(self, skus: Iterable[Sku]) -> None:
        object.__setattr__(self, "skus", frozenset(skus))

    def __len__(self) -> int:
        return len(self.skus)

    def __iter__(self) -> Iterator[Sku]:
        return iter(sorted(self.skus))


@dataclass(frozen=True, slots=True)
class OrderHistory:
    """A run of pick lists, and the two views of demand taken from it."""

    orders: tuple[Order, ...]

    def __init__(self, orders: Iterable[Order | Iterable[Sku]]) -> None:
        normalised = tuple(o if isinstance(o, Order) else Order(o) for o in orders)
        object.__setattr__(self, "orders", normalised)

    def __len__(self) -> int:
        return len(self.orders)

    def __iter__(self) -> Iterator[Order]:
        return iter(self.orders)

    @property
    def skus(self) -> list[Sku]:
        """Every SKU that appears anywhere, sorted.

        Sorted rather than in first-seen order, so a strategy that ranks by
        frequency and breaks ties by this list produces the same assignment
        whichever way the history was loaded.
        """
        return sorted({sku for order in self.orders for sku in order.skus})

    def frequency(self) -> Counter[Sku]:
        """How many orders each SKU appears on."""
        counts: Counter[Sku] = Counter()
        for order in self.orders:
            counts.update(order.skus)
        return counts

    def affinity(self) -> Counter[tuple[Sku, Sku]]:
        """How many orders each pair of SKUs appears on together.

        Keyed by the pair sorted, so `("A", "B")` and `("B", "A")` are one
        entry rather than two halves of the same count.

        This is quadratic in the size of an order and linear in the number of
        orders, which is fine: real pick lists are short. A history of a
        million orders averaging six lines is fifteen million increments, and
        a history of one order with a million lines is not a warehouse.
        """
        pairs: Counter[tuple[Sku, Sku]] = Counter()
        for order in self.orders:
            listed = sorted(order.skus)
            for i, a in enumerate(listed):
                for b in listed[i + 1 :]:
                    pairs[(a, b)] += 1
        return pairs

    def lines_per_order(self) -> float:
        """Mean number of distinct SKUs per pick list.

        Worth reporting next to any result, because it is the number that says
        whether affinity can help at all. A history of single-line orders has
        no affinity to find, and on one the optimiser cannot beat a plain
        frequency ranking. Saying so is more useful than a result that looks
        disappointing for no stated reason.
        """
        if not self.orders:
            return 0.0
        return sum(len(o) for o in self.orders) / len(self.orders)
