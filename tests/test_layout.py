"""Distance on the aisle graph.

Every number this package reports is built on `Layout.distance`, so these tests
are written against hand-computed metres rather than against whatever the code
happened to return.
"""

from __future__ import annotations

import pytest

from slotting import Layout, Location


@pytest.fixture
def small() -> Layout:
    # 4 aisles, 10 bays. Aisle pitch 3.6m, bay width 1.2m, so the aisle runs
    # 12m deep and the aisles sit at x = 0, 3.6, 7.2, 10.8.
    return Layout(aisles=4, bays_per_aisle=10)


def test_geometry_is_what_the_docstring_claims(small: Layout) -> None:
    assert small.depth == pytest.approx(12.0)
    assert small.x(0) == pytest.approx(0.0)
    assert small.x(3) == pytest.approx(10.8)
    # Bay centres, so bay 0 sits half a bay in rather than on the cross aisle.
    assert small.y(0) == pytest.approx(0.6)
    assert small.y(9) == pytest.approx(11.4)


def test_within_one_aisle_is_the_difference_in_depth(small: Layout) -> None:
    a = Location(1, 0, "L")
    b = Location(1, 9, "L")
    assert small.distance(a, b) == pytest.approx(10.8)


def test_side_of_the_aisle_does_not_change_the_distance(small: Layout) -> None:
    """Crossing a 3.6m aisle is a step, and modelling it would be false precision."""
    assert small.distance(Location(2, 4, "L"), Location(2, 4, "R")) == pytest.approx(0.0)


def test_a_picker_cannot_walk_through_a_rack(small: Layout) -> None:
    """The test this whole module exists for.

    Two bays facing each other across a rack are about a metre apart in a
    straight line. On foot they are the length of the aisle out, along the
    cross aisle, and the length of the aisle back. If this ever returns
    something near 3.6, the distance function has started measuring Euclidean
    distance and every result in the package is quietly wrong.
    """
    a = Location(0, 5, "R")
    b = Location(1, 5, "L")
    # Both at y = 6.6, in a 12m aisle. Out the front is 6.6 + 6.6; out the back
    # is 5.4 + 5.4, which wins. Plus 3.6 across.
    assert small.distance(a, b) == pytest.approx(3.6 + 10.8)
    assert small.distance(a, b) > 14.0


def test_the_cheaper_end_of_the_aisle_wins(small: Layout) -> None:
    near_front = Location(0, 0, "L")  # y = 0.6
    also_front = Location(2, 0, "L")  # y = 0.6
    # Front: 0.6 + 0.6 = 1.2. Back: 11.4 + 11.4 = 22.8. Front wins.
    assert small.distance(near_front, also_front) == pytest.approx(7.2 + 1.2)

    near_back = Location(0, 9, "L")  # y = 11.4
    also_back = Location(2, 9, "L")
    # Back: 0.6 + 0.6 = 1.2 this time.
    assert small.distance(near_back, also_back) == pytest.approx(7.2 + 1.2)


def test_distance_is_symmetric(small: Layout) -> None:
    a, b = Location(0, 2, "L"), Location(3, 7, "R")
    assert small.distance(a, b) == pytest.approx(small.distance(b, a))


def test_depot_distance_counts_the_walk_in(small: Layout) -> None:
    assert small.distance_from_depot(Location(0, 0, "L")) == pytest.approx(0.6)
    assert small.distance_from_depot(Location(3, 9, "L")) == pytest.approx(10.8 + 11.4)


def test_locations_come_back_nearest_the_dock_first(small: Layout) -> None:
    locs = small.locations()
    assert len(locs) == small.capacity == 80
    distances = [small.distance_from_depot(loc) for loc in locs]
    assert distances == sorted(distances)


def test_locations_are_deterministic(small: Layout) -> None:
    """Two runs must agree, or every strategy that assigns by rank is unstable."""
    assert small.locations() == small.locations()


@pytest.mark.parametrize(
    "kwargs",
    [
        {"aisles": 0, "bays_per_aisle": 5},
        {"aisles": 3, "bays_per_aisle": 0},
        {"aisles": 3, "bays_per_aisle": 5, "depot_aisle": 3},
    ],
)
def test_impossible_warehouses_are_refused(kwargs: dict[str, int]) -> None:
    with pytest.raises(ValueError):
        Layout(**kwargs)
