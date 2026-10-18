"""Gemeinsame Fixtures: die Mini-Instanzen, an denen jede Einheit von Hand geprüft wird (DEMO-PLAYBOOK §1b). Kante = Konflikt."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from vcv_scenario import adjacency_from_edges  # noqa: E402


@pytest.fixture
def p4():
    """Pfad 0-1-2-3: τ = 2 ({0, 2} oder {1, 2} oder {1, 3} ...), bipartit, LP ganzzahlig."""
    return adjacency_from_edges(4, [(0, 1), (1, 2), (2, 3)])


@pytest.fixture
def c5():
    """Fünfeck: τ = 3, LP-Wert 2,5 (überall ½), Matching-Verfahren nimmt 4 Knoten, Greedy 3."""
    return adjacency_from_edges(5, [(i, (i + 1) % 5) for i in range(5)])


@pytest.fixture
def tri_pendant():
    """Dreieck {0, 1, 2} plus Pendelknoten 3 an 2: τ = 2, LP-Wert 2."""
    return adjacency_from_edges(4, [(0, 1), (0, 2), (1, 2), (2, 3)])


@pytest.fixture
def star():
    """Stern mit Mitte 0 und drei Blättern: τ = 1."""
    return adjacency_from_edges(4, [(0, 1), (0, 2), (0, 3)])
