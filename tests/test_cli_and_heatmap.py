"""The command line and the picture.

Two things get tested here that look cosmetic and are not: that the two
heatmaps share one colour scale, and that the exit codes distinguish "nothing
to do" from "could not run".
"""

from __future__ import annotations

from pathlib import Path

import pytest

from slotting import Layout, Order, OrderHistory, frequency_assignment
from slotting.cli import demo_history, main, read_orders
from slotting.heatmap import heatmap_svg, pick_density


@pytest.fixture
def layout() -> Layout:
    return Layout(aisles=4, bays_per_aisle=6)


# -- reading -------------------------------------------------------------


def test_short_rows_do_not_invent_an_empty_sku(tmp_path: Path) -> None:
    """Every spreadsheet export has ragged rows.

    Without the guard, the trailing commas become a SKU named "" that appears
    on nearly every order, which would make it the hottest item in the
    warehouse and quietly wreck the result.
    """
    csv_file = tmp_path / "orders.csv"
    csv_file.write_text("A,B,\nC,,\nD,E,F\n", encoding="utf-8")

    history = read_orders(csv_file)
    assert "" not in history.skus
    assert history.skus == ["A", "B", "C", "D", "E", "F"]


def test_a_bom_does_not_corrupt_the_first_sku(tmp_path: Path) -> None:
    """Excel writes a BOM, and it lands on the first cell of the file."""
    csv_file = tmp_path / "orders.csv"
    csv_file.write_bytes("﻿SKU-1,SKU-2\n".encode())

    history = read_orders(csv_file)
    assert history.skus == ["SKU-1", "SKU-2"]


def test_an_empty_file_is_refused_rather_than_reported_as_perfect(
    tmp_path: Path,
) -> None:
    csv_file = tmp_path / "empty.csv"
    csv_file.write_text("\n\n", encoding="utf-8")
    with pytest.raises(ValueError, match="no orders"):
        read_orders(csv_file)


# -- heatmap -------------------------------------------------------------


def test_density_counts_picks_not_skus(layout: Layout) -> None:
    """A location holding one busy SKU is hot. Occupancy would say otherwise."""
    history = OrderHistory([Order(["A"]) for _ in range(10)] + [Order(["B"])])
    assignment = frequency_assignment(layout, history)

    density = pick_density(assignment, history)
    assert density[assignment.location("A")] == 10
    assert density[assignment.location("B")] == 1


def test_the_svg_is_self_contained_and_well_formed(layout: Layout) -> None:
    history = OrderHistory([Order(["A", "B"]) for _ in range(5)])
    svg = heatmap_svg(layout, frequency_assignment(layout, history), history, title="x")

    assert svg.startswith("<svg")
    assert svg.rstrip().endswith("</svg>")
    assert "http" not in svg.replace("http://www.w3.org/2000/svg", "")
    # One rect per location, plus the background and the dock.
    assert svg.count("<rect") == layout.capacity + 2


def test_a_title_cannot_break_out_of_the_markup(layout: Layout) -> None:
    history = OrderHistory([Order(["A"])])
    svg = heatmap_svg(
        layout, frequency_assignment(layout, history), history, title="<script>x</script>"
    )
    assert "<script>" not in svg
    assert "&lt;script&gt;" in svg


def test_a_shared_peak_makes_two_pictures_comparable(layout: Layout) -> None:
    """The test that stops the before and after lying.

    Rendered against their own peaks, a busy warehouse and a quiet one produce
    identically hot pictures. The darkest colour must only appear in the image
    that actually contains the busiest location.
    """
    busy = OrderHistory([Order(["A"]) for _ in range(100)])
    quiet = OrderHistory([Order(["A"]) for _ in range(2)])
    assignment = frequency_assignment(layout, busy)

    hottest = "#8F3F33"
    peak = 100
    busy_svg = heatmap_svg(layout, assignment, busy, peak=peak)
    quiet_svg = heatmap_svg(layout, assignment, quiet, peak=peak)

    assert hottest in busy_svg
    assert hottest not in quiet_svg

    # And without a shared peak, both go to full heat, which is the bug.
    assert hottest in heatmap_svg(layout, assignment, quiet)


# -- the command ---------------------------------------------------------


def test_demo_runs_and_finds_something(capsys: pytest.CaptureFixture[str]) -> None:
    code = main(["--demo", "--aisles", "6", "--bays", "10"])
    out = capsys.readouterr().out
    assert code == 0
    assert "saved" in out
    assert "optimised" in out


def test_demo_demand_actually_contains_the_effect() -> None:
    """A demo generated from noise would show nothing and misrepresent the tool."""
    history = demo_history()
    pairs = history.affinity()
    assert pairs[("KIT-A", "KIT-B")] > 50
    assert history.lines_per_order() > 1.5


def test_nothing_to_do_is_not_the_same_exit_code_as_success(
    capsys: pytest.CaptureFixture[str], tmp_path: Path
) -> None:
    """Single-line orders leave no affinity, so the honest answer is 1."""
    csv_file = tmp_path / "orders.csv"
    csv_file.write_text("\n".join(f"SKU-{i % 5}" for i in range(40)), encoding="utf-8")

    code = main([str(csv_file), "--aisles", "4", "--bays", "6"])
    out = capsys.readouterr().out
    assert code == 1
    assert "single-line" in out


def test_a_file_that_does_not_exist_exits_two(
    capsys: pytest.CaptureFixture[str], tmp_path: Path
) -> None:
    code = main([str(tmp_path / "missing.csv")])
    assert code == 2
    assert "slotting:" in capsys.readouterr().err


def test_it_writes_both_heatmaps(tmp_path: Path) -> None:
    before, after = tmp_path / "b.svg", tmp_path / "a.svg"
    code = main(
        [
            "--demo",
            "--aisles",
            "6",
            "--bays",
            "10",
            "--before",
            str(before),
            "--after",
            str(after),
        ]
    )
    assert code == 0
    for path in (before, after):
        assert path.exists()
        assert path.read_text(encoding="utf-8").startswith("<svg")
