"""The claim the README makes, tested.

The important test here is `test_affinity_is_found_where_frequency_cannot_see_it`.
It is built so that a frequency ranking provably cannot reach the right answer,
and the optimum is known by construction rather than by trusting the search.
"""

from __future__ import annotations

import pytest

from slotting import (
    Layout,
    Order,
    OrderHistory,
    evaluate,
    frequency_assignment,
    optimise,
    random_assignment,
)


@pytest.fixture
def layout() -> Layout:
    return Layout(aisles=6, bays_per_aisle=10)


@pytest.fixture
def narrow() -> Layout:
    """Three aisles holding two locations each: exactly six slots.

    Deliberately tight. In a roomy warehouse the whole catalogue fits in the
    first aisle, frequency ranking is already optimal, and there is nothing for
    any optimiser to find. That is a real property of slotting rather than a
    flaw, and it is why the scenario below has to force the pairs apart before
    it can show anything.
    """
    return Layout(aisles=3, bays_per_aisle=1)


def _paired_history() -> OrderHistory:
    """Three pairs that always travel together, and never mix.

    Two things are arranged on purpose.

    Every SKU is picked exactly the same number of times, so frequency carries
    no information at all and a frequency ranking is reduced to breaking ties
    on the name.

    The names are chosen so that alphabetical order splits every pair. The
    pairs are A with D, B with E, C with F, so ranking by name puts A next to
    B, which never share an order. If the pairs were called A1 and A2 the
    tie-break would co-locate them by luck and the test would pass without the
    search doing anything.
    """
    orders: list[Order] = []
    for _ in range(20):
        orders.append(Order(["A", "D"]))
        orders.append(Order(["B", "E"]))
        orders.append(Order(["C", "F"]))
    return OrderHistory(orders)


def test_frequency_beats_random_on_ordinary_demand(layout: Layout) -> None:
    """The baseline is not a straw man, and this says so out loud."""
    orders = []
    for i in range(200):
        hot = f"SKU-{i % 3}"
        cold = f"SKU-{20 + (i % 40)}"
        orders.append(Order([hot, cold]))
    history = OrderHistory(orders)

    rand = evaluate(layout, random_assignment(layout, history, seed=7), history)
    freq = evaluate(layout, frequency_assignment(layout, history), history)
    assert freq < rand


def test_frequency_ranking_provably_splits_every_pair(narrow: Layout) -> None:
    """The premise of the next test, asserted rather than assumed.

    If this ever stops holding, the test below would pass because the baseline
    was already correct rather than because the search did anything, which is
    the failure mode that makes an optimiser look good for free.
    """
    history = _paired_history()
    freq = frequency_assignment(narrow, history)
    for a, b in (("A", "D"), ("B", "E"), ("C", "F")):
        assert freq.location(a).aisle != freq.location(b).aisle


def test_affinity_is_found_where_frequency_cannot_see_it(narrow: Layout) -> None:
    """The whole argument of the package, in one assertion.

    Six SKUs, each picked twenty times, in three pairs that never mix. The
    counts are identical, so frequency ranking has nothing to go on and breaks
    ties on the name, which splits every pair.

    The search has to notice that co-occurrence is what matters and put each
    pair in one aisle. If it ever stops doing that, this goes red.
    """
    history = _paired_history()

    freq = frequency_assignment(narrow, history)
    before = evaluate(narrow, freq, history)

    result = optimise(narrow, history)

    assert result.optimised_metres < before
    assert result.improvement > 0.0
    # Each pair in one aisle, which is the only thing s-shape routing rewards.
    for a, b in (("A", "D"), ("B", "E"), ("C", "F")):
        assert result.assignment.location(a).aisle == result.assignment.location(b).aisle


def test_the_reported_saving_is_real(narrow: Layout) -> None:
    """Guards the delta bookkeeping in the search.

    `optimise` maintains a running total from thousands of deltas and then
    recomputes from scratch. If those two ever disagree, the tool is reporting
    a saving the assignment does not deliver, which is the one failure it must
    not have. Re-evaluating the returned assignment independently is the check.
    """
    history = _paired_history()
    result = optimise(narrow, history)

    independent = evaluate(narrow, result.assignment, history)
    assert independent == pytest.approx(result.optimised_metres)
    assert result.saved_metres == pytest.approx(
        result.baseline_metres - result.optimised_metres
    )


def test_optimise_never_returns_something_worse_than_it_started_with(
    narrow: Layout,
) -> None:
    history = _paired_history()
    result = optimise(narrow, history)
    assert result.optimised_metres <= result.baseline_metres


def test_it_says_when_it_ran_out_of_passes_rather_than_converging(
    narrow: Layout,
) -> None:
    """`converged` has to mean something, so it is tested in both states."""
    history = _paired_history()

    stopped = optimise(narrow, history, max_passes=1)
    assert stopped.passes == 1
    assert stopped.converged is False

    finished = optimise(narrow, history, max_passes=50)
    assert finished.converged is True
    assert finished.passes < 50


def test_single_line_orders_leave_nothing_for_affinity_to_find(
    layout: Layout,
) -> None:
    """An honest negative result, and the reason `lines_per_order` is reported.

    With one SKU per order there is no co-occurrence anywhere, so frequency
    ranking is already right and the search should find little or nothing. A
    package that claimed a double-digit improvement here would be measuring
    noise.
    """
    orders = [Order([f"SKU-{i % 10}"]) for i in range(100)]
    history = OrderHistory(orders)
    assert history.lines_per_order() == pytest.approx(1.0)

    result = optimise(layout, history)
    assert result.improvement == pytest.approx(0.0, abs=1e-9)


def test_discontinued_skus_do_not_stop_the_run(layout: Layout) -> None:
    """Real histories mention SKUs that no longer exist."""
    history = OrderHistory([Order(["A", "B"]), Order(["A", "GONE"])])
    assignment = frequency_assignment(layout, OrderHistory([Order(["A", "B"])]))
    assert "GONE" not in assignment

    cost = evaluate(layout, assignment, history)
    assert cost > 0


def test_random_baseline_is_reproducible(narrow: Layout) -> None:
    """An improvement figure measured against a moving baseline is not a figure."""
    history = _paired_history()
    a = random_assignment(narrow, history, seed=42)
    b = random_assignment(narrow, history, seed=42)
    assert a.as_dict() == b.as_dict()


def test_a_warehouse_too_small_for_the_catalogue_is_refused() -> None:
    tiny = Layout(aisles=1, bays_per_aisle=1)  # 2 locations
    history = OrderHistory([Order(["A", "B", "C"])])
    with pytest.raises(ValueError, match="will not fit"):
        frequency_assignment(tiny, history)


def test_unknown_routing_strategy_is_named(layout: Layout) -> None:
    history = _paired_history()
    with pytest.raises(ValueError, match="s-shape"):
        evaluate(layout, frequency_assignment(layout, history), history, route="zigzag")
