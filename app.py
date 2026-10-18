"""Knotenüberdeckung: Approximation, Kernbildung, Verzweigen - interaktive Konzept-Demo
Sebastian Hanisch - Operations Research und Machine Learning

Drittes Stück der Härte-und-Struktur-Reihe: Wie wenige Sendungen muss man auslagern, damit kein Konflikt bleibt? Näherung, LP-Kern, Kernbildung und Verzweigen am Konfliktgraphen einer Sammelladung.

Lauffähig mit: streamlit run app.py
"""

import pandas as pd
import streamlit as st

import vcv_algorithm as A
import vcv_constants as C
import vcv_evaluation as ev
from vcv_layout import dunkles_design, kopf_css
from vcv_presets import (
    bounds,
    init_session_state_defaults,
    load_permalink_settings,
    randomize_seed,
    sidebar_presets,
    sync_query_params,
)
from vcv_visualization import (
    build_decision_figure,
    build_graph_figure,
    build_hub_kernel_figure,
    build_hub_nodes_figure,
    build_lp_figure,
    build_structure_figure,
    build_trap_figure,
)

st.set_page_config(page_title="Knotenüberdeckung – Sebastian Hanisch", layout="wide")


def _i(x):
    """Ganze Zahl mit Punkt als Tausendertrenner."""
    return f"{x:,.0f}".replace(",", ".")


def _f(x, digits=1):
    """Dezimalzahl mit Komma."""
    return f"{x:.{digits}f}".replace(".", ",")


@st.cache_data(show_spinner=False)
def _analysis(settings):
    return ev.analyse(settings)


@st.cache_data(show_spinner=False)
def _structures():
    return ev.structure_rows()


@st.cache_data(show_spinner=False)
def _traps():
    return ev.trap_rows()


@st.cache_data(show_spinner=False)
def _hubs():
    return ev.hub_rows()


@st.cache_data(show_spinner=False)
def _complement(settings):
    return ev.complement_check(settings)


# Fester Kopf: nur der Titel bleibt beim Scrollen oben (Stylesheet in vcv_layout.py).
st.html(kopf_css(dunkles_design()))
with st.container(key="kopf"):
    st.title("🧩 Knotenüberdeckung: Approximation, Kernbildung, Verzweigen")
st.markdown(
    """
Wie wenige Sendungen muss man **auslagern**, damit kein **Konflikt** mehr übrig bleibt? Das ist eine **Knotenüberdeckung** im Konfliktgraphen (Sendung = Knoten, **Kante = „dürfen nicht zusammen verladen werden“**, also umgekehrt zu den Demos zur Cliquensuche). Die Sendungen, die bleiben, sind eine größte konfliktfreie Fuhre: Die kleinste Überdeckung τ und die größte unabhängige Menge α ergeben zusammen n.

Das ist das dritte Stück der **Härte-und-Struktur-Reihe**: Das Problem ist schwer, aber **wenige Verursacher** und **Baumstruktur** machen es leicht. Anders als die Fall-Demos zeigt diese Demo ein Verfahren an einem wachsenden Beispiel. Weiter unten: die vier Experimente **🔬**, **🚧 Wo die Annahmen enden** und der Expander **📐 Mathematische Formulierung**.
"""
)

with st.expander("So funktioniert die Knotenüberdeckung", expanded=True):
    st.markdown(
        """
Drei Wege, eine Überdeckung zu finden oder zu beweisen:

1. **Näherung:** schnell, aber nicht optimal. Das **Matching-Verfahren** nimmt beide Enden einer Kante nach der anderen, solange kein Ende schon gewählt ist: höchstens doppelt so viele Sendungen wie nötig. Die **Greedy-Regel** lagert immer die Sendung mit den meisten offenen Konflikten aus. Die **LP-Rundung** löst die Relaxation (jeder Konflikt: x_u + x_v ≥ 1) und rundet auf.
2. **Kern:** Was sich vorab entscheiden lässt, wird entschieden: Der **LP-Kern** (Nemhauser und Trotter) legt Sendungen mit x = 1 fest und streicht die mit x = 0, die **Grad-1-Regel** nimmt bei einer Sendung mit nur einem Konflikt dessen Partner, und **Buss** erzwingt Sendungen mit mehr als k Konflikten.
3. **Verzweigen:** „Gibt es eine Überdeckung der Größe ≤ k?“ Entweder auf einer Kante (u oder v hinein) oder auf der Sendung mit den meisten Konflikten (sie hinein oder alle ihre Partner hinein).

| Begriff | Bedeutung |
|---|---|
| **τ** | kleinste Zahl auszulagernder Sendungen |
| **k = τ + Δ** | der Parameter der Entscheidungsfrage: Δ = 0 ist eine Ja-Instanz, Δ < 0 eine Nein-Instanz |
| **Kern** | der Rest, der nach den Regeln noch offen ist |
        """
    )

st.caption("🔗 Die Adresszeile oben spiegelt Ihre aktuelle Konfiguration wider – einfach kopieren, um ein Szenario zu teilen.")

load_permalink_settings()
init_session_state_defaults()

with st.sidebar:
    sidebar_presets()  # Schnellstart oben, das aktive Preset ist hervorgehoben
    st.header("⚙️ Einstellungen")
    st.markdown("**Konfliktgraph**")
    graph_type = st.selectbox("Regelart", list(C.GRAPH_TYPES), format_func=C.GRAPH_TYPES.get, key="type_select",
                              help="Zufallsregeln: jedes Paar unabhängig im Konflikt. Zeitfenster: Konflikt, wenn die Fenster überlappen. Klassenregeln: sechs Klassen, ein Klassenpaar steht im Konflikt oder nicht. Wenige Verursacher: etwa jede zwanzigste Sendung steht mit vielen anderen im Konflikt.")
    n = st.slider("Sendungen n", *bounds("n_slider"), key="n_slider", help="Knotenzahl des Graphen.")
    density = st.slider("Konfliktanteil (%)", *bounds("density_slider"), key="density_slider",
                        help="Zufallsregeln: Wahrscheinlichkeit je Paar. Zeitfenster: die Fensterlänge wird so gewählt, dass zwei Fenster mit dieser Wahrscheinlichkeit überlappen. Klassenregeln: Wahrscheinlichkeit je Klassenpaar. Wenige Verursacher: Anteil der übrigen Sendungen, mit denen jeder Verursacher im Konflikt steht.")
    seed = st.number_input("Zufalls-Seed des Graphen", *bounds("seed_input"), key="seed_input", step=1)
    st.button("🎲 Neuen Graphen erzeugen", width="stretch", on_click=randomize_seed)
    st.markdown("**Näherung**")
    method = st.radio("Verfahren in der Graph-Ansicht", list(C.METHODS), format_func=C.METHODS.get, key="method_radio",
                      help="Welche Überdeckung der Graph zeigt. Die Kennzahlen vergleichen immer alle Verfahren.")
    st.markdown("**Entscheidungsfrage**")
    delta = st.slider("k = τ + Δ", *bounds("delta_slider"), key="delta_slider", help="Δ = 0: eine Überdeckung dieser Größe existiert (Ja). Δ < 0: sie existiert nicht (Nein, die Verzweigung muss es beweisen). Δ > 0: viel Spielraum.")
    rule = st.radio("Regel in der Verzweigungs-Ansicht", list(C.RULES), format_func=C.RULES.get, key="rule_radio",
                    help="Welche Regel die Ansicht hervorhebt. Das Diagramm vergleicht immer alle vier.")

sync_query_params({"type_select": graph_type, "n_slider": int(n), "density_slider": int(density), "seed_input": int(seed), "method_radio": method,
                   "delta_slider": int(delta), "rule_radio": rule})

settings = ev.Settings(graph_type=graph_type, n=int(n), density=int(density), seed=int(seed), method=method, delta=int(delta), rule=rule)
with st.spinner("Rechne..."):
    a = _analysis(settings)
g = a.graph
tau = a.tau
exact_txt = _i(tau) if tau is not None else "unbekannt"
cover_sizes = {m: len(c) for m, c in a.covers.items()}
m_size = len(a.matching)

tab_approx, tab_branch = st.tabs(["🎯 Näherung", "🌳 Verzweigen und Kerne"])

# --- Tab 1: Näherung -------------------------------------------------------------------------------------------------------------------------

with tab_approx:
    st.markdown("## 🎯 Wie wenige Sendungen auslagern?")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Kleinste Überdeckung τ", exact_txt, help="Mit dem LP-Kern und iterativer Vertiefung berechnet (exakt, soweit das Budget reicht).")
    chosen_size = cover_sizes[method]
    m2.metric(C.METHODS[method], _i(chosen_size), delta=(f"Faktor {_f(chosen_size / tau, 2)} gegen τ" if tau else "τ unbekannt"), delta_color="off",
              help="Größe der Überdeckung, die der Graph zeigt.")
    m3.metric("Untergrenze |M| ≤ τ ≤ 2|M|", f"|M| = {_i(m_size)}", delta=f"2|M| = {_i(2 * m_size)}", delta_color="off",
              help="Das Matching-Verfahren liefert nebenbei eine Untergrenze: Jede Überdeckung braucht je Kante des Matchings mindestens einen Endpunkt.")
    m4.metric("LP-Wert", _f(a.lp2 / 2, 1), delta=f"{_i(len(a.kernel))} Sendungen im Kern (x = ½)", delta_color="off",
              help="Der LP-Wert ist eine Untergrenze für τ; Sendungen im Kern haben den Wert ½.")
    if a.exact.aborted:
        st.warning(f"Die exakte Suche ist nach {_i(C.EXACT_BUDGET)} Knoten abgebrochen; τ ist unbekannt (untere Schranke {_i(a.exact.lower)}). Die Faktoren beziehen sich dann auf die beste bekannte Überdeckung.")
    show_lp = method == "lp"
    st.plotly_chart(build_graph_figure(g, cover=a.covers[method], matching=a.matching if method == "matching" else (), forced=a.forced, kernel=a.kernel, show_lp=show_lp),
                    width="stretch", key="graph_main")
    captions = {
        "matching": "Grüne Kanten: das maximale Matching. Jede seiner Kanten verlangt mindestens einen Endpunkt in jeder Überdeckung; das Verfahren nimmt beide.",
        "greedy": "Immer die Sendung mit den meisten noch offenen Konflikten wird ausgelagert (Gleichstand: kleinste Nummer).",
        "lp": "Rot: LP-Wert 1 (hinein). Orange: Kern, LP-Wert ½ (die Rundung nimmt alle). Blau: LP-Wert 0 (bleibt). Rot und Orange zusammen sind die gerundete Überdeckung.",
        "exact": "Eine kleinste Überdeckung (LP-Kern, dann iterative Vertiefung).",
    }
    st.caption(captions[method])

    st.markdown("## ❓ Kernfrage: Wie weit liegt die einfache Näherung vom Optimum, bei genau diesem Graphen?")
    if tau:
        fm, fg, fl = (cover_sizes[x] / tau for x in ("matching", "greedy", "lp"))
        text = (f"Matching-Verfahren: **{_i(cover_sizes['matching'])}** Sendungen (Faktor **{_f(fm, 2)}**, garantiert höchstens 2). Greedy Höchstgrad: {_i(cover_sizes['greedy'])} (Faktor {_f(fg, 2)}). "
                f"LP-Rundung: {_i(cover_sizes['lp'])} (Faktor {_f(fl, 2)}). Kleinste Überdeckung: **{_i(tau)}**.")
        if fm >= 1.8:
            st.warning(text + " Das Matching-Verfahren ist hier fast im schlechtesten Fall: ein perfektes Matching verlangt beide Enden jeder Kante, obwohl ein Ende genügt.")
        elif fm >= 1.3:
            st.info(text)
        else:
            st.success(text + " Hier ist die Näherung schon nah am Optimum.")
    else:
        st.info("Die kleinste Überdeckung ist in der Rechengrenze nicht gefunden worden; die Näherungen haben die Größen "
                f"{_i(cover_sizes['matching'])} (Matching), {_i(cover_sizes['greedy'])} (Greedy), {_i(cover_sizes['lp'])} (LP-Rundung).")

# --- Tab 2: Verzweigen und Kerne ----------------------------------------------------------------------------------------------------------------

with tab_branch:
    st.markdown("## 🌳 Gibt es eine Überdeckung der Größe ≤ k?")
    ref = "τ" if a.k_reference == "tau" else "der Greedy-Größe (τ unbekannt)"
    st.caption(f"k = {ref} {'+' if settings.delta >= 0 else '−'} {abs(settings.delta)} = **{_i(a.k)}**: "
               + ("eine **Ja-Instanz** (es gibt eine Überdeckung dieser Größe)." if a.tau is not None and a.k >= a.tau else "eine **Nein-Instanz**: die Verzweigung muss beweisen, dass es keine gibt." if a.tau is not None else "Ob Ja oder Nein, ist hier nicht sicher."))
    decisions = a.decisions
    d_chosen = decisions[rule]
    b = a.kernel_buss
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Antwort", ("Ja" if d_chosen.answer else "Nein") if not d_chosen.aborted else "offen", help="Antwort der gewählten Regel; „offen“, wenn das Knotenbudget erreicht wurde.")
    m2.metric("Knoten der Regel", (">" if d_chosen.aborted else "") + _i(d_chosen.nodes), delta=C.RULES[rule], delta_color="off", help="Aufrufe der Verzweigung (ein Knoten des Suchbaums) mit der in der Seitenleiste gewählten Regel.")
    m3.metric("Buss-Kern (Kanten)", _i(b.edges), delta=f"k' = {_i(b.k_rest)}, {_i(b.vertices)} Sendungen", delta_color="off",
              help="Was nach Buss übrig bleibt: Sendungen mit mehr als k offenen Konflikten sind erzwungen; der Rest hat höchstens k'² Kanten, sonst ist die Antwort Nein.")
    m4.metric("LP-Kern (x = ½)", f"{_i(len(a.kernel))} von {_i(g.n)}", delta=f"{_i(len(a.forced))} hinein", delta_color="off",
              help="Zerlegung nach Nemhauser und Trotter mit Sondierung: unabhängig von k.")
    if b.verdict is False:
        st.success("Der Buss-Kern entscheidet schon: Es gibt mehr offene Konflikte, als k' Sendungen decken könnten (höchstens k'² Kanten): **Nein**, ganz ohne Verzweigung.")
    st.plotly_chart(build_decision_figure(decisions, C.NODE_BUDGET), width="stretch", key="decision_chart")
    rest_copy = [set(x) for x in A.buss_kernel(g.adj, a.k)[1]]
    grad1 = A.reduce_degree_one(rest_copy)
    steps = pd.DataFrame({
        "Regel": ["Buss: Sendungen mit mehr als k offenen Konflikten", "Grad-1-Regel auf dem Buss-Rest", "LP-Kern: x = 1 (hinein)", "LP-Kern: x = 0 (heraus)"],
        "Sendungen entschieden": [len(b.forced), len(grad1), len(a.forced), len(a.excluded)],
        "Hinweis": ["hinein", "Partner des Grad-1-Knotens hinein", "unabhängig von k", "unabhängig von k"],
    })
    with st.expander("Welche Regel entscheidet wie viele Sendungen?"):
        st.dataframe(steps, hide_index=True, width="stretch")
        st.caption("Die Regeln überschneiden sich: Eine Sendung kann von mehreren entschieden werden. Die Tabelle zählt je Regel für sich.")
    st.markdown("## ❓ Kernfrage: Wie viel spart die Gradregel gegenüber dem Verzweigen auf einer Kante, bei genau diesem k?")
    de, dg, dr, dbs = (decisions[r] for r in ("edge", "degree", "degree_reduce", "buss"))
    if de.aborted and not dg.aborted:
        st.success(f"Das Verzweigen auf einer Kante bricht nach {_i(C.NODE_BUDGET)} Knoten ab (2^k wächst zu schnell), die Gradregel braucht **{_i(dg.nodes)}**, mit Grad-1-Regel **{_i(dr.nodes)}** und mit Buss-Kern **{_i(dbs.nodes)}**.")
    elif de.aborted:
        st.warning(f"Auch die Gradregel erreicht hier das Budget von {_i(C.NODE_BUDGET)} Knoten; mit Grad-1-Regel: {'>' if dr.aborted else ''}{_i(dr.nodes)} Knoten.")
    else:
        st.info(f"Kante: {_i(de.nodes)} Knoten, Gradregel: {_i(dg.nodes)}, mit Grad-1-Regel: {_i(dr.nodes)}, mit Buss-Kern: {_i(dbs.nodes)}. Bei dieser Größe ist die Kantenregel noch nicht hoffnungslos.")

st.markdown("---")

# --- Experiment 1 --------------------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Experiment 1: Wie nah kommen die Näherungen an das Optimum?")
st.caption("Median über 3 feste Graphen je Struktur (Zufallsstrukturen); die kleinste Überdeckung ist exakt berechnet. Die Punkte zeigen Größe der Überdeckung / τ; rechts von der Linie bei 2 darf nichts liegen, die das Matching-Verfahren garantiert.")
with st.spinner("Rechne die Strukturen..."):
    rows1 = _structures()
st.plotly_chart(build_structure_figure(rows1), width="stretch", key="structure_chart")
at_two = [r["name"] for r in rows1 if r["match"] >= 1.995]
worst_lp = max(rows1, key=lambda r: r["lp_max"])
best_greedy = max(rows1, key=lambda r: r["greedy_max"])
st.info(
    f"Das Matching-Verfahren liegt zwischen Faktor {_f(min(r['match'] for r in rows1), 2)} und {_f(max(r['match'] for r in rows1), 2)}"
    + (f"; **genau 2,0** bei „{'“, „'.join(at_two)}“" if at_two else "")
    + f". Greedy nach Höchstgrad liegt in allen {len(rows1)} Strukturen höchstens beim Faktor {_f(best_greedy['greedy_max'], 2)} (also fast optimal, aber ohne Garantie, siehe Experiment 2). "
    f"Die LP-Rundung ist dort exakt, wo der LP ganzzahlig ist, und erreicht bei „{worst_lp['name']}“ den Faktor {_f(worst_lp['lp_max'], 2)}: Wenn überall ½ herauskommt, rundet sie jede Sendung auf."
)
with st.expander("Tabelle zu Experiment 1"):
    st.dataframe(pd.DataFrame({
        "Struktur": [r["name"] for r in rows1], "n": [r["n"] for r in rows1], "τ": [r["tau"] for r in rows1],
        "Matching (Median / größter)": [f"{_f(r['match'], 2)} / {_f(r['match_max'], 2)}" for r in rows1],
        "Greedy (Median / größter)": [f"{_f(r['greedy'], 2)} / {_f(r['greedy_max'], 2)}" for r in rows1],
        "LP-Rundung (Median / größter)": [f"{_f(r['lp'], 2)} / {_f(r['lp_max'], 2)}" for r in rows1],
        "LP-Wert / τ": [_f(r["lp_ratio"], 2) for r in rows1],
    }), hide_index=True, width="stretch")

st.markdown("---")

# --- Experiment 2 --------------------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Experiment 2: Die Greedy-Falle")
st.caption("Links a Sendungen, die zusammen die kleinste Überdeckung bilden (τ = a); rechts Gruppen von Sendungen, die jeweils mit j linken im Konflikt stehen, für j = 2 bis a. Die rechten Sendungen haben mehr Konflikte als die linken, also lagert Greedy sie zuerst aus.")
with st.spinner("Rechne die Falle..."):
    rows2 = _traps()
st.plotly_chart(build_trap_figure(rows2), width="stretch", key="trap_chart")
worse = next((r for r in rows2 if r["greedy_factor"] > r["matching_factor"]), None)
last2 = rows2[-1]
st.info(
    f"Der Faktor von Greedy beträgt bei a = {rows2[0]['a']} {_f(rows2[0]['greedy_factor'], 2)}, bei a = {last2['a']} schon **{_f(last2['greedy_factor'], 2)}** ({last2['greedy']} statt {last2['tau']}), und er wächst weiter. "
    f"Das Matching-Verfahren bleibt auf dieser Familie bei genau {_f(rows2[0]['matching_factor'], 2)}. "
    + (f"Ab a = {worse['a']} liegt Greedy über der Garantie des Matching-Verfahrens, obwohl es in allen Strukturen von Experiment 1 näher am Optimum war: eine Heuristik ohne Garantie." if worse else "")
)

st.markdown("---")

# --- Experiment 3 --------------------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Experiment 3: Wie viel entscheidet der LP-Kern?")
st.caption("Anteil der Sendungen mit LP-Wert 1 (hinein), 0 (heraus) und ½ (Kern, bleibt offen) je Struktur. Auf bipartiten Graphen ist der LP ganzzahlig und τ gleich der Größe eines größten Matchings (Satz von König).")
st.plotly_chart(build_lp_figure(rows1), width="stretch", key="lp_chart")
koenig = [r for r in rows1 if r["bipartite"]]
all_half = [r for r in rows1 if r["half"] == r["n"]]
small_kernel = [r for r in rows1 if r["half"] < r["n"] and r["half"] > 0]
st.info(
    (f"Auf den bipartiten Strukturen („{'“, „'.join(r['name'] for r in koenig)}“) bleibt kein Kern, und τ ist gleich der Matchinggröße ({'bestätigt' if all(r['koenig'] for r in koenig) else 'NICHT bestätigt'}): Nemhauser–Trotter löst sie vollständig. " if koenig else "")
    + (f"Dagegen ist der Kern bei „{'“, „'.join(r['name'] for r in all_half)}“ der ganze Graph: Dort gibt es keine Vorentscheidung durch den LP. " if all_half else "")
    + (f"Dazwischen liegen „{'“, „'.join(r['name'] for r in small_kernel)}“ mit einem Teilkern. " if small_kernel else "")
    + "Der Anteil hängt an der Struktur (bipartit, Verursacher, Dichte), nicht an der Kantenzahl."
)

st.markdown("---")

# --- Experiment 4 --------------------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Experiment 4: Wenige Verursacher gegen Zufall mit gleicher Kantenzahl")
st.caption(f"n = {C.HUB_N} Sendungen; die Verursacher stehen mit 40 % der übrigen im Konflikt, dazu so viele Zufallskonflikte wie Verursacher. Der Vergleichsgraph hat **genau gleich viele Kanten**, aber zufällig verteilt. Gemessen für die Nein-Instanz k = τ − 1 (Median über 3 Graphen; "
           f"die Kantenregel ist auf {_i(C.EDGE_SWEEP_BUDGET)}, die anderen auf {_i(C.SWEEP_BUDGET)} Knoten begrenzt, offene Quadrate = mindestens ein Lauf abgebrochen).")
with st.spinner("Rechne die Verursacher-Graphen..."):
    rows4 = _hubs()
c1, c2 = st.columns(2)
c1.markdown("**Wenige Verursacher**")
c1.plotly_chart(build_hub_nodes_figure(rows4, "hubs"), width="stretch", key="hub_nodes")
c2.markdown("**Zufall, gleiche Kantenzahl**")
c2.plotly_chart(build_hub_nodes_figure(rows4, "random"), width="stretch", key="random_nodes")
st.plotly_chart(build_hub_kernel_figure(rows4), width="stretch", key="hub_kernel")
last_h = [r for r in rows4 if r["kind"] == "hubs"][-1]
last_r = [r for r in rows4 if r["kind"] == "random"][-1]
st.info(
    f"Bei {last_h['hubs']} Verursachern ({_i(last_h['m'])} Kanten) bleiben nach Buss **{_i(last_h['kernel_edges'])} Kanten** übrig, und Grad + Grad-1-Regel brauchen {_i(last_h['nodes']['degree_reduce'])} Knoten (mit Buss-Kern {_i(last_h['nodes']['buss'])}). "
    f"Im Zufallsgraphen mit denselben {_i(last_r['m'])} Kanten bleiben **{_i(last_r['kernel_edges'])} Kanten** im Kern"
    + (": Buss streicht nichts, weil keine Sendung mehr als k Konflikte hat. " if last_r["kernel_edges"] == last_r["m"] else ". ")
    + 
    "Dieselbe Kantenzahl, ganz andere Schwierigkeit: Die Kernbildung nutzt, dass **k klein** ist, nicht dass der Graph dünn ist."
)
with st.expander("Tabelle zu Experiment 4"):
    st.dataframe(pd.DataFrame({
        "Verursacher": [r["hubs"] for r in rows4], "Graph": ["wenige Verursacher" if r["kind"] == "hubs" else "Zufall" for r in rows4], "τ": [r["tau"] for r in rows4],
        "Kanten": [r["m"] for r in rows4], "Buss: k'": [r["k_rest"] for r in rows4], "Buss: Kanten": [r["kernel_edges"] for r in rows4],
        "Knoten Kante": [_i(r["nodes"]["edge"]) + ("+" if r["aborted"]["edge"] else "") for r in rows4], "Knoten Grad": [_i(r["nodes"]["degree"]) + ("+" if r["aborted"]["degree"] else "") for r in rows4],
        "Knoten Grad+1": [_i(r["nodes"]["degree_reduce"]) + ("+" if r["aborted"]["degree_reduce"] else "") for r in rows4], "Knoten Buss": [_i(r["nodes"]["buss"]) + ("+" if r["aborted"]["buss"] else "") for r in rows4],
    }), hide_index=True, width="stretch")
    st.caption("„+“: mindestens ein Lauf hat das Budget erreicht, der Median ist dann nur eine Untergrenze. Wo die exakte Lösung in " + _i(C.HUB_EXACT_BUDGET) + " Knoten nicht fertig wurde, steht für τ die Greedy-Größe (k = Greedy − 1).")

st.markdown("---")

# --- Brücken -------------------------------------------------------------------------------------------------------------------------------

st.subheader("🔗 Brücken: τ = n − α und der Satz von König")
cc = _complement(settings)
st.caption(f"Ein kleiner Graph mit n = {cc['n']} Sendungen (Regelart, Anteil und Seed aus der Seitenleiste): kleinste Überdeckung gegen n minus die größte konfliktfreie Fuhre (Brute Force über alle Teilmengen, ohne Verzweigen).")
b1, b2, b3 = st.columns(3)
b1.metric("τ (Verzweigen)", cc["tau"])
b2.metric("α (Brute Force)", cc["alpha"])
b3.metric("n − α", cc["n"] - cc["alpha"])
if cc["equal"]:
    st.success(f"τ = n − α = **{cc['tau']}**: Die Sendungen außerhalb einer kleinsten Überdeckung sind eine größte konfliktfreie Fuhre. Das ist dieselbe Aufgabe wie die größte Clique im Verträglichkeitsgraphen (Demo zur größten Clique): τ = n − ω des Komplements.")
else:
    st.error("τ und n − α stimmen nicht überein: Das darf nicht passieren, bitte melden.")
if a.bipartite_nu is not None:
    st.info(f"Der aktuelle Graph ist bipartit: Das größte Matching hat {_i(a.bipartite_nu)} Kanten und τ ist {exact_txt} (Satz von König: auf bipartiten Graphen gleich). Das Matching-Verfahren der Matching-Demos (Erweiterungswege) liefert dieselbe Zahl.")
else:
    st.caption("Der aktuelle Graph ist nicht bipartit, der Satz von König gilt hier nicht; in Experiment 3 steht die Bestätigung für Baum und Gitter.")

st.markdown("---")

# --- Grenzen -------------------------------------------------------------------------------------------------------------------------------

st.subheader("🚧 Wo die Annahmen enden")
st.markdown(
    """
| Annahme | Was passiert, wenn sie verletzt ist | Wer setzt an |
|---|---|---|
| **Jede Sendung gleich viel wert** | Mit Kosten je Sendung (gewichtete Überdeckung) ändern sich Matching-Verfahren und Greedy; der LP bleibt halbganzzahlig. | – |
| **Zwei Sendungen je Konflikt** | Regeln für Dreiergruppen („A, B und C nie alle drei“) sind eine Mengenüberdeckung im Hypergraphen: der Faktor 2 und der Kern gelten dort nicht. | – |
| **Knoten statt Laufzeit** | Knoten des Suchbaums sind keine Laufzeit; jeder Knoten kostet je nach Regel verschieden viel. | – |
| **Kleine Graphen** | Hauptansicht bis n = 60, Strukturen bis n = 200. Reale Löser nutzen Branch-and-Reduce mit vielen weiteren Regeln und Lokalsuche und lösen Graphen mit Millionen Kanten. | Reduktionen und Lokalsuche für große Graphen |
| **Rekordalgorithmen** | Der schnellste bekannte Algorithmus in k ist deutlich besser als die Gradregel hier (nur als Einordnung im Mathematik-Expander). | – |
| **Synthetische Graphen** | Die Graphen sind erzeugt, keine echten Sendungsdaten. | – |
"""
)

st.markdown("---")

with st.expander("📐 Mathematische Formulierung"):
    st.markdown(
        r"""
**Problem.** Gegeben ein ungerichteter Graph $G = (V, E)$. Eine **Überdeckung** ist eine Menge $C \subseteq V$, die jede Kante berührt; $\tau(G)$ ist die kleinste Größe. Eine **unabhängige Menge** enthält keine Kante, $\alpha(G)$ ist die größte Größe. Das Komplement einer Überdeckung ist eine unabhängige Menge und umgekehrt:

$$\tau(G) + \alpha(G) = n$$

**Matching-Verfahren.** Ein maximales Matching $M$ (keine Kante lässt sich hinzufügen). Jede Überdeckung braucht je Matchingkante einen Endpunkt, die Endpunkte aller Matchingkanten überdecken alles:

$$|M| \le \tau(G) \le 2|M|$$

**LP-Relaxation.** Minimiere die Summe der $x_v$ unter

$$x_u + x_v \ge 1 \ \text{ für jede Kante } \{u, v\}, \qquad 0 \le x_v \le 1.$$

Jede Ecke des zulässigen Polyeders ist halbganzzahlig ($x_v \in \{0, \tfrac12, 1\}$). Der LP-Wert ist eine Untergrenze für $\tau$. Gelöst wird er hier über den bipartiten Doppelgraphen: jeder Knoten $v$ wird zu $v_L$ und $v_R$, jede Kante $\{u, v\}$ zu $\{u_L, v_R\}$ und $\{v_L, u_R\}$; mit einer kleinsten Überdeckung $(a, b)$ des Doppelgraphen ist $x_v = (a_v + b_v)/2$, und der LP-Wert ist die Hälfte der Größe eines größten Matchings im Doppelgraphen.

**Nemhauser–Trotter.** Für jede optimale halbganzzahlige Lösung $x$ mit $V_1 = \{x_v = 1\}$, $V_0 = \{x_v = 0\}$ und Kern $K = \{x_v = \tfrac12\}$ gibt es eine kleinste Überdeckung, die $V_1$ enthält und $V_0$ meidet:

$$\tau(G) = |V_1| + \tau(G[K])$$

Die Sondierung setzt jede Sendung einzeln auf 1 (bzw. auf 0 mit allen Nachbarn auf 1); bleibt der LP-Wert gleich, ist das wieder eine optimale halbganzzahlige Lösung und die Sendung persistent.

**Buss.** Hat ein Knoten mehr als $k$ Nachbarn, gehört er in jede Überdeckung der Größe $\le k$ (sonst müssten alle seine Nachbarn hinein). Nach dem Entfernen aller solchen Knoten mit Restparameter $k'$ deckt jeder der $k'$ Knoten höchstens $k'$ Kanten, also

$$|E'| \le k'^2$$

sonst ist die Antwort Nein. **Grad-1-Regel:** Hat $v$ genau einen Nachbarn $u$, gibt es eine kleinste Überdeckung mit $u$.

**Verzweigen.** Auf einer Kante $\{u, v\}$ (u oder v hinein): Suchbaum mit höchstens $2^k$ Blättern. Auf einem Knoten $v$ mit Grad $d \ge 3$ (v hinein, oder alle $d$ Nachbarn hinein):

$$T(k) \le T(k-1) + T(k-d), \qquad d \ge 3$$

Bei Maximalgrad $\le 2$ besteht der Rest aus Pfaden und Kreisen: ein Pfad mit $m$ Knoten braucht $\lfloor m/2 \rfloor$, ein Kreis $\lceil m/2 \rceil$ Sendungen. Der schnellste bekannte Algorithmus in $k$ braucht $O^*(1{,}25284^k)$ (Harris und Narayanaswamy 2024); unter der Exponentialzeit-Hypothese gibt es keinen $O^*(2^{o(k)})$-Algorithmus.

**Annahmen.**

| Annahme | Inhalt | Wer setzt an |
|---|---|---|
| Ungewichtet | jede Sendung kostet gleich viel | – |
| Paarkonflikte | Konflikte betreffen genau zwei Sendungen | – |
| Knoten statt Laufzeit | Aufwand als Zahl der Suchbaumknoten | – |

**Literatur.**
- Nemhauser, G. L., & Trotter, L. E. (1975). *Vertex packings: structural properties and algorithms.* Mathematical Programming 8, 232–248.
- Buss, J. F., & Goldsmith, J. (1993). *Nondeterminism within P.* SIAM Journal on Computing 22(3), 560–572.
- Harris, D. G., & Narayanaswamy, N. S. (2024). *A faster algorithm for vertex cover parameterized by solution size.* STACS 2024, arXiv:2205.08022.
        """
    )

st.markdown("---")
st.caption(
    "Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – "
    "Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). "
    "Mehr zu den Demos: [Interaktive Demos](https://sebastianhanisch.net/demos.html)."
)
