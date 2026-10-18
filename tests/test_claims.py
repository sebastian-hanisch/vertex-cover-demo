"""Jede Zahl aus README und App wird hier nachgerechnet (DEMO-PLAYBOOK §4: erst messen, dann Text schreiben).
Alle Zählwerte (Knoten, Kanten, Sendungen) sind ganzzahlig und plattformunabhängig exakt; Faktoren mit enger Toleranz (Rundung)."""

import math

import pytest

import vcv_algorithm as A
import vcv_constants as C
import vcv_evaluation as ev
import vcv_scenario as S


def _preset(name):
    p = C.PRESETS[name]
    return ev.analyse(ev.Settings(graph_type=p["type"], n=p["n"], density=p["density"], seed=p["seed"], method=p["method"], delta=p["delta"], rule=p["rule"]))


def _decisions(a):
    return {r: (d.answer, d.nodes, d.aborted) for r, d in a.decisions.items()}


# --- Standardfall = Lehrbeispiel: 10 Sendungen, 30 %, Zufallsregeln, Seed 3 -----------------------------------------------------------------------

def test_default_case_numbers():
    a = ev.analyse(ev.Settings())
    assert a.tau == 4 and {m: len(c) for m, c in a.covers.items()} == {"matching": 6, "greedy": 4, "lp": 4, "exact": 4}
    assert (a.lp2, len(a.forced), len(a.excluded), len(a.kernel), len(a.matching)) == (8, 4, 6, 0, 3)
    assert a.k == 4 and _decisions(a) == {"edge": (True, 9, False), "degree": (True, 3, False), "degree_reduce": (True, 1, False), "buss": (True, 1, False)}
    assert (a.kernel_buss.k_rest, a.kernel_buss.edges, a.kernel_buss.vertices, a.kernel_buss.verdict) == (4, 11, 9, None)
    assert a.exact.cover == (0, 1, 5, 7) and a.exact.nodes == 0


# --- Presets ----------------------------------------------------------------------------------------------------------------------------------

def test_preset_dense_kernel_stays_large():
    a = _preset("Dicht: der Kern bleibt groß")
    assert a.tau == 33 and {m: len(c) for m, c in a.covers.items()} == {"matching": 40, "greedy": 34, "lp": 40, "exact": 33}
    assert (a.lp2, len(a.forced), len(a.excluded), len(a.kernel), len(a.matching)) == (40, 0, 0, 40, 20)
    assert a.k == 33 and _decisions(a) == {"edge": (None, C.NODE_BUDGET + 1, True), "degree": (True, 47, False), "degree_reduce": (True, 33, False), "buss": (True, 33, False)}
    assert (a.kernel_buss.k_rest, a.kernel_buss.edges, a.kernel_buss.vertices) == (33, 412, 40)


def test_preset_few_hubs_kernel_shrinks():
    a = _preset("Wenige Verursacher: der Kern schrumpft")
    assert a.tau == 6 and {m: len(c) for m, c in a.covers.items()} == {"matching": 12, "greedy": 6, "lp": 6, "exact": 6}
    assert (a.lp2, len(a.forced), len(a.excluded), len(a.kernel), len(a.matching)) == (12, 6, 54, 0, 6)
    assert a.k == 5 and _decisions(a) == {"edge": (False, 63, False), "degree": (False, 4, False), "degree_reduce": (False, 1, False), "buss": (False, 1, False)}
    assert (a.kernel_buss.k_rest, a.kernel_buss.edges, a.kernel_buss.vertices) == (2, 3, 6)


def test_preset_thin_graph_rules_solve_almost_everything():
    a = _preset("Dünn: die Regeln lösen fast alles")
    assert a.tau == 27 and {m: len(c) for m, c in a.covers.items()} == {"matching": 46, "greedy": 27, "lp": 27, "exact": 27}
    assert (a.lp2, len(a.forced), len(a.excluded), len(a.kernel), len(a.matching)) == (54, 27, 33, 0, 23)
    assert a.k == 27 and _decisions(a) == {"edge": (None, C.NODE_BUDGET + 1, True), "degree": (True, 17, False), "degree_reduce": (True, 1, False), "buss": (True, 1, False)}
    assert (a.kernel_buss.k_rest, a.kernel_buss.edges, a.kernel_buss.vertices) == (27, 87, 59)


def test_preset_windows_needs_thousands_of_nodes_to_prove_no():
    a = _preset("Zeitfenster")
    assert a.tau == 32 and {m: len(c) for m, c in a.covers.items()} == {"matching": 40, "greedy": 32, "lp": 40, "exact": 32}
    assert (len(a.forced), len(a.excluded), len(a.kernel)) == (0, 0, 40)
    assert a.k == 31 and _decisions(a) == {"edge": (None, C.NODE_BUDGET + 1, True), "degree": (False, 3929, False), "degree_reduce": (False, 2887, False), "buss": (False, 2887, False)}
    assert (a.kernel_buss.k_rest, a.kernel_buss.edges, a.kernel_buss.vertices) == (31, 139, 40)


# --- Experiment 1 und 3: Strukturen ----------------------------------------------------------------------------------------------------------

@pytest.fixture(scope="module")
def structures():
    return {r["name"]: r for r in ev.structure_rows()}


def test_structure_table_numbers(structures):
    expect = {  # n, τ, Matching (Median, größter), Greedy (Median, größter), LP-Rundung (Median, größter), LP-Wert/τ, x=1, x=0, Kern
        "Zufall, n = 40, 20 %": (40, 25, 1.44, 1.52, 1.04, 1.08, 1.60, 1.60, 0.80, 0, 0, 40),
        "Zufall, n = 40, 50 %": (40, 33, 1.212, 1.212, 1.03, 1.061, 1.212, 1.212, 0.606, 0, 0, 40),
        "Zufall, n = 60, 5 %": (60, 28, 1.667, 1.786, 1.033, 1.107, 1.346, 1.60, 0.981, 16, 25, 19),
        "Zeitfenster, n = 60, 20 %": (60, 52, 1.154, 1.176, 1.019, 1.02, 1.154, 1.176, 0.577, 0, 0, 60),
        "Klassenregeln, n = 60, 20 %": (60, 24, 1.75, 2.0, 1.0, 1.0, 1.042, 1.08, 0.917, 19, 35, 6),
        "Baum, n = 100": (100, 41, 1.641, 1.805, 1.026, 1.049, 1.0, 1.0, 1.0, 41, 59, 0),
        "Gitter 10 × 10": (100, 50, 2.0, 2.0, 1.0, 1.0, 1.0, 1.0, 1.0, 50, 50, 0),
        "skalenfrei, n = 200, m = 2": (200, 88, 1.543, 1.651, 1.034, 1.035, 1.0, 1.0, 1.0, 88, 112, 0),
        "skalenfrei, n = 200, m = 4": (200, 108, 1.463, 1.491, 1.019, 1.044, 1.852, 1.887, 0.926, 0, 0, 200),
        "Zufall, n = 100, 3 %": (100, 46, 1.609, 1.609, 1.02, 1.087, 1.5, 1.686, 0.978, 21, 31, 48),
        "Wenige Verursacher, n = 200": (200, 20, 1.889, 2.0, 1.0, 1.0, 1.0, 1.0, 1.0, 20, 180, 0),
    }
    assert set(structures) == set(expect)
    for name, (n, tau, m, mm, g, gm, lp, lpm, ratio, ones, zeros, half) in expect.items():
        r = structures[name]
        assert (r["n"], r["tau"], r["ones"], r["zeros"], r["half"], r["aborted"]) == (n, tau, ones, zeros, half, 0), name
        for key, val in (("match", m), ("match_max", mm), ("greedy", g), ("greedy_max", gm), ("lp", lp), ("lp_max", lpm), ("lp_ratio", ratio)):
            assert math.isclose(r[key], val, abs_tol=0.0015), (name, key, r[key])


def test_no_approximation_ever_exceeds_the_guarantee_and_the_matching_hits_two_on_grids_and_hubs(structures):
    assert all(r["match_max"] <= 2.0 + 1e-9 for r in structures.values())
    assert structures["Gitter 10 × 10"]["match"] == 2.0 and structures["Wenige Verursacher, n = 200"]["match_max"] == 2.0 and structures["Klassenregeln, n = 60, 20 %"]["match_max"] == 2.0
    assert max(r["greedy_max"] for r in structures.values()) < 1.11
    assert max(r["lp_max"] for r in structures.values()) < 1.89 and structures["skalenfrei, n = 200, m = 4"]["lp_max"] > 1.88


def test_koenig_holds_on_the_two_bipartite_structures_and_their_kernel_is_empty(structures):
    bip = {n for n, r in structures.items() if r["bipartite"]}
    assert bip == {"Baum, n = 100", "Gitter 10 × 10"}
    assert all(structures[n]["koenig"] and structures[n]["half"] == 0 for n in bip)
    assert [n for n, r in structures.items() if r["half"] == r["n"]] == ["Zufall, n = 40, 20 %", "Zufall, n = 40, 50 %", "Zeitfenster, n = 60, 20 %", "skalenfrei, n = 200, m = 4"]


# --- Experiment 2: Greedy-Falle ----------------------------------------------------------------------------------------------------------------

def test_trap_rows():
    rows = {r["a"]: r for r in ev.trap_rows()}
    assert {a: (r["n"], r["tau"], r["greedy"], r["matching"]) for a, r in rows.items()} == {
        4: (8, 4, 4, 8), 6: (14, 6, 8, 12), 8: (20, 8, 12, 16), 12: (35, 12, 23, 24), 16: (50, 16, 34, 32), 24: (84, 24, 60, 48)}
    assert all(r["matching_factor"] == 2.0 for r in rows.values())
    assert math.isclose(rows[24]["greedy_factor"], 2.5) and math.isclose(rows[16]["greedy_factor"], 2.125) and math.isclose(rows[6]["greedy_factor"], 4 / 3)
    assert [a for a, r in rows.items() if r["greedy_factor"] > r["matching_factor"]] == [16, 24]


# --- Experiment 4: wenige Verursacher ----------------------------------------------------------------------------------------------------------

@pytest.fixture(scope="module")
def hubs():
    return {(r["hubs"], r["kind"]): r for r in ev.hub_rows()}


def test_hub_rows(hubs):
    expect = {  # (τ, Kanten, k', Kernkanten, Kernknoten, Knoten Kante, Grad, Grad+1, Buss)
        (2, "hubs"): (4, 78, 1, 2, 4, 15, 3, 1, 0), (2, "random"): (37, 78, 36, 78, 81, 2001, 2067, 1, 1),
        (4, "hubs"): (8, 156, 3, 4, 8, 255, 5, 1, 1), (4, "random"): (47, 156, 46, 156, 96, 2001, 5001, 8, 8),
        (8, "hubs"): (15, 291, 6, 8, 15, 2001, 9, 1, 1), (8, "random"): (63, 291, 62, 291, 100, 2001, 5001, 24, 24),
        (12, "hubs"): (24, 417, 11, 12, 24, 2001, 13, 1, 1), (12, "random"): (70, 417, 69, 417, 100, 2001, 54, 37, 37),
        (16, "hubs"): (27, 541, 10, 16, 26, 2001, 19, 4, 1), (16, "random"): (75, 541, 74, 541, 100, 2001, 85, 50, 50),
    }
    assert set(hubs) == set(expect)
    for key, (tau, m, kr, ke, kv, n_edge, n_deg, n_dr, n_buss) in expect.items():
        r = hubs[key]
        assert (r["tau"], r["m"], r["k_rest"], r["kernel_edges"], r["kernel_vertices"]) == (tau, m, kr, ke, kv), key
        assert (r["nodes"]["edge"], r["nodes"]["degree"], r["nodes"]["degree_reduce"], r["nodes"]["buss"]) == (n_edge, n_deg, n_dr, n_buss), key


def test_random_comparison_graphs_keep_every_edge_in_the_buss_kernel_and_hub_graphs_almost_none(hubs):
    assert all(hubs[(h, "random")]["kernel_edges"] == hubs[(h, "random")]["m"] for h in C.HUB_SWEEP)
    assert all(hubs[(h, "hubs")]["kernel_edges"] <= h for h in C.HUB_SWEEP)
    assert hubs[(16, "hubs")]["m"] == hubs[(16, "random")]["m"] == 541
    assert [h for h in C.HUB_SWEEP if hubs[(h, "random")]["exact_aborted"]] == [8, 12, 16]          # dort steht für τ die Greedy-Größe


# --- Brücke ----------------------------------------------------------------------------------------------------------------------------------

def test_complement_bridge_on_the_default_small_instance():
    cc = ev.complement_check(ev.Settings())
    assert (cc["n"], cc["tau"], cc["alpha"]) == (14, 7, 7) and cc["equal"]


def test_limits_as_documented():
    assert (C.NODE_BUDGET, C.EXACT_BUDGET, C.SWEEP_BUDGET, C.EDGE_SWEEP_BUDGET, C.HUB_EXACT_BUDGET, C.HUB_N) == (200_000, 300_000, 5_000, 2_000, 20_000, 100)
    assert (C.N_MIN, C.N_MAX, C.DENSITY_MIN, C.DENSITY_MAX, C.DELTA_MIN, C.DELTA_MAX) == (6, 60, 5, 95, -3, 3)
    assert C.HUB_SWEEP == (2, 4, 8, 12, 16) and C.TRAP_SIZES == (4, 6, 8, 12, 16, 24)
    g = S.random_graph(60, 50, 35)
    assert A.decide(g.adj, 40, "edge", budget=C.NODE_BUDGET).aborted
