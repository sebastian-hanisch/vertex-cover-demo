"""Orakel-Test vertex-cover-demo: exakte Überdeckung, LP-Wert und LP-Kern gegen unabhängige Rechenwege.

Orakel 1: `scipy.optimize.milp` (HiGHS, ganzzahliges Programm) für τ. Orakel 2: τ = n − α(G) mit α aus `networkx.max_weight_clique` auf dem Komplement. Orakel 3:
Aufzählen aller Teilmengen (n <= 16). Orakel 4: `scipy.optimize.linprog` für den LP-Wert. Orakel 5: `networkx.bipartite.hopcroft_karp_matching` für die Gleichheit τ = ν
(Satz von König) auf bipartiten Graphen. Verglichen werden WERTE; die gelieferte Überdeckung wird zusätzlich als Überdeckung dieser Größe geprüft."""

import numpy as np
import pytest

import vcv_algorithm as A
import vcv_scenario as S

nx = pytest.importorskip("networkx")
sp = pytest.importorskip("scipy.optimize")


def _milp_tau(adj):
    n = len(adj)
    edges = A.edge_list(adj)
    if not edges:
        return 0
    mat = np.zeros((len(edges), n))
    for i, (u, v) in enumerate(edges):
        mat[i, u] = mat[i, v] = 1.0
    res = sp.milp(np.ones(n), constraints=sp.LinearConstraint(mat, lb=np.ones(len(edges))), integrality=np.ones(n), bounds=sp.Bounds(0, 1))
    assert res.status == 0
    return round(res.fun)


def _lp_value(adj):
    n = len(adj)
    edges = A.edge_list(adj)
    if not edges:
        return 0.0
    mat = np.zeros((len(edges), n))
    for i, (u, v) in enumerate(edges):
        mat[i, u] = mat[i, v] = -1.0
    res = sp.linprog(np.ones(n), A_ub=mat, b_ub=-np.ones(len(edges)), bounds=[(0, 1)] * n, method="highs-ds")
    return float(res.fun)


def _alpha_nx(adj):
    G = nx.Graph()
    G.add_nodes_from(range(len(adj)))
    G.add_edges_from(A.edge_list(adj))
    _, size = nx.max_weight_clique(nx.complement(G), weight=None)
    return size


def _instances():
    """> 300 feste Instanzen: Zufall, Zeitfenster, Klassen, Wenige Verursacher, Baum, Gitter, Sonderfälle."""
    out = []
    for seed in range(90):
        out.append(("random", S.random_graph(4 + seed % 22, 5 + 10 * (seed % 9), seed).adj))
    for seed in range(50):
        out.append(("windows", S.window_graph(5 + seed % 20, 10 + 10 * (seed % 8), seed).adj))
    for seed in range(50):
        out.append(("classes", S.class_graph(5 + seed % 20, 10 + 10 * (seed % 8), seed).adj))
    for seed in range(50):
        out.append(("hubs", S.hub_graph(10 + seed % 30, 20 + 10 * (seed % 7), seed).adj))
    for seed in range(20):
        out.append(("tree", S.tree_graph(5 + seed * 3, seed).adj))
    for side in range(2, 8):
        out.append(("grid", S.grid_graph(side).adj))
    for n in range(1, 10):
        out.append(("empty", S.adjacency_from_edges(n, [])))
        out.append(("complete", S.adjacency_from_edges(n, [(i, j) for i in range(n) for j in range(i + 1, n)])))
        out.append(("star", S.adjacency_from_edges(n, [(0, i) for i in range(1, n)])))
    for n in range(3, 12):
        out.append(("cycle", S.adjacency_from_edges(n, [(i, (i + 1) % n) for i in range(n)])))
    for a in (3, 5, 7):
        out.append(("k_aa", S.complete_bipartite_graph(a).adj))
    for a in (4, 6, 8):
        out.append(("trap", S.trap_graph(a).adj))
    out.append(("two components", S.adjacency_from_edges(8, [(0, 1), (1, 2), (0, 2), (4, 5), (5, 6), (6, 7), (4, 7)])))
    return out


INSTANCES = _instances()


def test_there_are_more_than_300_instances():
    assert len(INSTANCES) > 300


def test_exact_cover_equals_milp_and_networkx_on_every_instance():
    for name, adj in INSTANCES:
        r = A.exact_cover(adj)
        ref = _milp_tau(adj)
        assert r.tau == ref, (name, len(adj))
        assert len(adj) - _alpha_nx(adj) == ref, (name, len(adj))
        assert len(r.cover) == ref and A.is_cover(adj, r.cover), name


def test_equal_brute_force_on_small_instances():
    checked = 0
    for name, adj in INSTANCES:
        if len(adj) > 14:
            continue
        n = len(adj)
        masks = [(1 << u) | (1 << v) for u, v in A.edge_list(adj)]
        best = min((bin(m).count("1") for m in range(1 << n) if all(m & e for e in masks)), default=0)
        assert A.exact_cover(adj).tau == best, name
        checked += 1
    assert checked >= 150


def test_lp_value_equals_linprog_on_every_instance():
    for name, adj in INSTANCES:
        assert abs(A.lp_value2(adj) / 2 - _lp_value(adj)) < 1e-7, (name, len(adj))


def test_lp_kernel_sum_equals_the_lp_value_and_every_decision_rule_agrees_with_milp():
    for name, adj in INSTANCES:
        forced, excluded, kernel = A.lp_kernel(adj)
        assert 2 * len(forced) + len(kernel) == A.lp_value2(adj), (name, len(adj))
        if len(adj) > 24:
            continue
        tau = _milp_tau(adj)
        for rule in ("edge", "degree", "degree_reduce", "buss"):
            for k in (max(tau - 1, 0), tau):
                d = A.decide(adj, k, rule, budget=20_000)
                if d.aborted:                                    # nur die Kantenregel (2^k) darf das Budget erreichen
                    assert rule == "edge" and d.answer is None, (name, rule, k, tau)
                    continue
                assert d.answer == (k >= tau), (name, rule, k, tau)


def test_koenig_on_bipartite_graphs_tau_equals_the_maximum_matching():
    for name, adj in INSTANCES:
        side, ok = A.bipartition(adj)
        if not ok:
            continue
        G = nx.Graph()
        G.add_nodes_from(range(len(adj)))
        G.add_edges_from(A.edge_list(adj))
        top = {v for v in range(len(adj)) if side[v] == 0}
        matching = nx.bipartite.hopcroft_karp_matching(G, top_nodes=top)
        nu = len(matching) // 2
        assert A.exact_cover(adj).tau == nu, name
        assert A.lp_value2(adj) == 2 * nu and A.lp_kernel(adj)[2] == [], name              # der LP ist auf bipartiten Graphen ganzzahlig, der Kern leer


def test_matching_cover_is_within_factor_two_and_lp_round_is_a_cover_on_every_instance():
    for name, adj in INSTANCES:
        tau = _milp_tau(adj)
        cover, m = A.matching_cover(adj)
        assert len(m) <= tau <= len(cover) <= 2 * tau, name
        g = A.greedy_degree_cover(adj)
        assert A.is_cover(adj, g) and len(g) >= tau, name
        r, forced, excluded, kernel = A.lp_round_cover(adj)
        assert A.is_cover(adj, r) and len(r) >= tau, name
