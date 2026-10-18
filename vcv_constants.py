"""Konstanten: Regler-Grenzen, Rechengrenzen, feste Annahmen, Farben und Presets."""

N_MIN, N_MAX, DEFAULT_N = 6, 60, 10
DENSITY_MIN, DENSITY_MAX, DEFAULT_DENSITY = 5, 95, 30   # Anteil der Paare im KONFLIKT in Prozent (Kante = „dürfen nicht zusammen“)
SEED_MAX, DEFAULT_SEED = 999999, 3
SWEEP_SEEDS = tuple(range(100000, 100005))              # feste Instanzen für alle Sweeps: nie ein einzelner Seed als Befund
N_CLASSES = 6                                           # Zahl der Sendungsklassen bei den Klassenregeln

GRAPH_TYPES = {"random": "Zufallsregeln", "windows": "Zeitfenster", "classes": "Klassenregeln", "hubs": "Wenige Verursacher"}
DEFAULT_TYPE = "random"

# Verfahren der Approximations-Ansicht
METHODS = {"matching": "Matching-Verfahren (Faktor 2)", "greedy": "Greedy nach Höchstgrad", "lp": "LP-Rundung (halbganzzahlig)", "exact": "exakt (kleinste Überdeckung)"}
DEFAULT_METHOD = "matching"

# Regeln der Entscheidungsfrage „gibt es eine Überdeckung der Größe <= k?“
RULES = {"edge": "Verzweigen auf einer Kante", "degree": "Verzweigen auf dem Knoten höchsten Grades", "degree_reduce": "Grad + Grad-1-Regel", "buss": "Buss-Kern, dann Grad + Grad-1-Regel"}
DEFAULT_RULE = "degree_reduce"
DELTA_MIN, DELTA_MAX, DEFAULT_DELTA = -3, 3, 0           # k = τ + Δ: Δ = 0 ist eine Ja-Instanz, Δ < 0 eine Nein-Instanz

# Rechengrenzen: ein Knoten ist ein Aufruf der Verzweigung. Wird das Budget überschritten, bricht der Lauf ab und meldet es.
NODE_BUDGET = 200_000        # Hauptansicht, je Regel
EXACT_BUDGET = 300_000       # exakte Lösung (alle Tiefen zusammen)
SWEEP_BUDGET = 5_000         # Sweeps und Vergleichstabellen, je Lauf (Kantenregel: EDGE_SWEEP_BUDGET)
HUB_EXACT_BUDGET = 20_000  # Budget der exakten Lösung in Experiment 4 (bei Abbruch dient die Greedy-Größe als Bezug)
EDGE_SWEEP_BUDGET = 2_000   # die Kantenregel (2^k) bekommt in Sweeps ein kleineres Budget
HUB_SWEEP = (2, 4, 8, 12, 16)                 # Zahl der Verursacher in Experiment 4
HUB_N = 100                  # Sendungen in Experiment 4
TRAP_SIZES = (4, 6, 8, 12, 16, 24)                       # Greedy-Falle: a linke Knoten
CHECK_N = 14                 # Knotenzahl der Komplement-Gegenprobe (Brute Force über alle Teilmengen)

# Farben
COLOR_COVER = "#c0504d"      # in der Überdeckung (ausgelagert)
COLOR_HALF = "#e0a030"       # LP-Wert ½
COLOR_FREE = "#9fb3c8"       # nicht in der Überdeckung
COLOR_EDGE = "rgba(150,150,150,0.35)"
COLOR_MATCH = "#2F6B65"      # Kante des Matchings
COLOR_LINE = {"edge": "#c0504d", "degree": "#e0a030", "degree_reduce": "#4c78a8", "buss": "#2F6B65"}

PRESETS = {
    "Lehrbeispiel (klein)": {"type": "random", "n": 10, "density": 30, "seed": 3, "method": "matching", "rule": "degree_reduce", "delta": 0},
    "Dicht: der Kern bleibt groß": {"type": "random", "n": 40, "density": 50, "seed": 35, "method": "lp", "rule": "degree", "delta": 0},
    "Wenige Verursacher: der Kern schrumpft": {"type": "hubs", "n": 60, "density": 40, "seed": 35, "method": "greedy", "rule": "buss", "delta": -1},
    "Dünn: die Regeln lösen fast alles": {"type": "random", "n": 60, "density": 5, "seed": 35, "method": "lp", "rule": "degree_reduce", "delta": 0},
    "Zeitfenster": {"type": "windows", "n": 40, "density": 20, "seed": 35, "method": "matching", "rule": "degree", "delta": -1},
}
PRESET_HELP = {
    "Lehrbeispiel (klein)": "10 Sendungen, knapp jedes dritte Paar im Konflikt: wenige Schritte, gut zum Nachvollziehen.",
    "Dicht: der Kern bleibt groß": "40 Sendungen, jedes zweite Paar im Konflikt: Die LP-Lösung ist überall ½, der Kern ist der ganze Graph.",
    "Wenige Verursacher: der Kern schrumpft": "Wenige Sendungen verursachen fast alle Konflikte. Mit k = τ − 1 (Nein-Instanz) und dem Buss-Kern bleibt von 60 Sendungen fast nichts übrig.",
    "Dünn: die Regeln lösen fast alles": "60 Sendungen, nur jedes zwanzigste Paar im Konflikt: Die Grad-1-Regel und der LP-Kern entscheiden den größten Teil des Graphen.",
    "Zeitfenster": "Konflikt heißt: die Zeitfenster überlappen (ein Intervallgraph). Mit k = τ − 1 muss die Verzweigung beweisen, dass es nicht geht.",
}
