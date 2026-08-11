"""Demand, summarised two ways."""

from __future__ import annotations

import pytest

from slotting import Order, OrderHistory


def test_an_order_is_a_set_of_skus() -> None:
    """A pick list has no order. The sequence is a routing decision, made later."""
    assert Order(["A", "B", "A"]).skus == frozenset({"A", "B"})
    assert len(Order(["A", "B", "A"])) == 2


def test_history_accepts_bare_iterables() -> None:
    history = OrderHistory([["A", "B"], Order(["B", "C"])])
    assert len(history) == 2
    assert history.skus == ["A", "B", "C"]


def test_skus_come_back_sorted_not_in_first_seen_order() -> None:
    """Rank-based strategies break ties on this list, so it has to be stable."""
    a = OrderHistory([Order(["Z"]), Order(["A"])]).skus
    b = OrderHistory([Order(["A"]), Order(["Z"])]).skus
    assert a == b == ["A", "Z"]


def test_frequency_counts_orders_not_units() -> None:
    history = OrderHistory([Order(["A", "B"]), Order(["A"]), Order(["A", "C"])])
    counts = history.frequency()
    assert counts["A"] == 3
    assert counts["B"] == 1
    assert counts["C"] == 1


def test_affinity_keys_each_pair_once() -> None:
    """`(A, B)` and `(B, A)` are one fact, not two halves of one."""
    history = OrderHistory([Order(["B", "A"]), Order(["A", "B"])])
    pairs = history.affinity()
    assert pairs[("A", "B")] == 2
    assert ("B", "A") not in pairs


def test_affinity_sees_what_frequency_cannot() -> None:
    """Two SKUs picked equally often, one pair always together."""
    history = OrderHistory(
        [Order(["A", "B"]) for _ in range(5)] + [Order(["C"]) for _ in range(5)]
    )
    counts = history.frequency()
    assert counts["A"] == counts["C"] == 5
    pairs = history.affinity()
    assert pairs[("A", "B")] == 5
    assert pairs[("A", "C")] == 0


def test_lines_per_order_says_whether_affinity_can_help_at_all() -> None:
    assert OrderHistory([]).lines_per_order() == 0.0
    assert OrderHistory([Order(["A"]), Order(["B"])]).lines_per_order() == pytest.approx(1.0)
    assert OrderHistory([Order(["A", "B"]), Order(["C"])]).lines_per_order() == pytest.approx(
        1.5
    )
