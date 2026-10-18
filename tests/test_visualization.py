"""Figuren: jede lässt sich bauen, die Zustandsfarben stimmen, alle Achsen sind fest."""

import vcv_algorithm as A
import vcv_constants as C
import vcv_evaluation as ev
import vcv_scenario as S
import vcv_visualization as V


def _node_trace(fig):
    return next(t for t in fig.data if t.mode == "markers+text")


def _all_axes_fixed(fig):
    return fig.layout.xaxis.fixedrange and fig.layout.yaxis.fixedrange


def test_graph_figure_builds_for_every_method_and_colours_the_cover(p4):
    g = S.Graph(4, p4, S.circle_positions(list(range(4))), tuple(str(i) for i in range(4)), "random")
    fig = V.build_graph_figure(g, cover=(1, 2))
    assert list(_node_trace(fig).marker.color) == [C.COLOR_FREE, C.COLOR_COVER, C.COLOR_COVER, C.COLOR_FREE] and _all_axes_fixed(fig)
    cover, matching = A.matching_cover(p4)
    fig = V.build_graph_figure(g, cover=cover, matching=matching)
    assert any(t.mode == "lines" and t.line.color == C.COLOR_MATCH for t in fig.data)
    for method in C.METHODS:
        a = ev.analyse(ev.Settings(n=12, method=method))
        fig = V.build_graph_figure(a.graph, cover=a.covers[method], matching=a.matching if method == "matching" else (), forced=a.forced, kernel=a.kernel, show_lp=method == "lp")
        assert len(_node_trace(fig).x) == a.graph.n and _all_axes_fixed(fig)


def test_lp_tint_distinguishes_forced_kernel_and_free(c5, tri_pendant):
    g = S.Graph(5, c5, S.circle_positions(list(range(5))), tuple(str(i) for i in range(5)), "random")
    forced, excluded, kernel = A.lp_kernel(c5)
    fig = V.build_graph_figure(g, forced=forced, kernel=kernel, show_lp=True)
    assert list(_node_trace(fig).marker.color) == [C.COLOR_HALF] * 5
    forced, excluded, kernel = A.lp_kernel(tri_pendant)
    g2 = S.Graph(4, tri_pendant, S.circle_positions(list(range(4))), tuple(str(i) for i in range(4)), "random")
    colors = list(_node_trace(V.build_graph_figure(g2, forced=forced, kernel=kernel, show_lp=True)).marker.color)
    assert colors.count(C.COLOR_COVER) == 2 and colors.count(C.COLOR_FREE) == 2


def test_experiment_figures_build_and_lock_their_axes():
    rows = ev.structure_rows(seeds=(1,))
    hubs = ev.hub_rows(hubs=(2, 4), n=40, seeds=(1,), budget=500)
    a = ev.analyse(ev.Settings(n=20))
    figs = [V.build_structure_figure(rows), V.build_lp_figure(rows), V.build_trap_figure(ev.trap_rows(sizes=(4, 6))), V.build_decision_figure(a.decisions, C.NODE_BUDGET),
            V.build_hub_nodes_figure(hubs, "hubs"), V.build_hub_nodes_figure(hubs, "random"), V.build_hub_kernel_figure(hubs)]
    assert all(_all_axes_fixed(f) for f in figs)


def test_hub_nodes_figure_marks_aborted_medians():
    rows = ev.hub_rows(hubs=(8,), n=60, seeds=(1, 2), budget=50)
    fig = V.build_hub_nodes_figure(rows, "random")
    assert any(t.marker is not None and t.marker.symbol == "square-open" for t in fig.data)
