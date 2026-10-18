"""Kern gegen Handrechnung (Mini-Instanzen) und Brute Force: jede Einheit einzeln, dann die Komposition."""

import pytest

import vcv_algorithm as A
import vcv_scenario as S


def tau_brute(adj):
    """Kleinste Überdeckung durch Aufzählen aller Teilmengen (nur für n <= 16; unabhängige Referenz ohne jede Rekursion)."""
    n = len(adj)
    masks = [(1 << u) | (1 << v) for u, v in A.edge_list(adj)]
    best = n
    for mask in range(1 << n):
        size = bin(mask).count("1")
        if size < best and all(mask & m for m in masks):
            best = size
    return best


# --- Hilfen -----------------------------------------------------------------------------------------------------------------------------------

def test_edge_list_is_sorted_and_unique(p4):
    assert A.edge_list(p4) == [(0, 1), (1, 2), (2, 3)]


def test_is_cover(p4):
    assert A.is_cover(p4, (1, 2)) and A.is_cover(p4, (0, 2)) and not A.is_cover(p4, (0, 3)) and A.is_cover(p4, (0, 1, 2, 3))
    assert A.is_cover(S.adjacency_from_edges(3, []), ())


def test_bipartition():
    side, ok = A.bipartition(S.adjacency_from_edges(4, [(0, 1), (1, 2), (2, 3)]))
    assert ok and side == [0, 1, 0, 1]
    assert A.bipartition(S.adjacency_from_edges(3, [(0, 1), (1, 2), (0, 2)])) == (None, False)
    assert A.bipartition(S.grid_graph(4).adj)[1] and A.bipartition(S.tree_graph(30, 1).adj)[1]


# --- Approximation ----------------------------------------------------------------------------------------------------------------------------

def test_maximal_matching_and_cover_by_hand(p4, c5):
    assert A.maximal_matching(p4) == [(0, 1), (2, 3)]
    assert A.matching_cover(p4) == ((0, 1, 2, 3), [(0, 1), (2, 3)])            # Faktor 2 gegen τ = 2
    assert A.maximal_matching(c5) == [(0, 1), (2, 3)] and A.matching_cover(c5)[0] == (0, 1, 2, 3)


def test_matching_bounds_hold_on_known_graphs(star, tri_pendant):
    for adj, tau in ((star, 1), (tri_pendant, 2)):
        m = len(A.maximal_matching(adj))
        assert m <= tau <= 2 * m


def test_matching_is_maximal_and_a_cover_of_size_two_m():
    for seed in range(20):
        g = S.random_graph(12, 30, seed)
        cover, m = A.matching_cover(g.adj)
        used = {x for e in m for x in e}
        assert len(cover) == 2 * len(m) and A.is_cover(g.adj, cover)
        assert all(u in used or v in used for u, v in A.edge_list(g.adj))      # maximal: keine Kante bleibt frei


def test_greedy_degree_cover_by_hand(p4, c5, star):
    assert A.greedy_degree_cover(p4) == [1, 2]
    assert A.greedy_degree_cover(c5) == [0, 2, 3]
    assert A.greedy_degree_cover(star) == [0]
    assert A.greedy_degree_cover(S.adjacency_from_edges(3, [])) == []


def test_greedy_trap_family_reproduces_the_growing_factor():
    sizes = {a: len(A.greedy_degree_cover(S.trap_graph(a).adj)) for a in (6, 12, 24)}
    assert sizes == {6: 8, 12: 23, 24: 60}
    for a in (6, 12, 24):
        g = S.trap_graph(a)
        assert tau_brute(g.adj) == a if g.n <= 16 else True
        assert A.exact_cover(g.adj).tau == a
        assert len(A.matching_cover(g.adj)[0]) == 2 * a


def test_complete_bipartite_matching_takes_everything():
    for a in (3, 5, 8):
        g = S.complete_bipartite_graph(a)
        assert len(A.matching_cover(g.adj)[0]) == 2 * a and A.exact_cover(g.adj).tau == a


# --- LP und Kern ------------------------------------------------------------------------------------------------------------------------------

def test_lp_value_by_hand(p4, c5, tri_pendant, star):
    assert A.lp_value2(p4) == 4 and A.lp_value2(c5) == 5 and A.lp_value2(tri_pendant) == 4 and A.lp_value2(star) == 2
    assert A.lp_value2(S.adjacency_from_edges(3, [])) == 0


def test_lp_solution_is_a_feasible_half_integral_solution_of_the_stated_value():
    for seed in range(30):
        g = S.random_graph(5 + seed % 12, 15 + 10 * (seed % 7), seed)
        x2, lp2 = A.lp_solution(g.adj)
        assert set(x2.values()) <= {0, 1, 2}
        assert all(x2[u] + x2[v] >= 2 for u, v in A.edge_list(g.adj))           # x_u + x_v >= 1, verdoppelt
        assert sum(x2.values()) == lp2


def test_nt_split_partitions_the_vertices():
    v1, v0, half = A.nt_split({0: 2, 1: 0, 2: 1, 3: 1, 4: 2})
    assert (v1, v0, half) == ([0, 4], [1], [2, 3])


def test_lp_kernel_by_hand(p4, c5, tri_pendant, star):
    forced, excluded, kernel = A.lp_kernel(p4)
    assert kernel == [] and len(forced) == 2 and A.is_cover(p4, forced) and not set(forced) & set(excluded)
    assert A.lp_kernel(c5) == ([], [], [0, 1, 2, 3, 4])                         # überall ½, keine Sondierung greift
    forced, excluded, kernel = A.lp_kernel(tri_pendant)
    assert kernel == [] and len(forced) == 2 and A.is_cover(tri_pendant, forced)
    assert A.lp_kernel(star) == ([0], [1, 2, 3], [])


def test_lp_kernel_is_empty_on_trees_and_grids_and_all_on_odd_cycles():
    assert A.lp_kernel(S.tree_graph(60, 1).adj)[2] == []
    assert A.lp_kernel(S.grid_graph(6).adj)[2] == []
    assert A.lp_kernel(S.adjacency_from_edges(7, [(i, (i + 1) % 7) for i in range(7)]))[2] == list(range(7))


@pytest.mark.parametrize("seed", range(30))
def test_nemhauser_trotter_decomposition_preserves_tau(seed):
    """τ(G) = |forced| + τ(G[Kern]), und die Zerlegung ist konsistent (kein Konflikt zwischen excluded und dem Rest außerhalb von forced)."""
    n = 5 + seed % 10
    g = S.random_graph(n, 10 + 10 * (seed % 8), seed)
    forced, excluded, kernel = A.lp_kernel(g.adj)
    assert set(forced) | set(excluded) | set(kernel) == set(range(n)) and not (set(forced) & set(excluded)) and not (set(forced) & set(kernel)) and not (set(excluded) & set(kernel))
    for v in excluded:
        assert g.adj[v] <= set(forced)
    sub = S.adjacency_from_edges(n, [(u, v) for u, v in A.edge_list(g.adj) if u in kernel and v in kernel])
    assert tau_brute(g.adj) == len(forced) + tau_brute(sub)


def test_lp_round_cover_is_a_cover_between_lp_and_n(c5):
    cover, forced, excluded, kernel = A.lp_round_cover(c5)
    assert cover == (0, 1, 2, 3, 4) and A.is_cover(c5, cover)
    for seed in range(15):
        g = S.random_graph(14, 25, seed)
        cover, forced, excluded, kernel = A.lp_round_cover(g.adj)
        assert A.is_cover(g.adj, cover) and 2 * len(forced) + len(kernel) == A.lp_value2(g.adj)


# --- Kernbildung ------------------------------------------------------------------------------------------------------------------------------

def test_buss_kernel_by_hand(p4, star):
    res, rest = A.buss_kernel(p4, 1)
    assert res.forced == (1, 2) and res.k_rest == -1 and res.edges == 0 and res.verdict is False      # nach 1 hat 2 den Grad 1 > k_rest = 0: auch 2 wird erzwungen
    res, rest = A.buss_kernel(p4, 2)
    assert res.forced == () and res.k_rest == 2 and res.edges == 3 and res.vertices == 4 and res.verdict is None
    res, rest = A.buss_kernel(star, 1)
    assert res.forced == (0,) and res.k_rest == 0 and res.edges == 0 and res.verdict is None


def test_buss_forces_high_degree_vertices_and_bounds_the_remaining_edges():
    g = S.hub_family(60, 3, 50, 1)
    res, rest = A.buss_kernel(g.adj, 8)
    assert len(res.forced) >= 3 and res.edges <= max(res.k_rest, 0) ** 2 or res.verdict is False
    assert all(not rest[v] for v in res.forced)


def test_reduce_degree_one_solves_a_tree_completely():
    g = S.tree_graph(50, 2)
    rest = [set(a) for a in g.adj]
    taken = A.reduce_degree_one(rest)
    assert all(not a for a in rest) and A.is_cover(g.adj, taken)


def test_cover_paths_and_cycles_by_formula():
    path = [set(), {2}, {1, 3}, {2, 4}, {3, 5}, {4}]                        # Pfad aus 5 Knoten (1 bis 5): ⌊5 / 2⌋ = 2
    cover = A.cover_paths_and_cycles(path)
    assert len(cover) == 2 and A.is_cover(S.adjacency_from_edges(6, [(1, 2), (2, 3), (3, 4), (4, 5)]), cover)
    for m in range(3, 10):
        cyc = [set() for _ in range(m)]
        for i in range(m):
            cyc[i] |= {(i + 1) % m, (i - 1) % m}
        c = A.cover_paths_and_cycles(cyc)
        assert len(c) == (m + 1) // 2 and A.is_cover(S.adjacency_from_edges(m, [(i, (i + 1) % m) for i in range(m)]), c)
    for m in range(2, 10):
        pth = [set() for _ in range(m)]
        for i in range(m - 1):
            pth[i].add(i + 1)
            pth[i + 1].add(i)
        c = A.cover_paths_and_cycles(pth)
        assert len(c) == m // 2 and A.is_cover(S.adjacency_from_edges(m, [(i, i + 1) for i in range(m - 1)]), c)


# --- Verzweigen -------------------------------------------------------------------------------------------------------------------------------

def test_decide_by_hand_on_the_path(p4):
    expect = {("edge", 1): (False, 3), ("edge", 2): (True, 4), ("degree", 1): (False, 1), ("degree", 2): (True, 1),
              ("degree_reduce", 1): (False, 1), ("degree_reduce", 2): (True, 1), ("buss", 1): (False, 0), ("buss", 2): (True, 1)}
    for (rule, k), (answer, nodes) in expect.items():
        d = A.decide(p4, k, rule)
        assert (d.answer, d.nodes) == (answer, nodes), (rule, k)
        if answer:
            assert len(d.cover) <= k and A.is_cover(p4, d.cover)


@pytest.mark.parametrize("rule", ["edge", "degree", "degree_reduce", "buss"])
def test_decide_matches_tau_on_random_graphs_for_every_k(rule):
    for seed in range(25):
        n = 5 + seed % 8
        g = S.random_graph(n, 15 + 10 * (seed % 7), seed)
        tau = tau_brute(g.adj)
        for k in range(max(0, tau - 2), tau + 2):
            d = A.decide(g.adj, k, rule)
            assert d.answer == (k >= tau), (rule, seed, k, tau)
            if d.answer:
                assert len(d.cover) <= k and A.is_cover(g.adj, d.cover)


def test_degree_one_rule_solves_a_tree_in_one_node():
    g = S.tree_graph(80, 3)
    tau = A.exact_cover(g.adj).tau
    d = A.decide(g.adj, tau, "degree_reduce")
    assert d.answer and d.nodes == 1 and not A.decide(g.adj, tau - 1, "degree_reduce").answer


def test_edge_rule_needs_exponentially_more_nodes_than_the_degree_rule():
    g = S.hub_family(40, 6, 50, 1)
    tau = A.exact_cover(g.adj).tau
    no_edge = A.decide(g.adj, tau - 1, "edge", budget=50_000)
    no_degree = A.decide(g.adj, tau - 1, "degree", budget=50_000)
    assert not no_degree.aborted and no_degree.answer is False
    assert no_edge.aborted or no_edge.nodes > 20 * no_degree.nodes


def test_budget_aborts_decide_and_exact():
    g = S.random_graph(40, 30, 1)
    d = A.decide(g.adj, 10, "edge", budget=50)
    assert d.aborted and d.answer is None and d.nodes == 51
    e = A.exact_cover(S.random_graph(40, 50, 1).adj, budget=3)
    assert e.aborted and e.tau is None and A.is_cover(S.random_graph(40, 50, 1).adj, e.cover) and e.lower >= 1


def test_unknown_rule_raises(p4):
    with pytest.raises(ValueError):
        A.decide(p4, 1, "magic")


# --- Exakt ------------------------------------------------------------------------------------------------------------------------------------

def test_exact_cover_by_hand(p4, c5, tri_pendant, star):
    assert A.exact_cover(p4).tau == 2 and A.exact_cover(c5).tau == 3 and A.exact_cover(tri_pendant).tau == 2 and A.exact_cover(star).tau == 1
    assert A.exact_cover(S.adjacency_from_edges(3, [])).tau == 0
    r = A.exact_cover(c5)
    assert r.lower == 3 and r.kernel == (0, 1, 2, 3, 4) and r.history[0][0] == 3


@pytest.mark.parametrize("seed", range(40))
def test_exact_cover_equals_brute_force(seed):
    n = 3 + seed % 12
    g = S.random_graph(n, 10 + 10 * (seed % 8), seed)
    r = A.exact_cover(g.adj)
    assert r.tau == tau_brute(g.adj) == len(r.cover) and A.is_cover(g.adj, r.cover) and r.lower <= r.tau
