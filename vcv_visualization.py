"""Plotly-Figuren: Konfliktgraph mit Überdeckung, Faktoren je Struktur, Greedy-Falle, LP-Zerlegung, Verzweigungsknoten. Alle Achsen fest (fixedrange)."""

import plotly.graph_objects as go

import vcv_constants as C

_FONT = dict(size=13)


def _fix(fig, height=420, **layout):
    layout.setdefault("margin", dict(l=40, r=20, t=30, b=40))
    fig.update_layout(height=height, font=_FONT, **layout)
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    return fig


def _edge_trace(pos, edges, color, width):
    xs, ys = [], []
    for u, v in edges:
        xs += [pos[u][0], pos[v][0], None]
        ys += [pos[u][1], pos[v][1], None]
    return go.Scatter(x=xs, y=ys, mode="lines", line=dict(color=color, width=width), hoverinfo="skip", showlegend=False)


def build_graph_figure(graph, cover=(), matching=(), forced=(), kernel=(), show_lp=False):
    """Der Konfliktgraph auf dem Kreis. `cover`: ausgelagerte Sendungen (rot). Mit `show_lp`: Tönung nach LP-Kern (forced rot, Kern orange, übrige blau).
    `matching`: Kanten des Matchings (grün, dick)."""
    pos = graph.positions
    fig = go.Figure()
    fig.add_trace(_edge_trace(pos, graph.edges(), C.COLOR_EDGE, 1))
    if matching:
        fig.add_trace(_edge_trace(pos, list(matching), C.COLOR_MATCH, 4))
    cover_set, forced_set, kernel_set = set(cover), set(forced), set(kernel)
    colors = []
    for v in range(graph.n):
        if show_lp:
            colors.append(C.COLOR_COVER if v in forced_set else C.COLOR_HALF if v in kernel_set else C.COLOR_FREE)
        else:
            colors.append(C.COLOR_COVER if v in cover_set else C.COLOR_FREE)
    fig.add_trace(go.Scatter(
        x=[p[0] for p in pos], y=[p[1] for p in pos], mode="markers+text", text=[str(i + 1) for i in range(graph.n)], textposition="middle center",
        textfont=dict(color="white", size=10), marker=dict(color=colors, size=22, line=dict(color="white", width=1)), hovertext=list(graph.labels), hoverinfo="text", showlegend=False))
    legend = ((("x = 1 (Überdeckung)", C.COLOR_COVER), ("Kern (x = ½)", C.COLOR_HALF), ("x = 0", C.COLOR_FREE)) if show_lp
              else (("ausgelagert (in der Überdeckung)", C.COLOR_COVER), ("bleibt", C.COLOR_FREE)))
    for name, color in legend:
        fig.add_trace(go.Scatter(x=[None], y=[None], mode="markers", marker=dict(color=color, size=12), name=name))
    if matching:
        fig.add_trace(go.Scatter(x=[None], y=[None], mode="lines", line=dict(color=C.COLOR_MATCH, width=4), name="Kante des Matchings"))
    fig.add_trace(go.Scatter(x=[-1.25, 1.25], y=[-1.25, 1.25], mode="markers", marker=dict(opacity=0), hoverinfo="skip", showlegend=False))
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False, scaleanchor="x", scaleratio=1)
    return _fix(fig, 520, legend=dict(orientation="h", y=-0.02, x=0.5, xanchor="center"), margin=dict(l=10, r=10, t=10, b=40))


def build_structure_figure(rows):
    """Je Struktur der Faktor (Größe / τ) der drei Näherungen als Punkte; senkrechte Linien bei 1 (optimal) und 2 (Garantie des Matching-Verfahrens)."""
    names = [f"{r['name']} (τ = {r['tau']:.0f})" for r in rows]
    fig = go.Figure()
    for key, label, color, symbol in (("match", "Matching-Verfahren", "#4c78a8", "circle"), ("greedy", "Greedy Höchstgrad", "#2F6B65", "diamond"), ("lp", "LP-Rundung", "#e0a030", "square")):
        fig.add_trace(go.Scatter(x=[r[key] for r in rows], y=names, mode="markers", name=label, marker=dict(color=color, size=11, symbol=symbol),
                                 hovertemplate="Faktor %{x:.2f}<extra>" + label + "</extra>"))
    fig.add_vline(x=1.0, line_dash="dot", line_color="#888888")
    fig.add_vline(x=2.0, line_dash="dash", line_color="#c0504d", annotation_text="Faktor 2", annotation_position="top")
    fig.update_xaxes(title="Größe / kleinste Überdeckung (Median)", range=[0.9, 2.1])
    fig.update_yaxes(autorange="reversed")
    return _fix(fig, 470, legend=dict(orientation="h", y=1.12, x=0.5, xanchor="center"), margin=dict(l=250, r=20, t=40, b=50))


def build_trap_figure(rows):
    """Greedy nach Höchstgrad gegen das Matching-Verfahren auf der Greedy-Falle: der Faktor über der Größe a."""
    fig = go.Figure()
    xs = [r["a"] for r in rows]
    fig.add_trace(go.Scatter(x=xs, y=[r["greedy_factor"] for r in rows], mode="lines+markers", name="Greedy Höchstgrad", line=dict(color="#2F6B65", width=3), marker=dict(size=9),
                             hovertemplate="a = %{x}: Faktor %{y:.2f}<extra>Greedy</extra>"))
    fig.add_trace(go.Scatter(x=xs, y=[r["matching_factor"] for r in rows], mode="lines+markers", name="Matching-Verfahren", line=dict(color="#4c78a8", width=3, dash="dash"), marker=dict(size=9),
                             hovertemplate="a = %{x}: Faktor %{y:.2f}<extra>Matching</extra>"))
    fig.update_xaxes(title="a (kleinste Überdeckung = a)", dtick=4)
    fig.update_yaxes(title="Faktor gegen die kleinste Überdeckung", rangemode="tozero")
    return _fix(fig, 360, legend=dict(orientation="h", y=1.15, x=0.5, xanchor="center"))


def build_lp_figure(rows):
    """Je Struktur der Anteil der Sendungen bei x = 1, x = 0 und im Kern (x = ½) der LP-Zerlegung in Prozent."""
    names = [f"{r['name']}" + (" (bipartit)" if r["bipartite"] else "") for r in rows]
    fig = go.Figure()
    for key, label, color in (("ones", "x = 1 (hinein)", C.COLOR_COVER), ("zeros", "x = 0 (heraus)", C.COLOR_FREE), ("half", "Kern (x = ½)", C.COLOR_HALF)):
        fig.add_trace(go.Bar(y=names, x=[100.0 * r[key] / r["n"] for r in rows], orientation="h", name=label, marker_color=color, hovertemplate="%{x:.0f} %%<extra>" + label + "</extra>"))
    fig.update_xaxes(title="Anteil der Sendungen (%)", range=[0, 100])
    fig.update_yaxes(autorange="reversed")
    return _fix(fig, 470, barmode="stack", legend=dict(orientation="h", y=1.1, x=0.5, xanchor="center"), margin=dict(l=250, r=20, t=40, b=50))


def build_decision_figure(decisions, budget):
    """Knoten der vier Verzweigungsregeln für das eingestellte k (logarithmisch); abgebrochene Läufe als Untergrenze mit offenem Quadrat."""
    rules = list(C.RULES)
    fig = go.Figure()
    for r in rules:
        d = decisions[r]
        fig.add_trace(go.Bar(y=[C.RULES[r]], x=[max(d.nodes, 1)], orientation="h", marker_color=C.COLOR_LINE[r], showlegend=False,
                             hovertemplate=("mindestens " if d.aborted else "") + "%{x:,.0f} Knoten<extra>" + C.RULES[r] + "</extra>"))
    fig.update_xaxes(title=f"Knoten des Suchbaums (logarithmisch, Budget {budget:,.0f})".replace(",", "."), type="log")
    fig.update_yaxes(autorange="reversed")
    return _fix(fig, 260, margin=dict(l=250, r=20, t=20, b=50))


def build_hub_nodes_figure(rows, kind):
    """Knoten der vier Regeln über der Zahl der Verursacher für k = τ − 1, getrennt für „wenige Verursacher“ und den Zufallsgraphen gleicher Kantenzahl (logarithmisch)."""
    sub = [r for r in rows if r["kind"] == kind]
    fig = go.Figure()
    for rule, label in C.RULES.items():
        fig.add_trace(go.Scatter(x=[r["hubs"] for r in sub], y=[max(r["nodes"][rule], 1) for r in sub], mode="lines+markers", name=label,
                                 line=dict(color=C.COLOR_LINE[rule], width=3), marker=dict(size=8), hovertemplate="%{x} Verursacher: %{y:,.0f} Knoten<extra>" + label + "</extra>"))
        cut = [r for r in sub if r["aborted"][rule]]
        if cut:
            fig.add_trace(go.Scatter(x=[r["hubs"] for r in cut], y=[max(r["nodes"][rule], 1) for r in cut], mode="markers", showlegend=False,
                                     marker=dict(symbol="square-open", size=14, color=C.COLOR_LINE[rule], line=dict(width=2)),
                                     hovertemplate="mindestens ein Lauf abgebrochen: Untergrenze<extra></extra>"))
    fig.update_xaxes(title="Zahl der Verursacher", dtick=2)
    fig.update_yaxes(title="Knoten (Median, logarithmisch)", type="log")
    return _fix(fig, 380, legend=dict(orientation="h", y=1.25, x=0.5, xanchor="center"))


def build_hub_kernel_figure(rows):
    """Größe des Buss-Kerns (Kanten) über der Zahl der Verursacher für k = τ − 1: wenige Verursacher gegen Zufallsgraph gleicher Kantenzahl (die Zahl aller Kanten steht dabei)."""
    fig = go.Figure()
    for kind, label, color in (("hubs", "Wenige Verursacher", "#2F6B65"), ("random", "Zufall, gleiche Kantenzahl", "#c0504d")):
        sub = [r for r in rows if r["kind"] == kind]
        fig.add_trace(go.Scatter(x=[r["hubs"] for r in sub], y=[max(r["kernel_edges"], 1) for r in sub], mode="lines+markers", name=label, line=dict(color=color, width=3), marker=dict(size=8),
                                 hovertemplate="%{x} Verursacher: %{y:,.0f} Kanten im Kern<extra>" + label + "</extra>"))
    fig.update_xaxes(title="Zahl der Verursacher", dtick=2)
    fig.update_yaxes(title="Kanten im Buss-Kern (Median, logarithmisch)", type="log")
    return _fix(fig, 380, legend=dict(orientation="h", y=1.25, x=0.5, xanchor="center"))
