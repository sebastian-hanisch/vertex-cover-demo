"""Presets: Vollständigkeit, gültige Werte, erstes Preset = Standardeinstellungen; Permalink-Begrenzung."""

import pytest
from streamlit.testing.v1 import AppTest

import vcv_constants as C
import vcv_evaluation as ev
import vcv_presets as P


def test_every_preset_has_help_and_all_keys():
    assert set(C.PRESETS) == set(C.PRESET_HELP)
    for name, preset in C.PRESETS.items():
        assert set(preset) == set(P.PRESET_KEYS), name
        assert C.PRESET_HELP[name]


def test_preset_values_are_inside_the_slider_bounds_and_options():
    for name, p in C.PRESETS.items():
        assert C.N_MIN <= p["n"] <= C.N_MAX and C.DENSITY_MIN <= p["density"] <= C.DENSITY_MAX and 0 <= p["seed"] <= C.SEED_MAX, name
        assert C.DELTA_MIN <= p["delta"] <= C.DELTA_MAX, name
        assert p["type"] in C.GRAPH_TYPES and p["method"] in C.METHODS and p["rule"] in C.RULES, name


def test_first_preset_equals_the_default_settings():
    first = C.PRESETS[next(iter(C.PRESETS))]
    assert ev.Settings(graph_type=first["type"], n=first["n"], density=first["density"], seed=first["seed"], method=first["method"], delta=first["delta"], rule=first["rule"]) == ev.Settings()


def test_setting_specs_cover_every_preset_key_and_url_params_are_unique():
    assert set(P.PRESET_KEYS.values()) == set(P.SETTING_SPECS)
    params = [spec.url_param for spec in P.SETTING_SPECS.values()]
    assert len(params) == len(set(params))


def test_every_preset_runs_and_finishes():
    for name, p in C.PRESETS.items():
        s = ev.Settings(graph_type=p["type"], n=p["n"], density=p["density"], seed=p["seed"], method=p["method"], delta=p["delta"], rule=p["rule"])
        a = ev.analyse(s)
        assert a.tau is not None and not a.exact.aborted, name


def test_coerce_clamps_numbers_and_rejects_unknown_choices():
    n_spec = P.SETTING_SPECS["n_slider"]
    assert P._coerce(n_spec, "9999") == C.N_MAX and P._coerce(n_spec, "-5") == C.N_MIN and P._coerce(n_spec, "abc") is None
    assert P._coerce(P.SETTING_SPECS["type_select"], "hubs") == "hubs" and P._coerce(P.SETTING_SPECS["type_select"], "zzz") is None
    assert P._coerce(n_spec, ["12"]) == 12
    assert P._coerce(P.SETTING_SPECS["delta_slider"], "-99") == C.DELTA_MIN


def _probe():
    import streamlit as st

    import vcv_presets as P
    P.load_permalink_settings()
    P.init_session_state_defaults()
    st.session_state["seen"] = {k: st.session_state[k] for k in P.SETTING_SPECS}


def test_permalink_is_clamped_to_the_bounds_and_invalid_values_fall_back():
    at = AppTest.from_function(_probe)
    at.query_params["n"] = "9999"
    at.query_params["d"] = "-3"
    at.query_params["gt"] = "hubs"
    at.query_params["m"] = "nonsense"
    at.query_params["dk"] = "2"
    at.run()
    assert not at.exception
    seen = at.session_state["seen"]
    assert seen["n_slider"] == C.N_MAX and seen["density_slider"] == C.DENSITY_MIN and seen["delta_slider"] == 2
    assert seen["type_select"] == "hubs" and seen["method_radio"] == C.DEFAULT_METHOD


@pytest.mark.parametrize("name", list(C.PRESETS))
def test_apply_preset_writes_every_state_key(name):
    def _apply(preset_name):
        import streamlit as st

        import vcv_presets as P
        P.init_session_state_defaults()
        P.apply_preset(preset_name)
        st.session_state["seen"] = {k: st.session_state[k] for k in P.SETTING_SPECS}

    at = AppTest.from_function(_apply, args=(name,))
    at.run()
    assert not at.exception
    p = C.PRESETS[name]
    seen = at.session_state["seen"]
    assert (seen["n_slider"], seen["type_select"], seen["density_slider"], seen["method_radio"], seen["rule_radio"], seen["delta_slider"]) == \
        (p["n"], p["type"], p["density"], p["method"], p["rule"], p["delta"])
