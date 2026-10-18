"""Szenarien: Generatoren sind deterministisch, erzeugen gültige Graphen und treffen ihre Zielgrößen."""

import math

import pytest

import vcv_algorithm as A
import vcv_constants as C
import vcv_scenario as S


def _valid(g):
    assert len(g.adj) == g.n == len(g.positions) == len(g.labels)
    for v in range(g.n):
        assert v not in g.adj[v]
        for w in g.adj[v]:
            assert v in g.adj[w]


@pytest.mark.parametrize("gt", list(C.GRAPH_TYPES))
@pytest.mark.parametrize("density", [C.DENSITY_MIN, 50, C.DENSITY_MAX])
def test_every_graph_type_is_a_valid_graph_at_the_slider_edges(gt, density):
    for n in (C.N_MIN, C.N_MAX):
        _valid(S.build_graph(gt, n, density, 7))


@pytest.mark.parametrize("gt", list(C.GRAPH_TYPES))
def test_same_seed_same_graph_different_seed_different_graph(gt):
    a, b, c = S.build_graph(gt, 30, 50, 3), S.build_graph(gt, 30, 50, 3), S.build_graph(gt, 30, 50, 4)
    assert a.adj == b.adj and a.adj != c.adj


def test_random_graph_density_is_close_to_the_target_on_average():
    for d in (10, 50, 90):
        mean = sum(S.random_graph(30, d, s).m for s in range(40)) / 40 / (30 * 29 / 2)
        assert abs(mean - d / 100) < 0.03, d


def test_hub_graph_has_few_vertices_covering_almost_everything():
    for seed in range(10):
        g = S.hub_graph(40, 50, seed)
        hubs = -(-40 // 20)
        assert hubs == 2
        non_hub_edges = [(u, v) for u, v in g.edges() if u >= hubs and v >= hubs]
        assert len(non_hub_edges) <= hubs                                   # höchstens so viele Zufallskonflikte wie Verursacher
        assert A.exact_cover(g.adj).tau <= hubs + len(non_hub_edges)


def test_hub_family_edge_count_and_the_random_comparison_graph_has_exactly_as_many_edges():
    for h in (2, 8, 16):
        g = S.hub_family(100, h, 40, 5)
        r = S.random_graph_m(100, g.m, 5)
        assert r.m == g.m and r.n == 100
        _valid(g)
        _valid(r)
    assert S.random_graph_m(10, 1000, 1).m == 45                              # mehr Kanten als Paare: alle Paare


def test_trap_graph_shape():
    for a in (4, 6, 12):
        g = S.trap_graph(a)
        left_degrees = [len(g.adj[v]) for v in range(a)]
        assert all(d >= 1 for d in left_degrees)
        assert g.n == a + sum(a // j for j in range(2, a + 1))
        _valid(g)


def test_complete_bipartite_graph_shape():
    g = S.complete_bipartite_graph(5)
    assert g.n == 10 and g.m == 25 and all(len(x) == 5 for x in g.adj)


def test_window_length_formula_matches_the_overlap_probability():
    for d in (10, 30, 50, 90):
        assert math.isclose(1 - (1 - S.window_length(d)) ** 2, d / 100)


def test_class_graph_vertices_of_the_same_class_have_the_same_neighbours_outside_their_class():
    g = S.class_graph(30, 50, 11)
    classes = [int(label.split("Klasse ")[1]) for label in g.labels]
    twins = {}
    for v in range(30):
        twins.setdefault(classes[v], []).append(frozenset(g.adj[v] - {w for w in range(30) if classes[w] == classes[v]}))
    for members in twins.values():
        assert len(set(members)) == 1


def test_tree_grid_scale_free_sizes():
    assert S.tree_graph(50, 1).m == 49
    g = S.grid_graph(6)
    assert g.n == 36 and g.m == 2 * 6 * 5
    sf = S.scale_free_graph(200, 3, 1)
    assert sf.n == 200 and sf.m == 3 * (200 - 3) and max(len(a) for a in sf.adj) > 10


def test_complement_is_an_involution():
    g = S.random_graph(12, 40, 2)
    assert S.complement(S.complement(g.adj)) == g.adj


def test_adjacency_from_edges_ignores_loops_and_duplicates():
    assert S.adjacency_from_edges(3, [(0, 1), (1, 0), (1, 1), (0, 1)]) == (frozenset({1}), frozenset({0}), frozenset())


def test_unknown_graph_type_raises():
    with pytest.raises(ValueError):
        S.build_graph("nope", 10, 50, 1)
