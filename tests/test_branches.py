"""Zweig-Tests (Nullspalten-Lehre): jede Regel, jedes Verfahren, jede Sondierung weicht auf mindestens einer Instanz von ihrer Nachbarvariante ab;
die Invarianten gelten; die Rechengrenzen greifen; jeder Regler an jeder Grenze."""

import vcv_algorithm as A
import vcv_constants as C
import vcv_evaluation as ev
import vcv_scenario as S


def test_each_decision_rule_differs_from_the_next_on_at_least_one_instance():
    g = S.hub_family(40, 6, 50, 2)
    tau = A.exact_cover(g.adj).tau
    nodes = {rule: A.decide(g.adj, tau - 1, rule, budget=5000).nodes for rule in C.RULES}
    assert len({nodes["edge"], nodes["degree"], nodes["degree_reduce"]}) == 3
    differs = False
    for seed in range(10):
        h = S.hub_family(100, 16, 40, 100000 + seed)
        t = A.exact_cover(h.adj).tau
        differs |= A.decide(h.adj, t - 1, "buss").nodes != A.decide(h.adj, t - 1, "degree_reduce").nodes
    assert differs                                                          # der Buss-Kern spart auf mindestens einer Instanz Knoten


def test_degree_one_rule_changes_the_node_count_on_sparse_graphs_and_the_buss_kernel_on_hubs():
    g = S.random_graph(40, 8, 3)
    tau = A.exact_cover(g.adj).tau
    assert A.decide(g.adj, tau, "degree_reduce").nodes < A.decide(g.adj, tau, "degree").nodes
    hubs = S.hub_family(100, 8, 40, 1)
    res, rest = A.buss_kernel(hubs.adj, 20)
    assert res.forced and res.edges < hubs.m


def test_lp_kernel_probing_changes_the_kernel_on_a_graph_with_a_perfect_matching():
    """Ohne Sondierung bliebe auf einem Pfad der ganze Graph im Kern (überall ½); die Sondierung entscheidet ihn."""
    p = S.adjacency_from_edges(6, [(i, i + 1) for i in range(5)])
    x2, lp2 = A.lp_solution(p)
    assert set(x2.values()) == {1} and lp2 == 6                              # erste König-Lösung: überall ½
    assert A.lp_kernel(p)[2] == []


def test_lp_kernel_is_larger_when_every_vertex_has_degree_at_least_three():
    g = S.scale_free_graph(200, 4, 100000)
    assert len(A.lp_kernel(g.adj)[2]) == 200 and A.lp_kernel(S.scale_free_graph(200, 2, 100000).adj)[2] == []


def test_matching_edge_order_matters_and_greedy_tie_break_is_effective():
    adj = S.adjacency_from_edges(6, [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5)])
    assert len(A.matching_cover(adj)[0]) == 6                                # Kanten (0,1), (2,3), (4,5)
    shifted = S.adjacency_from_edges(6, [(0, 5), (5, 1), (1, 4), (4, 2), (2, 3)])    # derselbe Pfad, andere Nummern: Matching (0,5), (1,4), (2,3)
    assert len(A.matching_cover(shifted)[0]) == 6
    g = S.adjacency_from_edges(4, [(0, 1), (2, 3)])
    assert A.greedy_degree_cover(g) == [0, 2]                                # Gleichstand: kleinster Index zuerst


def test_the_greedy_trap_makes_greedy_worse_than_the_matching_guarantee():
    g = S.trap_graph(24)
    greedy, matching = len(A.greedy_degree_cover(g.adj)), len(A.matching_cover(g.adj)[0])
    assert greedy > matching > A.exact_cover(g.adj).tau


def test_budget_aborts_decide_exact_and_the_analysis_reports_it():
    g = S.random_graph(40, 30, 1)
    d = A.decide(g.adj, 10, "edge", budget=50)
    assert d.aborted and d.answer is None and d.nodes == 51
    a = ev.analyse(ev.Settings(graph_type="random", n=40, density=50, seed=35, rule="edge"), node_budget=500)
    assert a.decisions["edge"].aborted and a.decisions["edge"].nodes == 501
    e = A.exact_cover(S.random_graph(60, 20, 1).adj, budget=3)
    assert e.aborted and e.tau is None and e.lower >= 1 and A.is_cover(S.random_graph(60, 20, 1).adj, e.cover)


def test_analysis_falls_back_to_the_greedy_size_when_the_exact_search_aborts():
    a = ev.analyse(ev.Settings(graph_type="random", n=60, density=20, seed=35, delta=-1), exact_budget=2)
    assert a.tau is None and a.k_reference == "greedy" and a.k == len(a.covers["greedy"]) - 1


def test_every_configuration_runs_on_every_graph_type_at_the_slider_edges():
    for gt in C.GRAPH_TYPES:
        for n in (C.N_MIN, C.N_MAX):
            for d in (C.DENSITY_MIN, C.DENSITY_MAX):
                for delta in (C.DELTA_MIN, C.DELTA_MAX):
                    a = ev.analyse(ev.Settings(graph_type=gt, n=n, density=d, delta=delta), node_budget=20_000, exact_budget=50_000)
                    assert A.is_cover(a.graph.adj, a.covers["matching"]) and A.is_cover(a.graph.adj, a.covers["greedy"]) and A.is_cover(a.graph.adj, a.covers["lp"]), (gt, n, d)
                    assert a.k >= 0 and set(a.decisions) == set(C.RULES)


def test_decisions_agree_on_the_answer_when_none_aborted_and_with_tau():
    for seed in range(8):
        a = ev.analyse(ev.Settings(graph_type="hubs", n=30, density=40, seed=seed, delta=-1), node_budget=100_000)
        answers = {d.answer for d in a.decisions.values() if not d.aborted}
        assert answers == {a.k >= a.tau}
