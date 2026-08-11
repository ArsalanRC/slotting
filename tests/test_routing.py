"""Route cost, and the property the whole package rests on."""

from __future__ import annotations

import pytest

from slotting import Layout, Location, optimal_route, return_route, s_shape


@pytest.fixture
def small() -> Layout:
    return Layout(aisles=4, bays_per_aisle=10)


def test_an_empty_pick_list_is_free(small: Layout) -> None:
    assert s_shape(small, []) == 0.0
    assert return_route(small, []) == 0.0
    assert optimal_route(small, []) == 0.0


def test_route_length_is_not_the_sum_of_the_distances(small: Layout) -> None:
    """The mistake the package exists to correct.

    Four items in one aisle against four items spread across four aisles. The
    sum of individual distances from the dock is deliberately made *larger* for
    the clustered list, and yet the walk is shorter. Any cost model that scores
    these the other way round is measuring the wrong thing.
    """
    clustered = [Location(3, b, "L") for b in (6, 7, 8, 9)]
    spread = [Location(a, 0, "L") for a in range(4)]

    sum_clustered = sum(small.distance_from_depot(loc) for loc in clustered)
    sum_spread = sum(small.distance_from_depot(loc) for loc in spread)
    assert sum_clustered > sum_spread

    assert s_shape(small, clustered) < s_shape(small, spread)


def test_s_shape_barely_notices_extra_items_in_an_aisle_it_already_enters(
    small: Layout,
) -> None:
    """This property is why affinity beats frequency, so it is pinned down.

    Once the picker is sweeping an aisle, the items in it are free. Adding a
    fifth item to an aisle already on the route costs nothing; adding it to a
    new aisle costs a detour.
    """
    # Two aisles, both swept end to end. The route is already committed to
    # walking the whole of aisle 1.
    base = [Location(0, 9, "L"), Location(1, 9, "L")]
    extra_same_aisle = [*base, Location(1, 3, "R")]
    extra_new_aisle = [*base, Location(3, 3, "R")]

    # Free, exactly, because the picker was walking past it anyway.
    assert s_shape(small, extra_same_aisle) == pytest.approx(s_shape(small, base))
    # A new aisle is not free, and that gap is the money slotting recovers.
    assert s_shape(small, extra_new_aisle) > s_shape(small, base)


def test_s_shape_turns_round_in_the_last_aisle_when_that_is_shorter(
    small: Layout,
) -> None:
    """A single pick just inside aisle 0 should not cost a full sweep."""
    shallow = [Location(0, 0, "L")]  # y = 0.6
    # In and out: 1.2m. A full sweep would be the 12m depth plus the walk home.
    assert s_shape(small, shallow) == pytest.approx(1.2)


def test_return_route_wins_on_shallow_picks_and_loses_on_deep_ones(
    small: Layout,
) -> None:
    shallow = [Location(a, 0, "L") for a in range(3)]
    deep = [Location(a, 9, "L") for a in range(3)]

    assert return_route(small, shallow) < s_shape(small, shallow)
    assert return_route(small, deep) > s_shape(small, deep)


def test_the_heuristics_are_never_shorter_than_the_true_optimum(
    small: Layout,
) -> None:
    """A heuristic that beats the exact answer is a heuristic with a bug.

    This is the guard that would catch a cost model quietly skipping part of
    the walk, which is the easiest way to produce impressive savings that do
    not exist.
    """
    lists = [
        [Location(0, 1, "L"), Location(2, 8, "R")],
        [Location(0, 0, "L"), Location(1, 5, "L"), Location(3, 9, "R")],
        [Location(a, b, "L") for a, b in ((0, 2), (1, 7), (2, 3), (3, 8))],
    ]
    for locs in lists:
        best = optimal_route(small, locs)
        assert s_shape(small, locs) >= best - 1e-9
        assert return_route(small, locs) >= best - 1e-9


def test_optimal_route_refuses_a_list_it_cannot_finish(small: Layout) -> None:
    """Better to refuse than to appear to hang for hours."""
    too_many = [Location(a, b, "L") for a in range(4) for b in range(3)]
    with pytest.raises(ValueError, match="heuristic"):
        optimal_route(small, too_many)


def test_a_single_aisle_warehouse_is_just_there_and_back(small: Layout) -> None:
    strip = Layout(aisles=1, bays_per_aisle=10)
    assert s_shape(strip, [Location(0, 4, "L")]) == pytest.approx(2 * strip.y(4))
