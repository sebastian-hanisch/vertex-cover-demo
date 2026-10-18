"""Auswertung: Einstellungen, Analyse der Hauptansicht, Vergleichstabellen und Sweeps (alle Zahlen kommen aus diesen Funktionen, nie von Hand)."""

import statistics
from dataclasses import dataclass

import vcv_algorithm as A
import vcv_constants as C
import vcv_scenario as S


@dataclass(frozen=True)
class Settings:
    """Alle Regler der Seitenleiste. Immer mit Schlüsselwörtern bauen (ein eingefügtes Feld verschob früher still Werte)."""
    graph_type: str = C.DEFAULT_TYPE
    n: int = C.DEFAULT_N
    density: int = C.DEFAULT_DENSITY
    seed: int = C.DEFAULT_SEED
    method: str = C.DEFAULT_METHOD
    delta: int = C.DEFAULT_DELTA
    rule: str = C.DEFAULT_RULE


@dataclass(frozen=True)
class Analysis:
    settings: Settings
    graph: S.Graph
    exact: A.ExactResult
    tau: object                 # kleinste Überdeckung oder None (Abbruch)
    covers: dict                # Methode -> Überdeckung (Tupel)
    matching: list
    forced: tuple               # LP-Kern: in die Überdeckung
    excluded: tuple             # LP-Kern: nicht in die Überdeckung
    kernel: tuple               # LP-Kern: offen (x = ½)
    lp2: int                    # 2 * LP-Wert
    k: int                      # Parameter der Entscheidungsfrage
    k_reference: str            # "tau" oder "greedy" (wenn die exakte Lösung abgebrochen ist)
    decisions: dict             # Regel -> Decision
    kernel_buss: object         # BussResult für k
    bipartite_nu: object        # Matchinggröße bei bipartitem Graphen, sonst None


def build_instance(settings):
    return S.build_graph(settings.graph_type, settings.n, settings.density, settings.seed)


def analyse(settings, node_budget=C.NODE_BUDGET, exact_budget=C.EXACT_BUDGET):
    g = build_instance(settings)
    exact = A.exact_cover(g.adj, exact_budget)
    cover_m, matching = A.matching_cover(g.adj)
    greedy = tuple(sorted(A.greedy_degree_cover(g.adj)))
    lp_cover, forced, excluded, kernel = A.lp_round_cover(g.adj)
    covers = {"matching": cover_m, "greedy": greedy, "lp": lp_cover, "exact": exact.cover}
    if exact.tau is not None:
        base, ref = exact.tau, "tau"
    else:
        base, ref = len(greedy), "greedy"
    k = max(0, base + settings.delta)
    decisions = {rule: A.decide(g.adj, k, rule, node_budget) for rule in C.RULES}
    buss, _ = A.buss_kernel(g.adj, k)
    return Analysis(settings, g, exact, exact.tau, covers, matching, tuple(forced), tuple(excluded), tuple(kernel), A.lp_value2(g.adj), k, ref, decisions, buss,
                    A.bipartite_matching_size(g.adj))


def factor(a, b):
    """Wie viel mal so viel a gegenüber b (b = 0: 1, wenn auch a = 0, sonst unendlich)."""
    if b == 0:
        return 1.0 if a == 0 else float("inf")
    return a / b


def med(xs):
    return statistics.median(xs)


# --- Experiment 1 und 3: feste Strukturen -----------------------------------------------------------------------------------------------------

STRUCTURES = (
    ("Zufall, n = 40, 20 %", lambda seed: S.random_graph(40, 20, seed)),
    ("Zufall, n = 40, 50 %", lambda seed: S.random_graph(40, 50, seed)),
    ("Zufall, n = 60, 5 %", lambda seed: S.random_graph(60, 5, seed)),
    ("Zeitfenster, n = 60, 20 %", lambda seed: S.window_graph(60, 20, seed)),
    ("Klassenregeln, n = 60, 20 %", lambda seed: S.class_graph(60, 20, seed)),
    ("Baum, n = 100", lambda seed: S.tree_graph(100, seed)),
    ("Gitter 10 × 10", lambda seed: S.grid_graph(10)),
    ("skalenfrei, n = 200, m = 2", lambda seed: S.scale_free_graph(200, 2, seed)),
    ("skalenfrei, n = 200, m = 4", lambda seed: S.scale_free_graph(200, 4, seed)),
    ("Zufall, n = 100, 3 %", lambda seed: S.random_graph(100, 3, seed)),
    ("Wenige Verursacher, n = 200", lambda seed: S.hub_family(200, 10, 40, seed)),
)


def structure_rows(seeds=C.SWEEP_SEEDS[:3], budget=C.EXACT_BUDGET):
    """Je Struktur der Median über die festen Instanzen: kleinste Überdeckung τ, Faktor (Größe / τ) von Matching-Verfahren, Greedy und LP-Rundung (Median und größter Wert),
    LP-Wert / τ, Knoten bei x = 1, x = 0 und im Kern (x = ½) und bei bipartiten Graphen die Matchinggröße (Satz von König)."""
    rows = []
    for name, build in STRUCTURES:
        data = {k: [] for k in ("tau", "match", "greedy", "lp", "lp_ratio", "ones", "zeros", "half", "nu", "bip", "aborted")}
        n = None
        for seed in seeds:
            g = build(seed)
            n = g.n
            ex = A.exact_cover(g.adj, budget)
            tau = ex.tau if ex.tau is not None else ex.lower
            data["aborted"].append(int(ex.aborted))
            data["tau"].append(tau)
            data["match"].append(factor(len(A.matching_cover(g.adj)[0]), tau))
            data["greedy"].append(factor(len(A.greedy_degree_cover(g.adj)), tau))
            lp_cover, forced, excluded, kernel = A.lp_round_cover(g.adj)
            data["lp"].append(factor(len(lp_cover), tau))
            data["lp_ratio"].append(factor(A.lp_value2(g.adj) / 2, tau))
            data["ones"].append(len(forced))
            data["zeros"].append(len(excluded))
            data["half"].append(len(kernel))
            nu = A.bipartite_matching_size(g.adj)
            data["bip"].append(nu is not None)
            data["nu"].append(nu if nu is not None else -1)
        rows.append({
            "name": name, "n": n, "tau": med(data["tau"]), "aborted": sum(data["aborted"]),
            "match": med(data["match"]), "match_max": max(data["match"]), "greedy": med(data["greedy"]), "greedy_max": max(data["greedy"]),
            "lp": med(data["lp"]), "lp_max": max(data["lp"]), "lp_ratio": med(data["lp_ratio"]),
            "ones": med(data["ones"]), "zeros": med(data["zeros"]), "half": med(data["half"]), "bipartite": all(data["bip"]),
            "koenig": all(data["bip"]) and all(v == t for v, t in zip(data["nu"], data["tau"])),
        })
    return rows


# --- Experiment 2: Greedy-Falle ---------------------------------------------------------------------------------------------------------------

def trap_rows(sizes=C.TRAP_SIZES):
    """Die Greedy-Falle (τ = a): Größe der Überdeckung und Faktor von Greedy nach Höchstgrad und Matching-Verfahren je a."""
    rows = []
    for a in sizes:
        g = S.trap_graph(a)
        tau = A.exact_cover(g.adj).tau
        greedy = len(A.greedy_degree_cover(g.adj))
        match = len(A.matching_cover(g.adj)[0])
        rows.append({"a": a, "n": g.n, "tau": tau, "greedy": greedy, "greedy_factor": factor(greedy, tau), "matching": match, "matching_factor": factor(match, tau)})
    return rows


# --- Experiment 4: wenige Verursacher gegen Zufall ----------------------------------------------------------------------------------------------

def hub_rows(hubs=C.HUB_SWEEP, n=C.HUB_N, p_pct=40, seeds=C.SWEEP_SEEDS[:3], budget=C.SWEEP_BUDGET):
    """Je Zahl der Verursacher: der Verursacher-Graph und ein Zufallsgraph mit genau gleich vielen Kanten (gleiche Knotenzahl). Für die Nein-Instanz k = τ − 1: Buss-Kern
    (Kanten, Knoten) und Knoten der vier Verzweigungsregeln (Median; `aborted` = Läufe, die das Budget erreichen)."""
    rows = []
    for h in hubs:
        for kind in ("hubs", "random"):
            data = {"tau": [], "m": [], "kernel_edges": [], "kernel_vertices": [], "k_rest": [], "exact_aborted": []}
            nodes = {r: [] for r in C.RULES}
            aborted = {r: 0 for r in C.RULES}
            for seed in seeds:
                g = S.hub_family(n, h, p_pct, seed)
                if kind == "random":
                    g = S.random_graph_m(n, g.m, seed)
                ex = A.exact_cover(g.adj, C.HUB_EXACT_BUDGET)
                tau = ex.tau if ex.tau is not None else len(A.greedy_degree_cover(g.adj))
                data["exact_aborted"].append(int(ex.aborted))
                k = max(tau - 1, 0)
                data["tau"].append(tau)
                data["m"].append(g.m)
                buss, _ = A.buss_kernel(g.adj, k)
                data["kernel_edges"].append(buss.edges)
                data["kernel_vertices"].append(buss.vertices)
                data["k_rest"].append(buss.k_rest)
                for rule in C.RULES:
                    d = A.decide(g.adj, k, rule, min(budget, C.EDGE_SWEEP_BUDGET) if rule == "edge" else budget)
                    nodes[rule].append(d.nodes)
                    aborted[rule] += int(d.aborted)
            rows.append({"hubs": h, "kind": kind, "tau": med(data["tau"]), "m": med(data["m"]), "kernel_edges": med(data["kernel_edges"]),
                         "kernel_vertices": med(data["kernel_vertices"]), "k_rest": med(data["k_rest"]),
                         "nodes": {r: med(v) for r, v in nodes.items()}, "aborted": aborted, "exact_aborted": sum(data["exact_aborted"])})
    return rows


# --- Brücken ------------------------------------------------------------------------------------------------------------------------------------

def complement_check(settings, n=C.CHECK_N):
    """Kleine Instanz (n = CHECK_N, Regelart, Anteil und Seed wie eingestellt): τ(G) = n − α(G), α per Aufzählen aller Teilmengen des Komplements (ohne Verzweigen)."""
    g = S.build_graph(settings.graph_type, n, settings.density, settings.seed)
    tau = A.exact_cover(g.adj).tau
    comp = S.complement(g.adj)
    best = 0
    nbr = [sum(1 << w for w in comp[v]) for v in range(g.n)]
    for mask in range(1, 1 << g.n):
        size = bin(mask).count("1")
        if size > best and all((mask & nbr[v]) == (mask & ~(1 << v)) for v in range(g.n) if mask >> v & 1):
            best = size
    return {"n": g.n, "tau": tau, "alpha": best, "equal": tau == g.n - best}
