"""Unit tests for Bandha Traversal Engine (Sarvatobhadra, Padmabandha, Gomutrika, Chakrabandha)."""
import pytest
from clio.decipherment.bandhas.base import TraversalDirection
from clio.decipherment.bandhas.chakrabandha import Chakrabandha
from clio.decipherment.bandhas.gomutrika import GomutrikaBandha
from clio.decipherment.bandhas.padmabandha import Padmabandha
from clio.decipherment.bandhas.sarvatobhadra import SarvatobhadraBandha
from clio.decipherment.bandhas.selector import bandha_engine
from clio.models.decipherment import BandhaPattern


def test_sarvatobhadra_concentric_spiral():
    """Verify Sarvatobhadra concentric spiral covers exactly 729 unique cells without duplicates."""
    sarv = SarvatobhadraBandha()
    trajectory = sarv.generate_trajectory(max_steps=729)

    assert trajectory.total_steps == 729
    assert len(trajectory.steps) == 729

    # Verify coordinate bounds [0, 26]
    coords = [(s.row, s.col) for s in trajectory.steps]
    is_valid, errors = sarv.validate_bounds(coords)
    assert is_valid is True
    assert len(errors) == 0

    # Concentric spiral must have 0 duplicates and 100% coverage
    duplicates = sarv.detect_duplicates(coords)
    assert len(duplicates) == 0

    coverage = sarv.calculate_coverage(coords)
    assert coverage["unique_cells"] == 729
    assert coverage["coverage_percentage"] == 100.0


def test_padmabandha_lotus_petals():
    """Verify Padmabandha 8-petal traversal starting from center (13, 13)."""
    padma = Padmabandha()
    trajectory = padma.generate_trajectory(
        start_coord=(13, 13),
        max_steps=64,
        params={"radius": 6},
    )

    assert trajectory.total_steps == 64
    coords = [(s.row, s.col) for s in trajectory.steps]

    # Verify bounds
    is_valid, errors = padma.validate_bounds(coords)
    assert is_valid is True

    # Center is repeatedly visited as petal loops return to karnika
    duplicates = padma.detect_duplicates(coords)
    assert len(duplicates) > 0  # Expected for lotus petal loopback

    # Test visualization payload structure
    vis = padma.to_visualization_payload(trajectory)
    assert vis["bandha"] == "PADMABANDHA"
    assert len(vis["points"]) == 64
    assert "x_percent" in vis["points"][0]
    assert "y_percent" in vis["points"][0]


def test_gomutrika_zigzag_wave():
    """Verify Gomutrika periodic wave trajectory across paired rows."""
    gomu = GomutrikaBandha()
    trajectory = gomu.generate_trajectory(max_steps=100)

    assert trajectory.total_steps == 100
    coords = [(s.row, s.col) for s in trajectory.steps]

    is_valid, errors = gomu.validate_bounds(coords)
    assert is_valid is True

    # Check alternating row pattern: r(0) == 0, r(1) == 1, r(2) == 0, r(3) == 1
    assert coords[0][0] == 0
    assert coords[1][0] == 1
    assert coords[2][0] == 0
    assert coords[3][0] == 1


def test_chakrabandha_wheel():
    """Verify Chakrabandha wheel spoke and rim expansion."""
    chakra = Chakrabandha()
    trajectory = chakra.generate_trajectory(start_coord=(13, 13), max_steps=128)

    assert trajectory.total_steps == 128
    coords = [(s.row, s.col) for s in trajectory.steps]
    is_valid, errors = chakra.validate_bounds(coords)
    assert is_valid is True


def test_bandha_engine_registry_and_direction():
    """Verify bandha engine handles direction reversal and supported registry."""
    supported = bandha_engine.get_supported_bandhas()
    assert BandhaPattern.SARVATOBHADRA in supported
    assert BandhaPattern.PADMABANDHA in supported
    assert BandhaPattern.GOMUTRIKA in supported
    assert BandhaPattern.CHAKRABANDHA in supported

    # Forward vs Reverse
    traj_fwd = bandha_engine.generate_trajectory(
        BandhaPattern.SARVATOBHADRA,
        max_steps=10,
        params={"direction": "FORWARD"},
    )
    traj_rev = bandha_engine.generate_trajectory(
        BandhaPattern.SARVATOBHADRA,
        max_steps=10,
        params={"direction": "REVERSE"},
    )

    fwd_first = (traj_fwd.steps[0].row, traj_fwd.steps[0].col)
    rev_last = (traj_rev.steps[-1].row, traj_rev.steps[-1].col)
    assert fwd_first == rev_last

